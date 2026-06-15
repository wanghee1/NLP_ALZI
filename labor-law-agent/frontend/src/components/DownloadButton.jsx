import { getDownloadUrl } from '../api/client.js'

/**
 * 생성된 PDF 문서 다운로드 버튼 컴포넌트.
 *
 * Props:
 *   docId    {string}  - 백엔드에서 반환한 문서 식별자
 *   docType  {string}  - 문서 유형 (파일명에 사용)
 *   disabled {boolean} - 비활성화 여부 (생성 중일 때)
 */
export default function DownloadButton({ docId, docType = 'document', disabled = false }) {
  const handleDownload = () => {
    // TODO: 직접 링크 대신 Blob으로 받아 저장하는 방식으로 변경 가능
    const url = getDownloadUrl(docId)
    const a = document.createElement('a')
    a.href = url
    a.download = `${docType}_${docId}.pdf`
    a.click()
  }

  return (
    <button
      onClick={handleDownload}
      disabled={disabled || !docId}
      style={{
        padding: '0.5rem 1rem',
        background: disabled ? '#ccc' : '#28a745',
        color: '#fff',
        border: 'none',
        borderRadius: '6px',
        cursor: disabled ? 'not-allowed' : 'pointer',
        marginTop: '0.5rem',
      }}
    >
      PDF 다운로드
    </button>
  )
}
