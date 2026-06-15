"""문서 유형 분류기.

사용자 의도(채팅 히스토리 또는 명시적 선택)에서 생성할 문서 유형을 결정한다.
"""

from __future__ import annotations

from api.schemas import DocumentType


async def classify_document_type(session_history: list[dict]) -> DocumentType:
    """대화 히스토리를 분석하여 적합한 문서 유형을 반환한다.

    Args:
        session_history: 세션의 전체 메시지 목록

    Returns:
        DocumentType enum 값
    """
    # TODO: LLM 분류 또는 키워드 규칙 기반 분류
    # 예: '내용증명' 언급 → NOTICE_OF_CLAIM
    #     '진정', '고용노동부' 언급 → COMPLAINT
    #     '근로계약서 작성' 언급 → STANDARD_CONTRACT
    raise NotImplementedError
