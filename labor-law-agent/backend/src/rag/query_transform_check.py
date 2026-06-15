"""쿼리 변환(HyDE) 검색 개선 검증 스크립트 (일회성).

답변 생성(chain)을 만들기 전에, "사용자 질문 → 가상 조문 변환 → 검색"이
실제로 검색 품질을 끌어올리는지 눈으로 확인하는 목적이다.

각 질문마다 '변환 전 vs 변환 후' 검색 결과를 나란히 출력한다.
판정 기준: 변환 후 검색에서 기대 조문(제55조·제23조 등)이 상위 3위 안에 들어오는가.

retriever_check 의 TEST_QUERIES·_format_source 를 재사용한다 (질문/출처표기 단일 출처 유지).

실행:
    cd backend
    python -m src.rag.query_transform_check

사전 준비: build_index.py 로 적재 완료 + backend/.env 에 OPENAI_API_KEY 설정.
"""

from __future__ import annotations

import sys

from src.rag.embeddings import embed_texts
from src.rag.query_transform import transform_query
from src.rag.retriever_check import TEST_QUERIES, _format_source
from src.rag.vectorstore import get_collection

N_RESULTS = 3


def _print_results(metadatas: list[dict], distances: list[float]) -> None:
    """검색 상위 결과를 들여쓰기해 출력한다."""
    if not metadatas:
        print("    (검색 결과 없음)")
        return
    for rank, (meta, dist) in enumerate(zip(metadatas, distances), start=1):
        print(f"    {rank}. {_format_source(meta)}  거리={dist:.4f}")


def main() -> int:
    collection = get_collection()
    metric = (collection.metadata or {}).get("hnsw:space", "(미지정)")
    print(f"[쿼리변환 검증] 적재 개수: {collection.count()} | 거리척도: {metric}\n")

    questions = [q for q, _ in TEST_QUERIES]

    # 1) 질문들을 가상 조문으로 변환 (GPT-4o, 질문당 1회)
    try:
        transformed = [transform_query(q) for q in questions]
    except RuntimeError as exc:
        print(f"[실패] 쿼리 변환 단계: {exc}")
        return 1

    # 2) 원본 + 변환문을 한 번에 임베딩 (호출 수 절감, 순서 보존)
    try:
        vectors = embed_texts(questions + transformed)
    except RuntimeError as exc:
        print(f"[실패] 임베딩 단계: {exc}")
        return 1
    orig_vectors = vectors[: len(questions)]
    trans_vectors = vectors[len(questions) :]

    for i, (question, hint) in enumerate(TEST_QUERIES):
        print("=" * 76)
        print(f"Q. {question}    [{hint}]")
        print("-" * 76)

        # 변환 전 검색
        print("  [원본 질문으로 검색]")
        res_o = collection.query(
            query_embeddings=[orig_vectors[i]],
            n_results=N_RESULTS,
            include=["metadatas", "distances"],
        )
        _print_results(res_o["metadatas"][0], res_o["distances"][0])

        # 변환 결과 육안 확인 (실제로 무엇으로 바뀌었는지)
        print(f"\n  [변환된 가상조문]\n    {transformed[i]}")

        # 변환 후 검색
        print("\n  [변환 질문으로 검색]")
        res_t = collection.query(
            query_embeddings=[trans_vectors[i]],
            n_results=N_RESULTS,
            include=["metadatas", "distances"],
        )
        t_metas = res_t["metadatas"][0]
        t_dists = res_t["distances"][0]
        _print_results(t_metas, t_dists)

        # 가드3: 변환 후 최상위 거리. 너무 크면 변환이 엉뚱했다는 신호.
        if t_dists:
            print(f"    └ 변환 후 최상위 거리: {t_dists[0]:.4f}")
        print()

    print("=" * 76)
    print("[검증 종료] 변환 후 검색에서 기대 조문(제55조·제23조 등)이 상위 3위에 드는지 확인하라.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
