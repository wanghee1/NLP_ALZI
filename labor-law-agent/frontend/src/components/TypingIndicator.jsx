import { useState, useEffect } from 'react'

const STAGES = {
  chat: [
    '질문을 분석하고 있어요',
    '관련 법령을 찾고 있어요',
    '쉽게 정리하고 있어요',
  ],
  collecting: [
    '입력을 확인하고 있어요',
  ],
  document: [
    '진정서를 작성하고 있어요',
    '문서를 준비하고 있어요',
  ],
  contract: [
    '계약서를 읽고 있어요',
    '위험 조항을 분석하고 있어요',
    '개선 방법을 정리하고 있어요',
  ],
  'contract-vision': [
    '계약서를 읽고 있어요',
    '이미지를 인식하고 있어요',
    '텍스트를 추출하고 있어요',
    '위험 조항을 분석하고 있어요',
  ],
}

// 타입별 스테이지 전환 타이밍 (누적 ms)
const ADVANCE_AT = {
  chat: [1300, 2900],
  collecting: [],
  document: [2000],
  contract: [1300, 2900],
  'contract-vision': [1500, 4500, 8000],
}

function useStage(type) {
  const [idx, setIdx] = useState(0)

  useEffect(() => {
    setIdx(0)
    const delays = ADVANCE_AT[type] ?? ADVANCE_AT.chat
    const timers = delays.map((ms, i) => setTimeout(() => setIdx(i + 1), ms))
    return () => timers.forEach(clearTimeout)
  }, [type])

  const list = STAGES[type] ?? STAGES.chat
  return list[Math.min(idx, list.length - 1)]
}

/**
 * @param {{ type?: 'chat' | 'collecting' | 'document' | 'contract' }} props
 */
export default function TypingIndicator({ type = 'chat' }) {
  const stage = useStage(type)

  return (
    <div className="alzi-row alzi-row--bot">
      <div className="alzi-avatar" aria-hidden="true">A</div>
      <div
        className="alzi-typing-bubble"
        role="status"
        aria-live="polite"
        aria-label={stage}
      >
        <span className="alzi-typing-dots-inline" aria-hidden="true">
          <span className="alzi-typing-dot" />
          <span className="alzi-typing-dot" />
          <span className="alzi-typing-dot" />
        </span>
        <span key={stage} className="alzi-typing-stage">{stage}</span>
      </div>
    </div>
  )
}
