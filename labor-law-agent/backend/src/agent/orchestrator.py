"""에이전트 오케스트레이터.

RAG 체인과 LLM을 조합하여 사용자 메시지에 대한 최종 답변을 생성한다.
문서 작성 의도를 감지하여 suggest_document 플래그를 설정한다.
"""

from __future__ import annotations

from typing import Any


async def run_chat(
    message: str,
    history: list[dict[str, str]],
    session_id: str,
) -> dict[str, Any]:
    """RAG 기반 노동법 Q&A를 수행하고 결과를 반환한다.

    Args:
        message: 사용자 입력 텍스트
        history: 이전 대화 [{role, content}, ...]
        session_id: 현재 세션 ID

    Returns:
        {answer, suggest_document, suggested_doc_type, sources}
    """
    # TODO: rag.retriever.retrieve(message) 로 관련 문서 청크 가져오기
    # TODO: prompts.build_system_prompt() + history로 메시지 구성
    # TODO: LLM 호출 (langchain_openai.ChatOpenAI)
    # TODO: 답변 텍스트에서 문서 제안 키워드 감지
    raise NotImplementedError
