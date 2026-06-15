"""텍스트 임베딩 유틸리티.

OpenAI text-embedding-3-small 을 직접 호출한다 (langchain 미사용 — 의존성 최소화).
API 키는 config.settings 경유로만 로딩하며, 키를 로그/예외 메시지에 노출하지 않는다 (security 규칙).
순수 로직 계층(src/rag)이라 전송 계층(api/)에 의존하지 않는다.
"""

from __future__ import annotations

from openai import OpenAI

from config.settings import EMBEDDING_MODEL, OPENAI_API_KEY

# 한 번의 API 호출에 보낼 최대 텍스트 수 (대량 조문 적재 시 분할 호출).
_BATCH_SIZE = 100

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """OpenAI 클라이언트를 지연 초기화한다 (키 미설정 시 명확히 실패)."""
    global _client
    if _client is None:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY 미설정 — backend/.env 를 확인하라.")
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def embed_texts(texts: list[str]) -> list[list[float]]:
    """텍스트 리스트를 임베딩 벡터 리스트로 변환한다 (입력 순서 보존).

    Args:
        texts: 임베딩할 텍스트 청크 목록

    Returns:
        각 텍스트의 float 벡터 목록 (len(texts) 와 동일 길이).

    Raises:
        RuntimeError: 임베딩 API 호출 실패 (키는 메시지에 노출하지 않음).
    """
    if not texts:
        return []

    client = _get_client()
    vectors: list[list[float]] = []
    for start in range(0, len(texts), _BATCH_SIZE):
        batch = texts[start : start + _BATCH_SIZE]
        try:
            resp = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        except Exception as exc:  # noqa: BLE001 - 키 노출 방지 위해 타입만 보고
            raise RuntimeError(
                f"임베딩 호출 실패(batch {start // _BATCH_SIZE}): {type(exc).__name__}"
            ) from exc
        # 응답은 입력 순서를 보장하지만, index 순으로 정렬해 안전하게 추출한다.
        vectors.extend(item.embedding for item in sorted(resp.data, key=lambda d: d.index))
    return vectors
