import { useEffect, useRef } from 'react'
import UserBubble from './UserBubble.jsx'
import BotMessage from './BotMessage.jsx'
import TypingIndicator from './TypingIndicator.jsx'

/**
 * @param {{ messages: Array, isLoading: boolean, loadingType: string,
 *           onSend: (text: string, docType?: string) => void,
 *           onDocTypeSelect: (type: string) => void,
 *           onCancel: () => void }} props
 */
export default function MessageList({
  messages,
  isLoading,
  loadingType = 'chat',
  onSend,
  onDocTypeSelect,
  onCancel,
}) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  return (
    <div className="alzi-message-list" role="log" aria-live="polite" aria-label="대화 내용">
      {messages.map(msg =>
        msg.role === 'user'
          ? <UserBubble key={msg.id} content={msg.content} />
          : (
            <BotMessage
              key={msg.id}
              msg={msg}
              onSend={onSend}
              onDocTypeSelect={onDocTypeSelect}
              onCancel={onCancel}
            />
          )
      )}
      {isLoading && <TypingIndicator type={loadingType} />}
      <div ref={bottomRef} aria-hidden="true" />
    </div>
  )
}
