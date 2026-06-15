/**
 * @param {{ content: string }} props
 */
export default function UserBubble({ content }) {
  return (
    <div className="alzi-row alzi-row--user">
      <div className="alzi-bubble alzi-bubble--user">{content}</div>
    </div>
  )
}
