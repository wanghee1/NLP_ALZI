"""RAG 답변 생성 (기능 1: 법적 근거 제시).

검색된 '실제 조문'만 근거로 consultation(상담식 답변) + legal_grounds(근거 법조문 배열)를 분리 반환한다.
할루시네이션 차단(rag-and-llm)이 이 모듈의 존재 이유다:
  - 조문표기·법령명·원문은 모두 코드가 metadata/documents 에서 소유하고,
  - LLM 은 consultation 산문과 plain(쉬운 해석)만 생성한다.
  - LLM 이 검색 결과에 없는 조문을 grounds 에 돌려보내면 코드가 드롭한다.
  - article 값도 LLM 반환값이 아닌 metadata 값으로 덮어써, 오타·변형이 노출되지 않는다.

순수 로직 계층(src/rag)이라 전송 계층(api/)에 의존하지 않는다 (architecture 규칙).
채팅 LLM 호출은 공용 클라이언트(src/llm/client)를 쓴다. 키는 거기서 config.settings 경유로
로딩하며 로그/예외에 노출하지 않는다 (security 규칙).
"""

from __future__ import annotations

import json
import logging
import re

from config.settings import (
    MIN_WAGE_HOURLY,
    MIN_WAGE_MONTHLY,
    MIN_WAGE_YEAR,
    RETRIEVAL_DISTANCE_THRESHOLD,
    RETRIEVAL_TOP_K,
)
from src.llm.client import complete
from src.rag.embeddings import embed_texts
from src.rag.query_transform import transform_query
from src.rag.vectorstore import get_collection

_TEMPERATURE = 0.2
_MAX_TOKENS = 3000

logger = logging.getLogger(__name__)

_NOT_FOUND_REPLY = (
    "관련 노동법 조문을 명확히 찾지 못했어요. "
    "질문을 좀 더 구체적으로 말씀해 주시겠어요?"
)

# consultation 말미에 프로그래밍 방식으로 append — LLM 생성과 분리해 항상 1회, 정확한 문구 보장
_CONSULTATION_NOTICE = (
    "본 답변은 AI가 생성한 참고용 정보로, 정확하지 않을 수 있으며 법적 효력이 없습니다. "
    "정확한 판단은 고용노동부(1350) 또는 전문가 상담을 권고드립니다."
)

_SYSTEM_PROMPT = f"""당신은 한국 노동법을 쉽게 설명하는 상담 도우미다.
아래에 사용자 질문과, 검색된 노동법 조문 후보 여러 개(조문표기·제목·원문)가 주어진다.
반드시 이 후보 조문들의 내용에만 근거해 답하라.

[최저임금 기준 — 반드시 준수]
현재({MIN_WAGE_YEAR}년) 최저임금: 시급 {MIN_WAGE_HOURLY:,}원, 월 환산(209시간 기준) {MIN_WAGE_MONTHLY:,}원.
최저임금 관련 질문에는 반드시 이 값을 기준으로 답하라.
다른 연도(2025년 등) 금액을 자체 지식으로 추측·생성하지 마라.
사용자가 시급을 언급하면 {MIN_WAGE_HOURLY:,}원과 비교해 미달 여부를 판단하라.

[출력 형식] 순수 JSON만 (다른 텍스트·코드펜스 금지):
{{"consultation": "...", "grounds": [{{"article": "<조문표기 그대로>", "plain": "..."}}], "suggest_document": false, "document_type": null}}

[consultation 작성 규칙]
1. 사용자 질문에 직접 답하는 대화체. 조항 나열 금지.
2. 사용자가 구체적 정보(날짜·기간·시급 등)를 줬으면 그 값을 직접 반영해 구체적으로 답할 것.
3. "~할 수 있어요", "~에 해당해요" 안내 톤. "무조건 ~입니다" 단정 금지.
4. 알바생·사회초년생도 알 수 있는 일상어.
5. 법적 판단은 아래 제공된 후보 조문 내용에만 근거할 것.
   제공되지 않은 다른 법률 내용을 자체 지식으로 보충하지 마라.
6. 후보 조문만으로 충분히 답할 수 없으면 아는 척하지 말고, consultation을 다음 문장으로만 채울 것:
   "이 부분은 제가 가진 법령 정보 범위에서는 정확히 답하기 어려워요. 고용노동부(1350)나 노무사 상담을 권해요."
7. consultation 끝에 면책 고지 문구를 추가하지 말 것. 시스템이 별도로 처리한다.

[grounds 작성 규칙]
1. article은 제공된 조문표기를 한 글자도 바꾸지 말고 그대로 쓸 것.
2. plain은 해당 조문 원문 내용만을 바탕으로 1~2문장 쉬운 해석. 조문 밖 내용 추가 금지.
3. 검색된 모든 후보 조문을 grounds에 포함할 것. 가장 관련 높은 것을 첫 번째로.

[suggest_document 판단 규칙]
- consultation에서 다루는 상황이 아래에 명확히 해당할 때만 suggest_document=true로 설정하라.
  · 임금·수당을 못 받았다, 체불, 최저임금 미달 → document_type: "wage_complaint"
  · 갑자기 해고됐다, 부당해고 의심, 해고 통보를 받았다 → document_type: "unfair_dismissal"
- 단순 법률 정보 질문·법적 개념 설명이면 suggest_document=false, document_type=null.
- 상황이 애매하거나 확실하지 않으면 반드시 suggest_document=false. 과잉 제안 금지."""


def _citation(metadata: dict) -> str:
    """출처 인용 문자열 ('근로기준법 제55조' 형태 — rag-and-llm 인용 형식).

    조문표기·법령명 모두 코드가 metadata 에서 가져오므로 LLM 이 번호를 지어낼 여지가 없다.
    """
    법령명 = metadata.get("법령명", "").strip()
    조문표기 = metadata.get("조문표기", "").strip()
    return f"{법령명} {조문표기}".strip()


def _norm(text: str) -> str:
    """조문표기 매칭용 정규화 — 공백 차이로 매칭이 깨지지 않게 모든 공백을 제거한다."""
    return "".join(text.split())


def _article_body(doc: str) -> str:
    """표시용 원문에서 parser 가 앞에 붙인 '법령명 조문표기(제목)' 헤더 줄을 제거한다.

    parser 가 항상 헤더 1줄 + '\\n' + 본문 구조로 저장하므로 첫 줄만 떼어낸다.
    """
    _head, sep, rest = doc.partition("\n")
    return rest if sep else doc


def _build_user_message(user_query: str, docs: list[str], metas: list[dict]) -> str:
    """LLM 에 줄 컨텍스트(사용자 질문 + 후보 조문들)를 조립한다."""
    lines = [f"[사용자 질문]\n{user_query}", "", "[후보 조문]"]
    for i, (doc, meta) in enumerate(zip(docs, metas), start=1):
        조문제목 = meta.get("조문제목", "").strip()
        lines.append(f"({i}) 조문표기: {_citation(meta)} / 제목: {조문제목}")
        lines.append(f"원문: {doc}")
    return "\n".join(lines)


def _extract_json(text: str) -> str:
    """LLM 응답에서 JSON 객체 부분만 안전하게 끄집어낸다.

    설명 텍스트·코드펜스(대소문자 무관)를 먼저 제거한 뒤
    첫 '{' ~ 마지막 '}' 를 슬라이싱한다.
    """
    # 코드펜스 제거: ```json, ```JSON, ``` 등 모두 (대소문자·언더스코어 무관)
    t = re.sub(r"```[\w]*\n?", "", text)
    t = re.sub(r"```", "", t).strip()

    start = t.find("{")
    end = t.rfind("}")
    if start != -1 and end != -1 and end > start:
        return t[start : end + 1]
    return t


_PARSE_ERROR_REPLY = "답변을 불러오지 못했어요. 잠시 후 다시 시도해 주세요."


def _generate_consultation(user_query: str, docs: list[str], metas: list[dict]) -> dict:
    """Claude 로 consultation + grounds JSON 을 생성한다. 파싱 실패 시 안전한 기본값을 반환한다."""
    try:
        raw = complete(
            system=_SYSTEM_PROMPT,
            user=_build_user_message(user_query, docs, metas),
            max_tokens=_MAX_TOKENS,
            temperature=_TEMPERATURE,
        )
    except RuntimeError as exc:
        raise RuntimeError(f"답변 생성 호출 실패: {exc}") from exc

    # 진단용 — 파싱 실패가 재발하면 로그로 원인 확인 (운영 배포 전 제거)
    logger.debug("chain raw (%d chars): %.600s", len(raw), raw)

    try:
        data = json.loads(_extract_json(raw))
    except json.JSONDecodeError:
        # raw 원문을 절대 사용자에게 노출하지 않는다 (JSON 키·구조 노출 방지).
        logger.warning("chain: JSON 파싱 실패 (%d chars): %.600s", len(raw), raw)
        return {"consultation": _PARSE_ERROR_REPLY, "grounds": []}
    return data


def _build_legal_grounds(llm_grounds: list[dict], docs: list[str], metas: list[dict]) -> list[dict]:
    """LLM 이 반환한 grounds 에 코드가 original/law_name/title 을 채운다.

    할루시네이션 가드 두 가지:
    1. LLM 이 검색 결과에 없는 조문을 돌려보내면 드롭 (article_lookup 에 없는 경우).
    2. article 값은 LLM 반환값이 아닌 metadata 값으로 덮어씀 (오타·변형 방어).
    """
    article_lookup: dict[str, tuple[str, dict]] = {
        _norm(_citation(m)): (docs[i], metas[i])
        for i, m in enumerate(metas)
    }

    result: list[dict] = []
    for g in llm_grounds:
        key = _norm(g.get("article", ""))
        if key not in article_lookup:
            continue  # 검색 결과에 없는 조문 → 드롭
        doc, meta = article_lookup[key]
        result.append({
            "law_name": meta.get("법령명", ""),
            "article":  meta.get("조문표기", ""),  # LLM 값 아닌 metadata 값으로 교체
            "title":    meta.get("조문제목", ""),
            "plain":    g.get("plain", ""),
            "original": _article_body(doc),
        })
    return result


def answer(user_query: str) -> dict:
    """사용자 질문에 대해 검색된 조문 근거로 상담 답변과 근거 법조문을 분리 반환한다.

    Returns:
        found=True:  {"consultation": str, "legal_grounds": list[dict], "sources": list[str], "found": True}
        found=False: {"consultation": <안내>, "legal_grounds": [], "sources": [], "found": False}
    """
    # 1) 일상어 → 가상 조문 변환 (검색 어휘 간극 완화, HyDE)
    transformed = transform_query(user_query)

    # 2) 변환문 임베딩 → ChromaDB 검색
    query_vector = embed_texts([transformed])[0]
    collection = get_collection()
    res = collection.query(
        query_embeddings=[query_vector],
        n_results=RETRIEVAL_TOP_K,
        include=["documents", "metadatas", "distances"],
    )
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    distances = res["distances"][0]

    # 3) 가드: 결과가 없거나 최상위 거리가 임계값을 넘으면 지어내지 않고 안내한다.
    if not docs or distances[0] > RETRIEVAL_DISTANCE_THRESHOLD:
        return {"consultation": _NOT_FOUND_REPLY, "legal_grounds": [], "sources": [], "found": False}

    # 4) LLM 에서 consultation + grounds(article/plain) 생성
    llm_data = _generate_consultation(user_query, docs, metas)

    # 5) grounds 에 코드가 original/law_name/title 채움 + 할루시네이션 드롭
    legal_grounds = _build_legal_grounds(llm_data.get("grounds", []), docs, metas)

    # 6) 출처는 코드가 만든 인용만 (LLM 생성 번호 배제), 검색 거리순
    sources = [_citation(m) for m in metas]

    suggest = bool(llm_data.get("suggest_document", False))
    doc_type = llm_data.get("document_type") if suggest else None

    # 면책 고지를 consultation 말미에 항상 1회 append (LLM 지시 방식 대체)
    base_consultation = llm_data.get("consultation", _NOT_FOUND_REPLY)
    consultation_with_notice = f"{base_consultation}\n\n{_CONSULTATION_NOTICE}"

    return {
        "consultation": consultation_with_notice,
        "legal_grounds": legal_grounds,
        "sources": sources,
        "found": True,
        "suggest_document": suggest,
        "document_type": doc_type,
    }
