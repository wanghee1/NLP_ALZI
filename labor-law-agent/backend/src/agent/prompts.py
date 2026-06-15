"""시스템·사용자 프롬프트 템플릿 정의.

LangChain ChatPromptTemplate 형식으로 관리한다.
"""

from __future__ import annotations


SYSTEM_PROMPT = """당신은 대한민국 노동법 전문 AI 어시스턴트입니다.
근로기준법, 최저임금법, 기간제법 등을 기반으로 정확하고 친절하게 답변하세요.
법령 조문을 인용할 때는 반드시 조문 번호를 명시하세요.
법적 조언이 필요한 경우 전문 노무사·변호사 상담을 권유하세요.

[참고 문서]
{context}
"""


def build_system_prompt(context: str) -> str:
    """검색된 컨텍스트를 삽입한 시스템 프롬프트를 반환한다."""
    # TODO: 문서 청크를 포맷하여 context 문자열 생성
    return SYSTEM_PROMPT.format(context=context)


def build_document_suggestion_prompt(answer: str) -> str:
    """답변에서 문서 작성 필요 여부를 판단하는 분류 프롬프트를 반환한다."""
    # TODO: few-shot 예시 추가하여 정확도 개선
    raise NotImplementedError
