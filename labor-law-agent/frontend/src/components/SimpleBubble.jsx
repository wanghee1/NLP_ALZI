/**
 * 일반 봇 텍스트 응답
 * @param {{ content: string }} props
 */
export default function SimpleBubble({ content }) {
  return (
    <div className="alzi-row alzi-row--bot">
      <div className="alzi-avatar" aria-hidden="true">A</div>
      <div className="alzi-bubble alzi-bubble--bot">
        <p className="alzi-simple-text">{content}</p>
      </div>
    </div>
  )
}
