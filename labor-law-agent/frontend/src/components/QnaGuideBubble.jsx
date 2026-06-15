const GUIDE_TEXT =
  '안녕하세요! 노동법 관련 궁금한 점을 편하게 물어보세요 😊\n' +
  '상황을 구체적으로 적어주실수록 더 정확하게 안내해드릴 수 있어요.\n' +
  '필요하면 진정서·내용증명 작성도 도와드릴게요.'

const GUIDE_CHIPS = [
  '주 20시간 일했는데 주휴수당 받을 수 있어?',
  '갑자기 그만두라고 했는데 어떻게 해야 해?',
  '시급 9천원인데 최저임금 위반이야?',
]

/**
 * 노동법 Q&A 진입 시 1회 표시되는 활용 가이드 버블.
 * 예시 질문 칩을 클릭하면 바로 전송된다.
 *
 * @param {{ onSend: (text: string) => void }} props
 */
export default function QnaGuideBubble({ onSend }) {
  return (
    <div className="alzi-row alzi-row--bot">
      <div className="alzi-avatar" aria-hidden="true">A</div>
      <div className="alzi-bubble alzi-bubble--bot alzi-bubble--qna-guide">
        <p className="alzi-simple-text">{GUIDE_TEXT}</p>
        <div className="alzi-guide-chips">
          {GUIDE_CHIPS.map(chip => (
            <button
              key={chip}
              className="alzi-guide-chip"
              type="button"
              onClick={() => onSend(chip)}
            >
              {chip}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
