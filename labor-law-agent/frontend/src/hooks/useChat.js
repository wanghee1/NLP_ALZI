import { useState, useCallback } from 'react'
import { sendChat, analyzeContract } from '../api/client.js'

/** 메시지 kind 결정 — ChatResponse 의 필드 조합으로 판별 */
function resolveKind(res) {
  if (res.doc_ready) return 'download'
  if (res.mode === 'confirming') return 'confirming'
  // "editing" = 고칠래요 → 항목 선택 대기; confirm 버튼 없이 collecting 버블로 표시
  if (res.mode === 'collecting' || res.mode === 'onboarding' || res.mode === 'editing') return 'collecting'
  if (res.legal_grounds && res.legal_grounds.length > 0) return 'consultation'
  return 'simple'
}

function makeId() {
  return Math.random().toString(36).slice(2)
}

const DOC_TYPE_LABELS = {
  wage_complaint: '임금체불 진정서',
  unfair_dismissal: '부당해고 구제신청서',
  payment_demand: '내용증명',
}

// collector.py _CONFIRM 과 동기화 — 확인 응답 감지 (문서 생성 로딩 타입 결정용)
const _CONFIRM_RE = /^(맞아요|맞아|네|예|확인|좋아요|응|ok|오케이)$/i

function resolveLoadingType(currentMode, text) {
  if (currentMode === 'confirming') {
    return _CONFIRM_RE.test(text.trim()) ? 'document' : 'collecting'
  }
  if (currentMode === 'collecting' || currentMode === 'editing') return 'collecting'
  return 'chat'
}

export function useChat() {
  const [sessionId, setSessionId] = useState(() => crypto.randomUUID())
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [loadingType, setLoadingType] = useState('chat')
  const [placeholder, setPlaceholder] = useState('노동법 질문을 입력하세요...')
  // 마지막 API 응답의 backend mode 를 추적 — 다음 요청의 loadingType 결정에 사용
  const [currentMode, setCurrentMode] = useState('chat')

  const addMsg = useCallback((msg) => {
    setMessages(prev => [...prev, { id: makeId(), ...msg }])
  }, [])

  /** API 없이 Q&A 활용 가이드(QnaGuideBubble)를 채팅창에 표시 — 카드 클릭 시 1회 */
  const startQnaGuide = useCallback(() => {
    addMsg({ role: 'bot', kind: 'qna-guide', content: '' })
  }, [addMsg])

  /** API 없이 문서 선택 화면(DocSelectorBubble)을 채팅창에 표시 */
  const showDocSelector = useCallback(() => {
    addMsg({ role: 'bot', kind: 'doc_selector', content: '' })
  }, [addMsg])

  /** API 없이 선택된 문서 유형의 안내(GuidanceBubble)를 채팅창에 표시 */
  const selectDocType = useCallback((docType) => {
    addMsg({ role: 'user', kind: 'simple', content: DOC_TYPE_LABELS[docType] ?? docType })
    addMsg({ role: 'bot', kind: 'guidance', content: '', doc_type: docType })
  }, [addMsg])

  /** API 없이 안내 취소 메시지를 로컬에 추가 */
  const cancelDocFlow = useCallback(() => {
    addMsg({ role: 'user', kind: 'simple', content: '취소' })
    addMsg({ role: 'bot', kind: 'simple', content: '알겠어요! 다른 궁금한 점이 있으면 언제든 말씀해 주세요.' })
  }, [addMsg])

  /**
   * @param {string} text
   * @param {string|null} docType - 문서 선택 후 [시작하기] 클릭 시에만 전달
   */
  const sendMessage = useCallback(async (text, docType = null) => {
    const trimmed = text.trim()
    if (!trimmed || isLoading) return

    addMsg({ role: 'user', kind: 'simple', content: trimmed })
    // docType 전달(시작하기) 시에는 수집 시작 → collecting 타입
    const loadType = docType ? 'collecting' : resolveLoadingType(currentMode, trimmed)
    setLoadingType(loadType)
    setIsLoading(true)

    try {
      const res = await sendChat(sessionId, trimmed, docType)
      const kind = resolveKind(res)
      const resMode = res.mode ?? 'chat'

      addMsg({
        role: 'bot',
        kind,
        content: res.reply,
        legal_grounds: res.legal_grounds ?? [],
        sources: res.sources ?? [],
        mode: resMode,
        doc_ready: res.doc_ready ?? false,
        download_url: res.download_url ?? null,
        choices: res.choices ?? [],
        suggest_document: res.suggest_document ?? false,
        document_type: res.document_type ?? null,
      })

      setCurrentMode(resMode)

      if (kind === 'collecting') setPlaceholder('답변을 입력하세요...')
      else if (kind === 'confirming') setPlaceholder('"맞아요" 또는 "고칠래요" 로 답해주세요')
      else setPlaceholder('노동법 질문을 입력하세요...')
    } catch {
      addMsg({ role: 'bot', kind: 'simple', content: '잠시 문제가 생겼어요. 다시 시도해 주세요.' })
    } finally {
      setIsLoading(false)
    }
  }, [sessionId, isLoading, currentMode, addMsg])

  const sendContractFile = useCallback(async (file) => {
    if (isLoading) return

    if (file.size > 10 * 1024 * 1024) {
      addMsg({ role: 'bot', kind: 'simple', content: '10MB 이하 파일만 분석할 수 있어요.' })
      return
    }
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      addMsg({ role: 'bot', kind: 'simple', content: 'PDF 파일만 올릴 수 있어요.' })
      return
    }

    addMsg({ role: 'user', kind: 'simple', content: `📎 ${file.name}` })
    setLoadingType('contract')
    setIsLoading(true)

    // 4초 후 비전 경로 로딩 메시지로 전환 (이미지 PDF 인식 중일 때 UX)
    const visionTimer = setTimeout(() => setLoadingType('contract-vision'), 4000)

    try {
      const res = await analyzeContract(file)
      addMsg({
        role: 'bot',
        kind: 'contract',
        analyzed: res.analyzed,
        violations: res.violations ?? [],
        content: res.message ?? '',
        used_vision: res.used_vision ?? false,
      })
    } catch (err) {
      addMsg({ role: 'bot', kind: 'simple', content: err.message || '계약서 분석 중 문제가 생겼어요. 다시 시도해 주세요.' })
    } finally {
      clearTimeout(visionTimer)
      setIsLoading(false)
    }
  }, [isLoading, addMsg])

  const resetChat = useCallback(() => {
    setMessages([])
    setIsLoading(false)
    setLoadingType('chat')
    setCurrentMode('chat')
    setPlaceholder('노동법 질문을 입력하세요...')
    setSessionId(crypto.randomUUID())
  }, [])

  return {
    messages,
    sessionId,
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
  }
}
