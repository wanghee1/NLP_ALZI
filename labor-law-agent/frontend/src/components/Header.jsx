/**
 * @param {{ onReset: () => void }} props
 */
export default function Header({ onReset }) {
  return (
    <header className="alzi-header">
      <div className="alzi-header-brand">
        <button
          className="alzi-logo-btn"
          type="button"
          aria-label="홈으로"
          onClick={onReset}
        >
          <span className="alzi-logo">ALZI</span>
        </button>
        <span className="alzi-tagline">법은 어렵지만, ALZI는 쉽게</span>
      </div>
    </header>
  )
}
