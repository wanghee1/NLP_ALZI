"""검색 검증 게이트 스크립트 (일회성).

Phase 3(RAG 검색/답변) 코드를 짜기 전에, 적재된 ChromaDB 데이터가 검색에서
의도대로 매칭되는지 사람이 눈으로 확인하는 목적이다. 런타임 경로(api/)에 넣지 않는다.

검증 방식: 대표 질문을 임베딩 → collection.query(n_results=3) → 상위 매칭 조문을
"법령명 법령구분명 조문표기 (조문제목)  거리=..." 형태로 질문별로 출력한다.

거리(distance)는 작을수록 유사하다(chromadb 기본 L2/코사인 거리). 기대 조문이
상위에 올라오는지로 적재·임베딩 품질을 가늠한다.

실행:
    cd backend
    python -m src.rag.retriever_check

사전 준비: build_index.py 로 적재 완료 + backend/.env 에 OPENAI_API_KEY 설정.
"""

from __future__ import annotations

import sys

from src.rag.embeddings import embed_texts
from src.rag.vectorstore import get_collection

# (질문, 기대 결과 힌트) — 힌트는 사람이 눈으로 대조하기 위한 참고용일 뿐, 자동 판정하지 않는다.
TEST_QUERIES: list[tuple[str, str]] = [
    ("주휴수당을 못 받았어요", "기대: 근로기준법 제55조(휴일)"),
    ("최저임금은 얼마인가요", "기대: 최저임금법"),
    ("사장이 갑자기 해고했어요", "기대: 근로기준법 제23조 부근(해고 제한)"),
    ("월급을 14일 넘게 안 줘요", "기대: 근로기준법 제36조(금품 청산)"),
]

N_RESULTS = 3


def _format_source(metadata: dict[str, str]) -> str:
    """메타데이터에서 출처 표기를 만든다.

    조문표기 키가 있으면 그대로 쓰고(가지조문 포함 정확 표기), 없으면 조문번호+가지번호로 구성한다.
    """
    표기 = metadata.get("조문표기")
    if not 표기:
        조문번호 = metadata.get("조문번호", "?")
        가지 = metadata.get("조문가지번호", "0")
        표기 = f"제{조문번호}조" if 가지 in ("", "0", None) else f"제{조문번호}조의{가지}"

    법령명 = metadata.get("법령명", "?")
    법령구분명 = metadata.get("법령구분명", "")
    조문제목 = metadata.get("조문제목", "")
    제목부 = f" ({조문제목})" if 조문제목 else ""
    return f"{법령명} {법령구분명} {표기}{제목부}".strip()


def main() -> int:
    collection = get_collection()
    metric = (collection.metadata or {}).get("hnsw:space", "(미지정)")
    print(f"[검색 검증] 컬렉션 적재 개수: {collection.count()} | 거리척도: {metric}\n")

    # 질문들을 한 번에 임베딩해 호출 수를 줄인다 (embed_texts 는 순서를 보존).
    questions = [q for q, _ in TEST_QUERIES]
    try:
        query_vectors = embed_texts(questions)
    except RuntimeError as exc:
        print(f"[실패] 질문 임베딩 단계: {exc}")
        return 1

    for (question, hint), vector in zip(TEST_QUERIES, query_vectors):
        print("=" * 72)
        print(f"Q. {question}    [{hint}]")
        print("-" * 72)
        try:
            res = collection.query(
                query_embeddings=[vector],
                n_results=N_RESULTS,
                include=["metadatas", "distances"],
            )
        except Exception as exc:  # noqa: BLE001 - 게이트 스크립트라 단계만 보고
            print(f"  [실패] 검색 단계: {type(exc).__name__}")
            continue

        metadatas = res["metadatas"][0]
        distances = res["distances"][0]
        if not metadatas:
            print("  (검색 결과 없음 — 적재 상태를 확인하라)")
            continue

        for rank, (meta, dist) in enumerate(zip(metadatas, distances), start=1):
            print(f"  {rank}. {_format_source(meta)}  거리={dist:.4f}")
        print()

    print("=" * 72)
    print("[검증 종료] 각 질문의 상위 결과에 기대 조문이 보이는지 눈으로 확인하라.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
