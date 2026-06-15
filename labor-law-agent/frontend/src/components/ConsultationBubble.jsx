import LegalGroundsToggle from './LegalGroundsToggle.jsx'
import SuggestDocBanner from './SuggestDocBanner.jsx'

/**
 * \n\n 기준으로 문단 분리 → 각각 <p> 렌더 (간격 제어 + pre-wrap 줄바꿈 유지)
 */
function Paragraphs({ text }) {
  if (!text) return null
  const paras = text.split('\n\n').filter(Boolean)
  if (paras.length === 1) {
    return <p className="alzi-consultation-para">{text}</p>
  }
  return (
    <>
      {paras.map((para, i) => (
        <p key={i} className="alzi-consultation-para">{para}</p>
      ))}
    </>
  )
}

/**
 * @param {{ content: string, legal_grounds: Array, sources: Array,
 *           suggest_document: boolean, document_type: string|null,
 *           onDocTypeSelect: (type: string) => void }} props
 */
export default function ConsultationBubble({
  content,
  legal_grounds,
  sources,
  suggest_document = false,
  document_type = null,
  onDocTypeSelect,
}) {
  return (
    <div className="alzi-row alzi-row--bot">
      <div className="alzi-avatar" aria-hidden="true">A</div>
      <div className="alzi-bubble alzi-bubble--bot alzi-bubble--consultation">
        <Paragraphs text={content} />
        <LegalGroundsToggle grounds={legal_grounds} />
        {sources && sources.length > 0 && (
          <p className="alzi-sources">출처: {sources.join(', ')}</p>
        )}
        {suggest_document && document_type && (
          <SuggestDocBanner document_type={document_type} onDocTypeSelect={onDocTypeSelect} />
        )}
      </div>
    </div>
  )
}
