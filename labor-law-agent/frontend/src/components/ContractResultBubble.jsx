import ViolationCard from './ViolationCard.jsx'

const CONTRACT_NOTICE =
  '본 분석은 AI가 일반적인 노동법 기준에 따라 검토한 참고 결과이며, 실제 위법 여부는 ' +
  '계약 전체의 맥락과 개별 사정에 따라 달라질 수 있습니다. 법적 효력이 있는 판단이 ' +
  '아니므로, 정확한 검토는 전문가에게 받으시기 바랍니다.'

/**
 * @param {{ analyzed: boolean, violations: Array, content: string, used_vision: boolean }} props
 */
export default function ContractResultBubble({ analyzed, violations, content, used_vision = false }) {
  const high = violations.filter(v => v.severity === '높음').length
  const mid = violations.filter(v => v.severity === '중간').length
  const low = violations.filter(v => v.severity === '낮음').length

  return (
    <div className="alzi-row alzi-row--bot">
      <div className="alzi-avatar" aria-hidden="true">A</div>
      <div className="alzi-bubble alzi-bubble--bot alzi-bubble--contract">
        {used_vision && (
          <p className="alzi-vision-badge">이미지 인식(OCR)으로 분석했어요</p>
        )}
        {analyzed && violations.length > 0 ? (
          <>
            <p className="alzi-contract-summary">
              계약서 분석 완료 —
              {high > 0 && <span className="alzi-contract-count alzi-contract-count--높음"> 높음 {high}건</span>}
              {mid > 0 && <span className="alzi-contract-count alzi-contract-count--중간"> 중간 {mid}건</span>}
              {low > 0 && <span className="alzi-contract-count alzi-contract-count--낮음"> 낮음 {low}건</span>}
            </p>
            <div className="alzi-v-list">
              {violations.map((v, i) => (
                <ViolationCard key={i} violation={v} />
              ))}
            </div>
          </>
        ) : (
          <p className="alzi-consultation-text">
            {content || (analyzed ? '특이사항이 발견되지 않았어요.' : '계약서를 분석하지 못했어요. 다시 시도해 주세요.')}
          </p>
        )}
        {analyzed && (
          <p className="alzi-contract-notice">{CONTRACT_NOTICE}</p>
        )}
      </div>
    </div>
  )
}
