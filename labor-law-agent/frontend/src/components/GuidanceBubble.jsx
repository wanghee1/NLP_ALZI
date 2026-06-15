const GUIDANCE = {
  wage_complaint: {
    title: '임금체불 진정서',
    paragraphs: [
      '노동청(고용노동부 노동포털)에 제출하는 공식 서류예요. 못 받은 임금·수당이 있을 때 사용하고, 제출하면 담당 근로감독관이 조사를 시작해요.',
      '사업장 정보와 체불 금액을 미리 알아두면 작성이 빠를 거예요.',
    ],
  },
  unfair_dismissal: {
    title: '부당해고 구제신청서',
    paragraphs: [
      '노동위원회에 제출해요. 해고일로부터 3개월 이내 신청해야 하고, 5인 이상 사업장에만 적용돼요.',
      '두 조건에 해당하면 복직 또는 임금 상당액을 받을 수 있어요. 시작 전에 꼭 확인해 보세요.',
    ],
  },
  payment_demand: {
    title: '내용증명',
    paragraphs: [
      '우체국에서 발송하는 공식 편지예요. 진정·소송 전에 "이 돈을 달라"고 공식 기록을 남기는 용도예요.',
      '법적 강제력은 없지만 이후 분쟁에서 중요한 증거가 돼요.',
    ],
  },
}

/**
 * @param {{ doc_type: string, onStart: (docType: string) => void, onCancel: () => void }} props
 */
export default function GuidanceBubble({ doc_type, onStart, onCancel }) {
  const info = GUIDANCE[doc_type] ?? GUIDANCE.wage_complaint

  return (
    <div className="alzi-row alzi-row--bot">
      <div className="alzi-avatar" aria-hidden="true">A</div>
      <div className="alzi-bubble alzi-bubble--bot alzi-bubble--guidance">
        <p className="alzi-guidance-title">{info.title}</p>
        {info.paragraphs.map((p, i) => (
          <p key={i} className="alzi-guidance-body">{p}</p>
        ))}
        <p className="alzi-guidance-prompt">몇 가지만 여쭤보고 작성해 드릴게요. 시작할까요?</p>
        <div className="alzi-choice-row alzi-choice-row--inline">
          <button
            className="alzi-choice-btn alzi-choice-btn--primary"
            type="button"
            onClick={() => onStart(doc_type)}
          >
            시작하기
          </button>
          <button
            className="alzi-choice-btn alzi-choice-btn--secondary"
            type="button"
            onClick={onCancel}
          >
            취소
          </button>
        </div>
      </div>
    </div>
  )
}
