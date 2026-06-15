"""벡터스토어 기반 문서 검색기.

쿼리에 가장 관련 있는 법령·판례 청크를 반환한다.
"""

from __future__ import annotations

from langchain_core.documents import Document


async def retrieve(query: str, top_k: int | None = None) -> list[Document]:
    """쿼리와 유사도가 높은 상위 top_k 개 문서 청크를 반환한다.

    Args:
        query: 사용자 검색 문자열
        top_k: 반환 개수 (None이면 settings.retriever_top_k 사용)

    Returns:
        관련 Document 청크 리스트
    """
    # TODO: vectorstore.load_vectorstore() 로 스토어 로드
    # TODO: similarity_search_with_score(query, k=top_k) 호출
    # TODO: 점수 임계값 필터링
    raise NotImplementedError
