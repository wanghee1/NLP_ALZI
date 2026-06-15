"""판례 수집 클라이언트.

국가법령정보센터 판례 API 또는 대법원 판례 공개 데이터를 활용한다.
"""

from __future__ import annotations


async def fetch_precedents(keyword: str, max_count: int = 100) -> list[dict]:
    """키워드 관련 판례를 수집한다.

    Args:
        keyword: 검색 키워드 (예: '최저임금 위반', '부당해고')
        max_count: 최대 수집 건수

    Returns:
        판례 딕셔너리 리스트 [{case_no, title, summary, full_text}, ...]
    """
    # TODO: 판례 API 엔드포인트 확인 후 httpx 호출 구현
    # TODO: 페이지네이션 처리
    # TODO: data/raw/precedents/ 에 JSON으로 저장
    raise NotImplementedError
