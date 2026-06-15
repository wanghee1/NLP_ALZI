const CHIPS = [
  '주휴수당 받을 수 있나요?',
  '퇴직금 조건이 어떻게 되나요?',
  '최저임금 기준이 궁금해요',
  '해고예고수당 뭔가요?',
]

/**
 * @param {{ onSelect: (text: string) => void }} props
 */
export default function QuickChips({ onSelect }) {
  return (
    <div className="alzi-chips" role="list" aria-label="빠른 질문 예시">
      {CHIPS.map(chip => (
        <button
          key={chip}
          className="alzi-chip"
          role="listitem"
          type="button"
          onClick={() => onSelect(chip)}
        >
          {chip}
        </button>
      ))}
    </div>
  )
}
