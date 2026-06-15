/**
 * 단일 채팅 메시지 말풍선 컴포넌트.
 *
 * Props:
 *   role {string}   - 'user' | 'assistant'
 *   content {string} - 메시지 텍스트 (마크다운 지원 예정)
 */
export default function MessageBubble({ role, content }) {
  const isUser = role === 'user'

  // TODO: 마크다운 렌더링 (react-markdown 도입 예정)
  // TODO: 법령 인용 하이라이트 처리
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: '0.75rem',
      }}
    >
      <div
        style={{
          maxWidth: '70%',
          padding: '0.5rem 0.75rem',
          borderRadius: '12px',
          background: isUser ? '#0084ff' : '#f0f0f0',
          color: isUser ? '#fff' : '#000',
          whiteSpace: 'pre-wrap',
        }}
      >
        {content}
      </div>
    </div>
  )
}
