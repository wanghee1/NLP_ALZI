import { useCallback, useState } from 'react'
import { useChat } from './hooks/useChat.js'
import Header from './components/Header.jsx'
import EmptyState from './components/EmptyState.jsx'
import MessageList from './components/MessageList.jsx'
import InputArea from './components/InputArea.jsx'

export default function App() {
  const {
    messages,
    isLoading,
    loadingType,
    placeholder,
    sendMessage,
    sendContractFile,
    resetChat,
    startQnaGuide,
    showDocSelector,
    selectDocType,
    cancelDocFlow,
  } = useChat()

  // focusSignal 증가 시 InputArea 의 textarea 에 포커스를 부여한다
  const [focusSignal, setFocusSignal] = useState(0)

  const handleContractClick = useCallback(() => {
    document.querySelector('.alzi-file-input')?.click()
  }, [])

  const handleQnaClick = useCallback(() => {
    startQnaGuide()
    setFocusSignal(s => s + 1)
  }, [startQnaGuide])

  const isEmpty = messages.length === 0

  return (
    <div className="alzi-app">
      <Header onReset={resetChat} />

      <main className="alzi-main">
        {isEmpty ? (
          <EmptyState
            onSend={sendMessage}
            onContractClick={handleContractClick}
            onDocSelect={showDocSelector}
            onQnaClick={handleQnaClick}
          />
        ) : (
          <MessageList
            messages={messages}
            isLoading={isLoading}
            loadingType={loadingType}
            onSend={sendMessage}
            onDocTypeSelect={selectDocType}
            onCancel={cancelDocFlow}
          />
        )}
      </main>

      <footer className="alzi-footer">
        <InputArea
          placeholder={placeholder}
          isLoading={isLoading}
          onSend={sendMessage}
          onContractFile={sendContractFile}
          focusSignal={focusSignal}
        />
        <p className="alzi-disclaimer">
          본 서비스는 노동 관련 법령 정보를 안내하기 위한 것으로, 법률 자문에 해당하지 아니합니다.
          제공되는 답변은 참고 목적의 일반적 정보이며 법적 효력을 가지지 않습니다.
          구체적 사안에 대하여는 고용노동부(국번 없이 1350) 또는 노무사·변호사 등 전문가의 상담을 권고드립니다.
        </p>
      </footer>
    </div>
  )
}
