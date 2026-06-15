"""law.go.kr 본문 XML → 조문 단위 청크 변환 (적재 파이프라인의 청킹 핵심).

탐색으로 확인한 실제 응답 구조에 맞춰 파싱한다 (2026-05-29 근로기준법 본문 기준):

  <조문여부> 실제 값은 두 종류뿐:
    · "전문"  → 장(章) 제목 행 (예: "제1장 총칙"). 실제 조문이 아니므로 임베딩에서 제외하고
                현재_장 컨텍스트로만 사용한다. (근로기준법 기준 13개)
    · "조문"  → 실제 조문. 청크 1개로 만든다. (근로기준법 기준 132개)

  가지조문(예: 제43조의2)은 <조문번호>43 + <조문가지번호>2 로 표현된다.
  <조문가지번호> 값이 "0"/빈값이면 일반조문, 그 외 숫자면 가지조문이다.
  → "제43조"와 "제43조의2"가 같은 id/출처표기로 충돌하지 않도록 라벨에 반영한다.

  본문 텍스트는 <조문내용>(머리행) + 하위 <항내용>/<호내용>/<목내용> 을 문서 순서대로
  이어붙여야 조문 전문이 완성된다 (호가 많은 조는 조문내용에 헤더만 있음).

이 모듈은 순수 파싱 로직이며 런타임(api/)·전송 계층에 의존하지 않는다 (architecture 규칙).
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

# 조문 본문을 구성하는 콘텐츠 태그 (문서 순서대로 이어붙인다)
_CONTENT_TAGS = ("조문내용", "항내용", "호내용", "목내용")

# 가지조문이 아님을 뜻하는 <조문가지번호> 값
_NO_BRANCH = ("", "0")


@dataclass
class LawChunk:
    """벡터스토어 적재 단위. 출처 명시(rag-and-llm)를 위해 메타데이터를 함께 들고 다닌다."""

    id: str
    text: str
    metadata: dict[str, str]


def _clean(text: str | None) -> str:
    """CDATA 안의 선행 공백·들여쓰기·중복 공백을 정규화한다.

    원문에 들여쓰기 공백과 줄바꿈이 많아, 임베딩 품질을 위해 공백을 한 칸으로 모은다.
    """
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def _article_label(jo_num: str, branch_num: str) -> str:
    """조문 출처 표기를 만든다. 가지조문이면 '제○조의□', 아니면 '제○조'.

    인용 형식 규칙(rag-and-llm: '근로기준법 제○조')에 맞춘 정확한 표기를 보장한다.
    """
    if branch_num and branch_num.strip() not in _NO_BRANCH:
        return f"제{jo_num}조의{branch_num.strip()}"
    return f"제{jo_num}조"


def parse_articles(
    xml: str,
    *,
    법령명: str,
    법령구분명: str,
    mst: str,
    수집일자: str,
) -> list[LawChunk]:
    """본문 XML을 순회하여 조문 단위 청크 리스트를 만든다.

    Args:
        xml: lawService.do 가 반환한 본문 XML 문자열
        법령명: 출처 표기에 쓸 법령명 (예: '근로기준법')
        법령구분명: 법률/시행령/시행규칙 (id 충돌 방지 및 출처 메타)
        mst: 법령 마스터 일련번호 (출처 추적용)
        수집일자: 수집 시점 (법령 개정 대비 — rag-and-llm 인덱싱 규칙)

    Returns:
        LawChunk 리스트 (장 제목 '전문'은 제외).
    """
    root = ET.fromstring(xml)

    # 시행일자는 조문이 아니라 <기본정보> 에 있다. 모든 조문 청크의 공통 메타로 사용.
    시행일자 = _clean(root.findtext(".//기본정보/시행일자"))

    현재_장 = ""  # 직전에 만난 '전문'(장 제목)을 일반 조문의 소속_장으로 부착
    chunks: list[LawChunk] = []

    for unit in root.findall(".//조문단위"):
        조문여부 = _clean(unit.findtext("조문여부"))

        if 조문여부 == "전문":
            # 장 제목 행 (예: '제1장 총칙'). 임베딩하지 않고 컨텍스트로만 기억한다.
            현재_장 = _clean(unit.findtext("조문내용"))
            continue

        조문번호 = _clean(unit.findtext("조문번호"))
        조문가지번호 = _clean(unit.findtext("조문가지번호"))
        조문제목 = _clean(unit.findtext("조문제목"))
        label = _article_label(조문번호, 조문가지번호)

        # 조문내용 + 하위 항/호/목 을 문서 순서대로 결합 → 조문 전문 복원
        parts: list[str] = []
        for el in unit.iter():
            if el.tag in _CONTENT_TAGS:
                cleaned = _clean(el.text)
                if cleaned:
                    parts.append(cleaned)
        body = "\n".join(parts)

        # 검색 품질·가독성을 위해 본문 앞에 '법령명 제○조(제목)' 헤더를 붙인다.
        header = f"{법령명} {label}"
        if 조문제목:
            header += f"({조문제목})"
        text = f"{header}\n{body}" if body else header

        # id 에 법령구분명 포함 → 시행령/시행규칙 확장 시 조문번호 충돌 방지
        chunk_id = f"{법령명}_{법령구분명}_{label}"

        metadata = {
            "법령명": 법령명,
            "법령구분명": 법령구분명,
            "조문번호": 조문번호,
            "조문가지번호": 조문가지번호 or "0",
            "조문표기": label,
            "조문제목": 조문제목,
            "소속_장": 현재_장,
            "시행일자": 시행일자,
            "MST": mst,
            "수집일자": 수집일자,
        }
        chunks.append(LawChunk(id=chunk_id, text=text, metadata=metadata))

    return chunks
