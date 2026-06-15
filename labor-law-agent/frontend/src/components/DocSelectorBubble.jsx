const DOC_OPTIONS = [
  {
    type: 'wage_complaint',
    icon: '📋',
    label: '임금체불 진정서',
    desc: '못 받은 임금을 노동청에 신고',
  },
  {
    type: 'unfair_dismissal',
    icon: '⚖️',
    label: '부당해고 구제신청서',
    desc: '부당하게 해고됐을 때 노동위원회에 신청',
  },
  {
    type: 'payment_demand',
    icon: '✉️',
    label: '내용증명',
    desc: '진정 전, 사장님께 공식 지급 요청 기록',
  },
]

/**
 * @param {{ onDocTypeSelect: (type: string) => void }} props
 */
export default function DocSelectorBubble({ onDocTypeSelect }) {
  return (
    <div className="alzi-row alzi-row--bot">
      <div className="alzi-avatar" aria-hidden="true">A</div>
      <div className="alzi-bubble alzi-bubble--bot alzi-bubble--doc-selector">
        <p className="alzi-doc-selector-title">어떤 문서를 만들어 드릴까요?</p>
        <div className="alzi-doc-selector-list" role="group" aria-label="문서 선택">
          {DOC_OPTIONS.map(opt => (
            <button
              key={opt.type}
              className="alzi-doc-option-btn"
              type="button"
              onClick={() => onDocTypeSelect(opt.type)}
            >
              <span className="alzi-doc-option-icon" aria-hidden="true">{opt.icon}</span>
              <span className="alzi-doc-option-text">
                <span className="alzi-doc-option-label">{opt.label}</span>
                <span className="alzi-doc-option-desc">{opt.desc}</span>
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
