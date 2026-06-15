/**
 * 문서 작성 제안에 대한 사용자 선택 버튼 컴포넌트.
 * AI가 문서 작성을 제안할 때 채팅창 하단에 표시된다.
 *
 * Props:
 *   docType   {string}     - 제안된 문서 유형 (예: 'notice_of_claim')
 *   onConfirm {() => void} - "네, 작성해주세요" 클릭 시 콜백
 *   onDeny    {() => void} - "아니요" 클릭 시 콜백
 */
export default function ChoiceButtons({ docType, onConfirm, onDeny }) {
  const docTypeLabel = {
    notice_of_claim: '내용증명',
    complaint: '진정서',
    standard_contract: '표준근로계약서',
  }[docType] ?? '문서'

  return (
    <div style={{ padding: '0.75rem', background: '#fffbe6', borderRadius: '8px', marginTop: '0.5rem' }}>
      <p style={{ margin: '0 0 0.5rem' }}>
        {docTypeLabel} 작성을 도와드릴까요?
      </p>
      <div style={{ display: 'flex', gap: '0.5rem' }}>
        <button
          onClick={onConfirm}
          style={{ padding: '0.4rem 1rem', background: '#0084ff', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
        >
          네, 작성해주세요
        </button>
        <button
          onClick={onDeny}
          style={{ padding: '0.4rem 1rem', background: '#eee', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
        >
          아니요
        </button>
      </div>
    </div>
  )
}
