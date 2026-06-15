/**
 * @param {{ icon: string, title: string, desc: string, onClick: () => void }} props
 */
export default function FeatureCard({ icon, title, desc, onClick }) {
  return (
    <button className="alzi-feature-card" onClick={onClick} type="button">
      <span className="alzi-feature-icon" aria-hidden="true">{icon}</span>
      <span className="alzi-feature-text">
        <span className="alzi-feature-title">{title}</span>
        <span className="alzi-feature-desc">{desc}</span>
      </span>
    </button>
  )
}
