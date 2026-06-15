import { useState, useRef, useCallback, useEffect } from 'react'

function formatBytes(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

/**
 * @param {{
 *   placeholder: string,
 *   isLoading: boolean,
 *   onSend: (text: string) => void,
 *   onContractFile: (file: File) => void,
 *   focusSignal?: number
 * }} props
 */
export default function InputArea({ placeholder, isLoading, onSend, onContractFile, focusSignal = 0 }) {
  const [text, setText] = useState('')
  const [pendingFile, setPendingFile] = useState(null)
  const [fileError, setFileError] = useState(null)
  const fileRef = useRef(null)
  const textareaRef = useRef(null)

  // 로딩 완료 시 포커스 복원 — disabled 해제 직후 textarea에 다시 포커스
  useEffect(() => {
    if (!isLoading) {
      textareaRef.current?.focus()
    }
  }, [isLoading])

  // 외부 focusSignal 변경 시 textarea 포커스 (Q&A 카드 클릭 등 수동 전환)
  useEffect(() => {
    if (focusSignal > 0) textareaRef.current?.focus()
  }, [focusSignal])

  const handleSend = useCallback(() => {
    const trimmed = text.trim()
    if (!trimmed || isLoading) return
    onSend(trimmed)
    setText('')
    textareaRef.current?.focus()
  }, [text, isLoading, onSend])

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }, [handleSend])

  const handleFileChange = useCallback((e) => {
    const file = e.target.files?.[0]
    e.target.value = ''  // 같은 파일 재선택 허용
    if (!file) return

    // 선택 시점 검증 — 잘못된 파일이면 분석하기 누르기 전에 바로 안내
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setFileError('PDF 파일만 올릴 수 있어요.')
      setPendingFile(null)
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      setFileError('10MB 이하 파일만 분석할 수 있어요.')
      setPendingFile(null)
      return
    }

    setFileError(null)
    setPendingFile(file)
  }, [])

  const handleAnalyze = useCallback(() => {
    if (!pendingFile || isLoading) return
    const file = pendingFile
    setPendingFile(null)
    setFileError(null)
    onContractFile(file)
  }, [pendingFile, isLoading, onContractFile])

  const handleCancelFile = useCallback(() => {
    setPendingFile(null)
    setFileError(null)
    if (fileRef.current) fileRef.current.value = ''
  }, [])

  const showPreview = pendingFile !== null || fileError !== null

  return (
    <div className="alzi-input-area">
      {showPreview && (
        <div className={`alzi-file-preview${fileError ? ' alzi-file-preview--error' : ''}`}>
          <span className="alzi-file-preview__icon" aria-hidden="true">📄</span>
          {fileError ? (
            <span className="alzi-file-preview__error">{fileError}</span>
          ) : (
            <>
              <span className="alzi-file-preview__name">{pendingFile.name}</span>
              <span className="alzi-file-preview__size">{formatBytes(pendingFile.size)}</span>
            </>
          )}
          <div className="alzi-file-preview__actions">
            <button
              className="alzi-file-cancel-btn"
              type="button"
              onClick={handleCancelFile}
            >
              {fileError ? '닫기' : '취소'}
            </button>
            {!fileError && (
              <button
                className="alzi-file-analyze-btn"
                type="button"
                disabled={isLoading}
                onClick={handleAnalyze}
              >
                {isLoading ? '분석 중…' : '분석하기'}
              </button>
            )}
          </div>
        </div>
      )}
      <div className="alzi-input-row">
        <button
          className="alzi-attach-btn"
          type="button"
          aria-label="계약서 PDF 업로드"
          title="계약서 PDF 분석"
          disabled={isLoading}
          onClick={() => fileRef.current?.click()}
        >
          📎
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".pdf,application/pdf"
          className="alzi-file-input"
          aria-hidden="true"
          tabIndex={-1}
          onChange={handleFileChange}
        />
        <textarea
          ref={textareaRef}
          className="alzi-textarea"
          rows={1}
          value={text}
          placeholder={placeholder}
          disabled={isLoading}
          aria-label="메시지 입력"
          onChange={e => setText(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button
          className="alzi-send-btn"
          type="button"
          aria-label="전송"
          disabled={!text.trim() || isLoading}
          onClick={handleSend}
        >
          ↑
        </button>
      </div>
    </div>
  )
}
