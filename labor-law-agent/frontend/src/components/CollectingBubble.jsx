/**
 * 진정서 정보 수집 중 봇 메시지.
 * choices 가 있으면 입력창 대신 선택 버튼을 표시한다.
 *
 * @param {{ content: string, choices?: string[], onSend: (text: string) => void }} props
 */
export default function CollectingBubble({ content, choices = [], onSend }) {
  return (
    <div className="alzi-row alzi-row--bot">
      <div className="alzi-avatar" aria-hidden="true">A</div>
      <div className="alzi-bubble alzi-bubble--bot alzi-bubble--collecting">
        <p className="alzi-collecting-text">{content}</p>
        {choices.length > 0 && (
          <div className="alzi-choice-row alzi-choice-row--inline" role="group" aria-label="선택지">
            {choices.map(c => (
              <button
                key={c}
                className="alzi-choice-btn alzi-choice-btn--option"
                type="button"
                onClick={() => onSend(c)}
              >
                {c}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
