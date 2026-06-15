/**
 * 백엔드 REST API 호출 래퍼.
 * 모든 백엔드 통신은 이 파일을 통해서만 한다 (컴포넌트에서 직접 fetch 금지).
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

/** 상대 경로를 절대 URL로 변환 (doc_ready 다운로드 링크 등) */
export function resolveUrl(path) {
  if (!path) return null
  if (path.startsWith('http')) return path
  return `${BASE_URL}${path}`
}

/**
 * POST /chat — 노동법 Q&A
 * @param {string} sessionId
 * @param {string} message
 * @param {string|null} docType - 문서 선택 화면에서 명시적으로 전달할 때만 설정
 */
export async function sendChat(sessionId, message, docType = null) {
  const body = { session_id: sessionId, message }
  if (docType) body.doc_type = docType
  const res = await fetch(`${BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`서버 오류 (${res.status})`)
  return res.json()
}

/**
 * POST /contract/analyze — 계약서 PDF 위험 조항 탐지
 * @param {File} file - PDF 파일
 */
export async function analyzeContract(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE_URL}/contract/analyze`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? `서버 오류 (${res.status})`)
  }
  return res.json()
}
