"""chain.answer() 답변 품질 검증 스크립트 (일회성).

대표 질문 4개를 answer() 에 넣고 found/sources/reply 를 사람이 한눈에 검증한다.
런타임 경로(api/)에 넣지 않는다.

확인 포인트: found 판정, 출처(조문표기) 정확성, 원문이 코드로 삽입됐는지,
LLM 이 풀이만 쓰고 조문번호를 지어내지 않았는지, 고지 문구가 붙는지.

실행:
    cd backend
    python -m src.rag.chain_check

사전 준비: build_index.py 로 적재 완료 + backend/.env 에 OPENAI_API_KEY 설정.
"""

from __future__ import annotations

import sys

from src.rag.chain import answer

TEST_QUERIES = [
    "주휴수당을 못 받았어요",
    "사장이 갑자기 해고했어요",
    "최저임금은 얼마인가요",
    "월급을 14일 넘게 안 줘요",
]


def main() -> int:
    for i, question in enumerate(TEST_QUERIES, start=1):
        print("=" * 76)
        print(f"[{i}/{len(TEST_QUERIES)}] 질문: {question}")
        print("-" * 76)
        try:
            result = answer(question)
        except RuntimeError as exc:
            print(f"  [실패] {exc}")
            print()
            continue

        print(f"found  : {result['found']}")
        print(f"sources: {result['sources']}")
        print("reply  :")
        # reply 안의 \n 이 실제 줄바꿈으로 보이도록 그대로 print 한다.
        print(result["reply"])
        print()

    print("=" * 76)
    print("[검증 종료] 각 답변의 found/출처/원문 삽입/풀이/고지 문구를 눈으로 확인하라.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
