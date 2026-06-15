"""표준근로계약서 기준 데이터.

고용노동부 표준근로계약서의 필수 조항 목록과 체크 항목을 정의한다.
"""

from __future__ import annotations


MANDATORY_CLAUSES = [
    "임금(기본급·수당·지급 방법·지급일)",
    "소정근로시간",
    "휴일",
    "연차유급휴가",
    "취업 장소 및 업무 내용",
    "근로계약 기간",
]


def get_standard_clauses() -> list[str]:
    """고용노동부 표준근로계약서의 필수 포함 조항 목록을 반환한다."""
    # TODO: 조항 목록을 DB 또는 설정 파일로 분리하여 업데이트 가능하게 관리
    return MANDATORY_CLAUSES


def check_missing_clauses(contract_clauses: list[str]) -> list[str]:
    """계약서에서 누락된 필수 조항을 찾는다.

    Args:
        contract_clauses: pdf_parser.extract_clauses() 결과

    Returns:
        누락된 필수 조항 이름 리스트
    """
    # TODO: 의미론적 유사도(임베딩) 또는 키워드 매칭으로 조항 존재 확인
    raise NotImplementedError
