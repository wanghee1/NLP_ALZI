/**
 * 진정서 최종 확인 단계 봇 메시지
 * @param {{ content: string, onConfirm: () => void, onEdit: () => void }} props
 */
export default function ConfirmingBubble({ content, onConfirm, onEdit }) {
  return (
    <div className="alzi-row alzi-row--bot">
      <div className="alzi-avatar" aria-hidden="true">A</div>
      <div className="alzi-bubble alzi-bubble--bot alzi-bubble--confirming">
        <p className="alzi-collecting-text">{content}</p>
        <div className="alzi-choice-row">
          <button className="alzi-choice-btn alzi-choice-btn--primary" type="button" onClick={onConfirm}>
            맞아요
          </button>
          <button className="alzi-choice-btn alzi-choice-btn--secondary" type="button" onClick={onEdit}>
            고칠래요
          </button>
        </div>
      </div>
    </div>
  )
}
