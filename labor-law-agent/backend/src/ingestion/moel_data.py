"""고용노동부(MOEL) 공공데이터 수집.

공공데이터포털 DATA_GO_KR_API_KEY를 사용하여 고용노동부 행정 데이터를 가져온다.
예: 최저임금 고시, 표준근로계약서 가이드라인
"""

from __future__ import annotations


async def fetch_minimum_wage_history() -> list[dict]:
    """연도별 최저임금 이력을 수집한다.

    Returns:
        [{year, hourly_wage, monthly_wage}, ...] 형태의 리스트
    """
    # TODO: data.go.kr 고용노동부 최저임금 API 호출
    raise NotImplementedError


async def fetch_standard_contract_guide() -> str:
    """표준근로계약서 작성 가이드라인 텍스트를 가져온다."""
    # TODO: 고용노동부 공식 가이드 PDF 또는 API 활용
    raise NotImplementedError
