import { useState } from 'react'
import { useChat } from '../hooks/useChat.js'
import MessageBubble from './MessageBubble.jsx'
import FileUploader from './FileUploader.jsx'
import ChoiceButtons from './ChoiceButtons.jsx'

/**
 * 채팅 인터페이스 최상위 컴포넌트.
 * 메시지 목록, 입력창, 파일 업로더, 문서 제안 버튼을 조합한다.
 */
export default function ChatWindow() {
  const { messages, isLoading, suggestDocument, suggestedDocType, sendMessage } = useChat()
  const [input, setInput] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!input.trim()) return
    sendMessage(input.trim())
    setInput('')
  }

  return (
    <div>
      {/* 메시지 목록 */}
      <div style={{ minHeight: '400px', overflowY: 'auto', padding: '1rem', border: '1px solid #ddd' }}>
        {messages.map((msg, i) => (
          <MessageBubble key={i} role={msg.role} content={msg.content} />
        ))}
        {isLoading && <p>분석 중...</p>}
      </div>

      {/* 문서 작성 제안 */}
      {suggestDocument && (
        <ChoiceButtons
          docType={suggestedDocType}
          onConfirm={() => { /* TODO: document generate 흐름 시작 */ }}
          onDeny={() => { /* TODO: 제안 숨김 */ }}
        />
      )}

      {/* 계약서 업로드 */}
      <FileUploader onUpload={(file) => { /* TODO: analyzeContract 호출 */ }} />

      {/* 텍스트 입력 */}
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="노동법 관련 질문을 입력하세요..."
          style={{ flex: 1, padding: '0.5rem' }}
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading || !input.trim()}>전송</button>
      </form>
    </div>
  )
}
