"""노동 법령 적재 메인 스크립트 (일회성 실행).

대상 법령을 목록 API로 찾아 본법(법령구분명='법률')의 본문을 받아오고,
parser 로 조문 단위 청킹 → OpenAI 임베딩 → ChromaDB 에 적재한다.

멱등성: 청크 id 가 '법령명_법령구분명_제○조' 로 고정되고 upsert 를 쓰므로,
        재실행해도 중복 적재되지 않고 최신 내용으로 갱신된다.

이 스크립트는 ingestion(일회성) 계층이며 런타임 요청 경로(api/)에 의존하지 않는다.

실행:
    cd backend
    python -m src.ingestion.build_index

사전 준비: backend/.env 에 OPENAI_API_KEY, LAW_API_KEY 설정.
"""

from __future__ import annotations

import sys
from datetime import date

from src.ingestion.law_api import fetch_law_body, fetch_law_list
from src.ingestion.parser import parse_articles
from src.rag.embeddings import embed_texts
from src.rag.vectorstore import (
    add_chunks,
    collection_exists_count,
    get_collection,
    reset_collection,
)

# 적재 대상 법령 (현재는 본법만. 시행령/시행규칙은 확장 시 추가)
TARGET_LAWS = ["근로기준법", "최저임금법"]

# 본법만 적재한다 (시행령/시행규칙은 조문번호가 겹쳐 혼동 가능 — 우선 법률 본문부터)
TARGET_KIND = "법률"


def _select_target(items: list[dict[str, str]], law_name: str) -> dict[str, str] | None:
    """목록 결과에서 본법(법령명 정확 일치 + 법령구분명='법률')을 고른다.

    검색어 하나로 시행령·시행규칙까지 반환되므로 정확 일치로 본법만 추린다.
    """
    for item in items:
        if item["법령명"] == law_name and item["법령구분명"] == TARGET_KIND:
            return item
    return None


def index_law(law_name: str, 수집일자: str) -> int:
    """단일 법령을 적재하고 적재된 조문 수를 반환한다."""
    items = fetch_law_list(law_name)
    target = _select_target(items, law_name)
    if target is None:
        print(f"  [경고] '{law_name}' 의 본법(법령구분명={TARGET_KIND})을 목록에서 찾지 못함 — 건너뜀.")
        return 0

    mst = target["MST"]
    body_xml = fetch_law_body(mst)
    chunks = parse_articles(
        body_xml,
        법령명=law_name,
        법령구분명=target["법령구분명"],
        mst=mst,
        수집일자=수집일자,
    )
    if not chunks:
        print(f"  [경고] '{law_name}' 에서 조문 청크를 만들지 못함 — 본문 구조 확인 필요.")
        return 0

    # 임베딩 → 적재 (id 순서와 벡터 순서를 일치시켜 전달)
    texts = [c.text for c in chunks]
    embeddings = embed_texts(texts)

    collection = get_collection()
    add_chunks(
        collection,
        ids=[c.id for c in chunks],
        documents=texts,
        embeddings=embeddings,
        metadatas=[c.metadata for c in chunks],
    )
    return len(chunks)


def main() -> int:
    수집일자 = date.today().isoformat()  # 법령 개정 추적용 (rag-and-llm 인덱싱 규칙)
    print(f"[적재 시작] 대상: {', '.join(TARGET_LAWS)} (수집일자={수집일자})")

    # 거리척도를 cosine 으로 확실히 적용하기 위해 기존 컬렉션을 삭제하고 재생성한다.
    # (실수 방지용으로 삭제 대상 규모를 먼저 안내한다.)
    existing = collection_exists_count()
    print(f"[재생성] 기존 컬렉션 문서 {existing}개를 삭제하고 cosine 거리척도로 재적재합니다.")
    reset_collection()

    total = 0
    for law_name in TARGET_LAWS:
        print(f"\n- {law_name} 적재 중...")
        try:
            count = index_law(law_name, 수집일자)
        except RuntimeError as exc:
            # 한 법령이 실패해도 나머지는 계속 진행한다.
            print(f"  [실패] {law_name}: {exc}")
            continue
        total += count
        if count:
            print(f"  [완료] {law_name}: 조문 {count}개 적재")

    print(f"\n[적재 종료] 총 {total}개 조문 적재 완료.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
