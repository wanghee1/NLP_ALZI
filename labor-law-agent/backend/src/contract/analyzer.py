"""계약서 위험 조항 탐지 — Phase 5-A (LLM 단독).

Claude 에게 계약서 텍스트를 넘기고 위법·불리·누락 조항을 JSON 배열로 받는다.
Phase 5-B 에서 RAG 출처 검증이 추가될 예정이므로, 지금은 law_hint(쟁점 키워드)까지만 반환한다.

보안: 계약서 원문을 로그에 출력하지 않는다 (rag-and-llm.md, security.md).
LLM 규칙: issue/suggestion 에 조문번호 단정 금지 — "가능성" 표현 유지 (rag-and-llm.md).
"""

from __future__ import annotations

import json
import logging
import re

from config.settings import MIN_WAGE_HOURLY, MIN_WAGE_MONTHLY, MIN_WAGE_YEAR
from src.contract.pdf_parser import ScannedPdfError, extract_text, render_pages_to_images
from src.llm.client import complete, complete_with_images

logger = logging.getLogger(__name__)

_MIN_OCR_TEXT = 100  # 비전 OCR 결과도 이 미만이면 실패로 간주

_OCR_SYSTEM = "당신은 문서 이미지에서 텍스트를 정확히 추출하는 OCR 도구입니다."
_OCR_USER = (
    "이 근로계약서 이미지에서 텍스트를 정확히 읽어 그대로 추출하세요. "
    "해석·요약·의견 없이 원문 텍스트만 출력하세요."
)

_SEVERITY_ORDER: dict[str, int] = {"높음": 0, "중간": 1, "낮음": 2}
_TYPE_ORDER: dict[str, int] = {"위법": 0, "불리": 1, "누락": 2}

_SYSTEM_PROMPT = f"""당신은 대한민국 근로계약서를 검토하는 노동법 전문가입니다.
아래 계약서 텍스트에서 위법·불리·누락 조항을 탐지하여 JSON 배열만 반환하세요.

출력 제약 (반드시 준수):
- 응답의 첫 글자는 반드시 [ 이어야 합니다.
- 응답의 마지막 글자는 반드시 ] 이어야 합니다.
- 객체({{"key": [...]}})로 감싸지 마세요. 배열 [...]만 출력하세요.
- 코드펜스(```)·설명·인사말·머리말 일절 금지.
- 문제 없으면 빈 배열 [] 만 출력하세요.

## 탐지 기준

[위법] 법령 위반 가능성 있는 조항
- 최저임금 미달: 시급 {MIN_WAGE_HOURLY:,}원({MIN_WAGE_YEAR}년 기준) 또는 월급 {MIN_WAGE_MONTHLY:,}원(209시간 기준) 미만
- 위약금·손해배상액 예정 약정
- 법적 근거 없는 임금 공제
- 강제근로·감금·협박 조항
- 해고예고 없는 즉시해고

[불리] 위반은 아니나 근로자에게 일방적으로 불리한 조항
- 사용자 단독 근로조건 변경권
- 수습 기간 3개월 초과 또는 수습 중 최저임금 90% 미만 감액
- 연장·야간·휴일수당 포기 합의
- 과도한 경업금지·비밀유지 의무
- 지각·조퇴 시 일당 전액 공제 등 과도한 제재

[누락] 근로기준법 제17조 필수 기재사항 부재
- ① 임금 구성항목·계산방법·지급방법
- ② 소정근로시간
- ③ 휴일 (주휴일 포함)
- ④ 연차유급휴가

## 출력 규칙
1. JSON 배열만 반환. 배열 외 텍스트 일절 금지.
2. issue 에 "제○조 위반" 식 조문번호 단정 금지 → "~가능성이 있습니다", "~해당할 수 있습니다" 톤 유지.
3. law_hint 는 5~10자 이내 핵심 키워드만 (추후 RAG 검색 단서용).
4. severity 기준:
   - 높음: 명백한 법 위반 가능성, 금전적 피해 직결
   - 중간: 법적 경계선상이거나 상당히 불리
   - 낮음: 실질 피해 작음
5. suggestion 작성 규칙:
   - 해당 조항을 어떻게 수정하거나 추가해야 하는지 구체적·실행가능하게 제안.
   - 가능하면 수정 예시 문구를 직접 제시 (예: '시급 {MIN_WAGE_HOURLY:,}원으로 지급한다.').
   - 톤: "~하는 것이 좋아요", "~권장돼요" — "이렇게 하면 무조건 합법" 단정 금지.
   - 조문번호 직접 인용 금지.
   - 알바생도 이해할 수 있는 쉬운 말.

[출력 형식]
[
  {{
    "type": "위법" | "불리" | "누락",
    "clause": "문제되는 조항 원문 또는 누락 항목명",
    "issue": "알바생도 이해할 수 있는 쉬운 설명 (단정 금지, 가능성 표현)",
    "law_hint": "최저임금 미달",
    "severity": "높음" | "중간" | "낮음",
    "suggestion": "구체적 수정 제안 + 가능하면 예시 문구"
  }}
]"""


def _parse_violations(raw: str) -> list[dict]:
    """Claude 응답에서 JSON 배열을 안전하게 파싱한다.

    4단계 시도:
    1) 코드펜스 제거 후 직접 파싱
    2) JSON 객체 래핑({violations:[...]} 등)에서 배열 추출
    3) 마지막 ] 기준으로 앞에서 첫 [ 찾아 슬라이싱 (greedy regex 대체)
    4) 모두 실패 시 빈 배열 fallback + raw 앞부분 경고 로그
    """
    # 코드펜스 제거 (대소문자 무관, 언더스코어·숫자 포함 언어 이름 허용)
    cleaned = re.sub(r"```[\w]*\n?", "", raw)
    cleaned = re.sub(r"```", "", cleaned).strip()

    # ── 단계 1: 직접 파싱 (가장 깔끔한 경우) ──────────────────────────────
    try:
        result = json.loads(cleaned)
        if isinstance(result, list):
            return result
        # 단계 2로 연결 (객체 래핑)
        if isinstance(result, dict):
            for key in ("violations", "result", "items", "data"):
                if isinstance(result.get(key), list):
                    return result[key]
    except json.JSONDecodeError:
        pass

    # ── 단계 3: 마지막 ] 기준 슬라이싱 ───────────────────────────────────
    # greedy regex \[.*\] 는 응답이 잘려 ] 가 없으면 None 반환하는 문제 있음.
    # rfind(']') + rindex('[', 0, end) 로 마지막 완결된 배열 구간을 찾는다.
    end = cleaned.rfind("]")
    if end != -1:
        start = cleaned.rfind("[", 0, end + 1)
        if start != -1:
            candidate = cleaned[start: end + 1]
            try:
                result = json.loads(candidate)
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass

    # ── 단계 4: fallback ─────────────────────────────────────────────────
    # 개인정보 보호를 위해 앞 800자만 기록한다 (시연용 — 운영에서는 제거).
    logger.warning(
        "analyze_contract: JSON 파싱 실패. raw 앞부분(%d chars total): %.800s",
        len(raw),
        raw,
    )
    return []


def analyze_contract(contract_text: str) -> list[dict]:
    """계약서 텍스트에서 위법·불리·누락 조항을 탐지한다.

    Args:
        contract_text: pdf_parser.extract_text() 결과

    Returns:
        ViolationItem 형식의 dict 리스트, 심각도순(높음→중간→낮음) + type순(위법→불리→누락) 정렬.
        문제 없으면 빈 리스트.
    """
    raw = complete(
        system=_SYSTEM_PROMPT,
        user=contract_text,
        max_tokens=4096,
        temperature=0.1,
    )
    violations = _parse_violations(raw)
    violations.sort(key=lambda v: (
        _SEVERITY_ORDER.get(v.get("severity", ""), 99),
        _TYPE_ORDER.get(v.get("type", ""), 99),
    ))
    return violations


def _ocr_images_to_text(images: list[bytes]) -> str:
    """페이지 이미지 리스트를 비전 OCR 로 텍스트로 변환한다.

    이미지·결과를 로그에 출력하지 않는다 (security).
    """
    return complete_with_images(
        system=_OCR_SYSTEM,
        user_text=_OCR_USER,
        images=images,
        max_tokens=4096,
        temperature=0.0,
    )


def analyze_contract_from_pdf(file_bytes: bytes) -> tuple[list[dict], bool]:
    """PDF bytes 에서 위반 조항을 탐지한다.

    텍스트 PDF 는 PyMuPDF 직접 추출을 사용하고(빠른 경로),
    스캔/이미지 PDF 는 Claude 비전 OCR 로 우회한 뒤 기존 analyze_contract 에 합류한다.

    Returns:
        (violations, used_vision)
        used_vision=True 이면 비전 OCR 경로를 사용한 것.

    Raises:
        ScannedPdfError: 텍스트 추출도 비전 OCR 도 실패한 경우 (상위에서 "읽을 수 없음" 안내).
        ValueError: PDF 자체가 손상된 경우.
    """
    # ── 1) 텍스트 추출 시도 (빠른 경로) ──────────────────────────────────────
    try:
        text = extract_text(file_bytes)
        return analyze_contract(text), False
    except ScannedPdfError:
        pass  # 비전으로 우회

    # ── 2) 비전 OCR 시도 ──────────────────────────────────────────────────────
    images = render_pages_to_images(file_bytes)
    try:
        ocr_text = _ocr_images_to_text(images)
    finally:
        del images  # 이미지 바이트 즉시 해제 (security)

    if len(ocr_text.strip()) < _MIN_OCR_TEXT:
        raise ScannedPdfError(
            "이미지 인식으로도 텍스트를 읽을 수 없는 PDF입니다. "
            "선명한 스캔본 또는 텍스트 PDF 를 업로드해 주세요."
        )

    return analyze_contract(ocr_text), True
