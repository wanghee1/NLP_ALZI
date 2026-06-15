const SEVERITY_LABEL = { 높음: '높음', 중간: '중간', 낮음: '낮음' }
const TYPE_LABEL = { 위법: '위법', 불리: '불리한 조항', 누락: '누락' }

/**
 * @param {{ violation: {type:string, clause:string, issue:string, law_hint:string, severity:string, suggestion:string} }} props
 */
export default function ViolationCard({ violation }) {
  const { type, clause, issue, law_hint, severity, suggestion } = violation

  return (
    <div className={`alzi-v-card alzi-v-card--${severity ?? '낮음'}`}>
      <div className="alzi-v-card-header">
        <span className={`alzi-severity-badge alzi-severity-badge--${severity}`}>
          {SEVERITY_LABEL[severity] ?? severity}
        </span>
        <span className={`alzi-type-badge alzi-type-badge--${type}`}>
          {TYPE_LABEL[type] ?? type}
        </span>
        <span className="alzi-v-clause">{clause}</span>
      </div>
      <p className="alzi-v-issue">{issue}</p>
      {law_hint && <p className="alzi-v-law-hint">📎 {law_hint}</p>}
      {suggestion && (
        <div className="alzi-suggestion-box">
          <span className="alzi-suggestion-label">개선 제안</span>
          <p className="alzi-suggestion-text">{suggestion}</p>
        </div>
      )}
    </div>
  )
}
