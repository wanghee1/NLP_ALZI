"""ChromaDB 벡터스토어 초기화 및 적재.

chromadb.PersistentClient 를 직접 사용한다 (langchain 래퍼 미사용 — 의존성 최소화).
저장 경로·컬렉션명은 config.settings 상수로 관리한다 (coding-conventions).
순수 로직 계층이라 전송 계층(api/)에 의존하지 않는다.
"""

from __future__ import annotations

import chromadb
from chromadb.api.models.Collection import Collection

from config.settings import CHROMA_COLLECTION, VECTORSTORE_DIR

# 텍스트 임베딩 검색에는 cosine 이 표준이다 (ChromaDB 기본값은 L2 → 거리값이 1을 넘음).
# hnsw:space 는 컬렉션 '생성' 시점에만 적용되며, 이후에는 바꿀 수 없다.
_COLLECTION_METADATA = {"hnsw:space": "cosine"}


def get_collection() -> Collection:
    """영속 클라이언트에서 컬렉션을 가져오거나 생성해 반환한다.

    PersistentClient 는 VECTORSTORE_DIR 에 데이터를 디스크 저장하므로 별도 persist 호출이 불필요하다.

    주의: get_or_create_collection 은 기존 컬렉션이 있으면 metadata 를 무시한다.
    따라서 기존이 L2 로 만들어졌다면 cosine 이 적용되지 않으므로, 거리척도를 검사해 경고한다
    (cosine 으로 바꾸려면 reset_collection 으로 재생성 후 재적재해야 한다).
    """
    client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION, metadata=_COLLECTION_METADATA
    )
    space = (collection.metadata or {}).get("hnsw:space")
    if space != "cosine":
        print(
            f"[경고] 컬렉션 '{CHROMA_COLLECTION}' 의 거리척도가 '{space}' 입니다. "
            "cosine 적용을 위해 build_index 로 재적재(컬렉션 재생성)하세요."
        )
    return collection


def collection_exists_count() -> int:
    """기존 컬렉션의 문서 수를 반환한다 (없으면 0). 재생성 전 안내 출력용 — 경고 없이 조회만 한다."""
    client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
    try:
        existing = client.get_collection(name=CHROMA_COLLECTION)
    except Exception:  # noqa: BLE001 - 컬렉션 미존재 시 0 으로 간주
        return 0
    return existing.count()


def reset_collection() -> Collection:
    """기존 컬렉션을 삭제하고 cosine metric 으로 새로 생성한다 (재적재 진입점).

    get_or_create_collection 은 기존 컬렉션의 거리척도를 바꾸지 못하므로,
    metric 을 확실히 cosine 으로 적용하려면 삭제 후 재생성이 유일한 경로다.
    """
    client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
    try:
        client.delete_collection(name=CHROMA_COLLECTION)
    except Exception:  # noqa: BLE001 - 기존 컬렉션이 없으면 그대로 새로 만든다
        pass
    return client.create_collection(name=CHROMA_COLLECTION, metadata=_COLLECTION_METADATA)


def add_chunks(
    collection: Collection,
    *,
    ids: list[str],
    documents: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict[str, str]],
) -> None:
    """청크를 컬렉션에 적재한다.

    멱등성: add 가 아니라 upsert 를 사용해 재실행 시 같은 id 를 갱신한다
    (재적재 시 중복 적재·중복 id 에러 방지).

    Args:
        collection: get_collection() 으로 얻은 대상 컬렉션
        ids: 청크 고유 id ('법령명_법령구분명_제○조' 형식)
        documents: 임베딩 원문 (검색 결과로 반환할 조문 텍스트)
        embeddings: 각 document 의 벡터
        metadatas: 출처 메타데이터 (조문 번호·시행일자·수집일자 등)
    """
    if not ids:
        return
    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )
