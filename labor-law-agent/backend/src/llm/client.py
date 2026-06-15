"""공용 Anthropic Claude 클라이언트.

채팅(LLM) 호출 지점이 여러 곳(query_transform, chain, 곧 추가될 analyzer)으로 늘어나
공용으로 분리한다. 임베딩은 OpenAI 를 그대로 쓰므로(embeddings.py) 여기서 다루지 않는다.

순수 로직 계층이라 전송 계층(api/)에 의존하지 않는다 (architecture).
API 키는 config.settings 경유로만 로딩하며, 키/입력을 로그·예외 메시지에 노출하지 않는다 (security).
"""

from __future__ import annotations

import base64

import anthropic

from config.settings import ANTHROPIC_API_KEY, LLM_MODEL

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    """Anthropic 클라이언트를 지연 초기화한다 (키 미설정 시 명확히 실패)."""
    global _client
    if _client is None:
        if not ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY 미설정 — backend/.env 를 확인하라.")
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def complete(
    system: str,
    user: str,
    max_tokens: int = 1024,
    temperature: float = 0.3,
    model: str | None = None,
) -> str:
    """Claude Messages API 로 단발 완성을 요청하고 텍스트만 반환한다.

    Args:
        system: 시스템 프롬프트 (top-level system 파라미터로 전달)
        user: 사용자 메시지 (messages 의 단일 user 턴)
        max_tokens: 생성 토큰 상한
        temperature: 샘플링 온도
        model: 모델 ID (None 이면 settings.LLM_MODEL)

    Returns:
        응답 텍스트 (content 블록의 text 를 이어붙인 문자열, strip 적용).

    Raises:
        RuntimeError: 호출 실패 (키/입력은 메시지에 노출하지 않음).
    """
    client = _get_client()
    try:
        resp = client.messages.create(
            model=model or LLM_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
    except Exception as exc:  # noqa: BLE001 - 키 노출 방지 위해 타입만 보고
        raise RuntimeError(f"LLM 호출 실패: {type(exc).__name__}") from exc

    # content 는 블록 리스트. 텍스트 블록(.text)만 안전하게 모은다.
    parts: list[str] = []
    for block in resp.content:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "".join(parts).strip()


def complete_with_images(
    system: str,
    user_text: str,
    images: list[bytes],
    max_tokens: int = 4096,
    temperature: float = 0.1,
    model: str | None = None,
) -> str:
    """Claude Messages API 의 이미지 블록을 사용해 비전 완성을 요청한다.

    이미지는 메모리에서 base64 인코딩하며 디스크에 저장하지 않는다 (security).
    이미지·입력 내용을 로그·예외 메시지에 노출하지 않는다 (security).

    Args:
        system: 시스템 프롬프트
        user_text: 이미지와 함께 전달할 텍스트 지시문
        images: PNG 바이트 리스트 (페이지별)
        max_tokens: 생성 토큰 상한
        temperature: 샘플링 온도
        model: 모델 ID (None 이면 settings.LLM_MODEL)

    Returns:
        응답 텍스트 (strip 적용).

    Raises:
        RuntimeError: 호출 실패 (키/입력은 메시지에 노출하지 않음).
    """
    client = _get_client()
    content: list[dict] = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": base64.b64encode(img).decode(),
            },
        }
        for img in images
    ]
    content.append({"type": "text", "text": user_text})

    try:
        resp = client.messages.create(
            model=model or LLM_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": content}],
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"LLM 비전 호출 실패: {type(exc).__name__}") from exc

    parts: list[str] = []
    for block in resp.content:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "".join(parts).strip()
