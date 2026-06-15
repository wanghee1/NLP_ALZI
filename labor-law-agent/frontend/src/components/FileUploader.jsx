/**
 * 계약서 PDF 파일 업로드 컴포넌트.
 *
 * Props:
 *   onUpload {(file: File) => void} - 파일 선택 시 호출되는 콜백
 *   accept   {string}               - 허용 MIME 타입 (기본값: 'application/pdf')
 *   disabled {boolean}              - 비활성화 여부
 */
export default function FileUploader({ onUpload, accept = 'application/pdf', disabled = false }) {
  const handleChange = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    // TODO: 파일 크기 검증 (20 MB 이하)
    // TODO: MIME 타입 검증
    onUpload(file)
    e.target.value = ''  // 같은 파일 재선택 허용
  }

  return (
    <div style={{ marginTop: '0.5rem' }}>
      <label style={{ cursor: disabled ? 'not-allowed' : 'pointer', color: '#555', fontSize: '0.875rem' }}>
        📎 계약서 PDF 업로드
        <input
          type="file"
          accept={accept}
          onChange={handleChange}
          disabled={disabled}
          style={{ display: 'none' }}
        />
      </label>
      {/* TODO: 업로드 진행 상태 표시 */}
      {/* TODO: 분석 결과(위반 조항)를 모달 또는 사이드패널로 표시 */}
    </div>
  )
}
