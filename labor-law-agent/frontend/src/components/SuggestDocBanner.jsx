/** wage_complaint 일 때 관련 문서 2개, 나머지는 1개 */
const SUGGEST_BUTTONS = {
  wage_complaint: [
    { type: 'wage_complaint',   label: '📋 임금체불 진정서 작성' },
    { type: 'payment_demand',   label: '✉️ 내용증명 작성' },
  ],
  unfair_dismissal: [
    { type: 'unfair_dismissal', label: '⚖️ 구제신청서 작성' },
  ],
  payment_demand: [
    { type: 'payment_demand',   label: '✉️ 내용증명 작성' },
    { type: 'wage_complaint',   label: '📋 임금체불 진정서 작성' },
  ],
}

const SUGGEST_TEXT = {
  wage_complaint:    '진정서나 내용증명 작성을 도와드릴 수 있어요.',
  unfair_dismissal:  '부당해고 구제신청서 작성을 도와드릴 수 있어요. (해고일로부터 3개월 이내, 5인 이상 사업장)',
  payment_demand:    '내용증명 작성을 도와드릴 수 있어요.',
}

/**
 * @param {{ document_type: string, onDocTypeSelect: (type: string) => void }} props
 */
export default function SuggestDocBanner({ document_type, onDocTypeSelect }) {
  const buttons = SUGGEST_BUTTONS[document_type] ?? []
  if (!buttons.length) return null

  return (
    <div className="alzi-suggest-banner">
      <p className="alzi-suggest-text">{SUGGEST_TEXT[document_type] ?? '문서 작성을 도와드릴 수 있어요.'}</p>
      <div className="alzi-suggest-btns">
        {buttons.map(b => (
          <button
            key={b.type}
            className="alzi-suggest-btn"
            type="button"
            onClick={() => onDocTypeSelect(b.type)}
          >
            {b.label}
          </button>
        ))}
      </div>
    </div>
  )
}
