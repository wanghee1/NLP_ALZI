"""문서 필드 자동 추출기.

채팅 히스토리에서 문서 작성에 필요한 정보(당사자명, 날짜, 금액 등)를 추출한다.
"""

from __future__ import annotations

from api.schemas import DocumentType


async def extract_fields(
    session_history: list[dict],
    doc_type: DocumentType,
) -> dict:
    """세션 히스토리에서 문서 템플릿에 필요한 필드를 추출한다.

    Args:
        session_history: 채팅 메시지 목록
        doc_type: 생성할 문서 유형

    Returns:
        템플릿 변수 딕셔너리 (예: {worker_name, employer_name, start_date, wage, ...})
    """
    # TODO: doc_type별 필수 필드 목록 정의
    # TODO: LLM에 히스토리와 필드 목록을 주고 JSON 추출 요청
    # TODO: 누락 필드는 None으로 표시하여 caller가 사용자에게 재질문 가능하게
    raise NotImplementedError


def get_required_fields(doc_type: DocumentType) -> list[str]:
    """문서 유형별 필수 필드 목록을 반환한다."""
    # TODO: 각 DOCX 템플릿의 {{변수}} 목록과 일치시켜 관리
    _fields: dict[DocumentType, list[str]] = {
        DocumentType.NOTICE_OF_CLAIM: [
            "sender_name", "sender_address", "recipient_name",
            "recipient_address", "claim_amount", "claim_reason", "send_date",
        ],
        DocumentType.COMPLAINT: [
            "complainant_name", "complainant_address", "respondent_name",
            "respondent_company", "violation_details", "filing_date",
        ],
        DocumentType.STANDARD_CONTRACT: [
            "worker_name", "employer_name", "workplace", "job_description",
            "start_date", "end_date", "work_hours", "wage", "pay_date",
        ],
    }
    return _fields.get(doc_type, [])
