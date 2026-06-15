import FeatureCard from './FeatureCard.jsx'
import QuickChips from './QuickChips.jsx'

const FEATURES = [
  {
    icon: '⚖️',
    title: '노동법 Q&A',
    desc: '임금·근로시간·해고 등 궁금한 점을 물어보세요',
  },
  {
    icon: '📄',
    title: '계약서 분석',
    desc: '근로계약서 PDF를 올리면 위험 조항을 찾아드려요',
  },
  {
    icon: '📝',
    title: '진정서 작성',
    desc: '임금체불·부당해고 등 진정서·내용증명을 만들어 드려요',
  },
]

/**
 * @param {{ onSend: (text: string) => void, onContractClick: () => void,
 *           onDocSelect: () => void, onQnaClick: () => void }} props
 */
export default function EmptyState({ onSend, onContractClick, onDocSelect, onQnaClick }) {
  function handleFeatureClick(title) {
    if (title === '계약서 분석') {
      onContractClick()
    } else if (title === '진정서 작성') {
      onDocSelect()
    } else if (title === '노동법 Q&A') {
      onQnaClick()
    }
  }

  return (
    <div className="alzi-empty" aria-label="ALZI 시작 화면">
      <div className="alzi-empty-hero">
        <p className="alzi-empty-tagline">법은 어렵지만,</p>
        <p className="alzi-empty-tagline highlight">ALZI는 쉽게</p>
        <p className="alzi-empty-sub">아르바이트·신입 근로자를 위한 노동법 AI 상담</p>
      </div>

      <div className="alzi-feature-grid" role="list" aria-label="주요 기능">
        {FEATURES.map(f => (
          <FeatureCard
            key={f.title}
            icon={f.icon}
            title={f.title}
            desc={f.desc}
            onClick={() => handleFeatureClick(f.title)}
          />
        ))}
      </div>

      <div className="alzi-faq-section">
        <p className="alzi-faq-title">자주 묻는 질문</p>
        <QuickChips onSelect={onSend} />
      </div>
    </div>
  )
}
