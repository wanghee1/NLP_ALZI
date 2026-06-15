import { useState } from 'react'

/**
 * @param {{ grounds: Array<{law_name:string, article:string, title:string, plain:string, original:string}> }} props
 */
export default function LegalGroundsToggle({ grounds }) {
  const [open, setOpen] = useState(false)

  if (!grounds || grounds.length === 0) return null

  return (
    <div className="alzi-grounds">
      <button
        className="alzi-grounds-toggle-btn"
        type="button"
        aria-expanded={open}
        onClick={() => setOpen(v => !v)}
      >
        <span>
          {open
            ? `▲ 접기`
            : `📖 근거 법률 ${grounds.length}개 확인하기`}
        </span>
        <span className={`alzi-grounds-chevron${open ? ' alzi-grounds-chevron--open' : ''}`} aria-hidden="true" />
      </button>

      {/* 항상 DOM에 존재 — open 클래스로 CSS transition 제어 (조건부 렌더 시 max-height 전환 불가) */}
      <ul
        className={`alzi-grounds-body${open ? ' alzi-grounds-body--open' : ''}`}
        role="list"
        aria-hidden={!open}
      >
        {grounds.map((g, i) => (
          <li key={i} className="alzi-ground-item">
            <p className="alzi-ground-meta">
              <span className="alzi-ground-law">{g.law_name}</span>
              {g.article && <span className="alzi-ground-article"> {g.article}</span>}
              {g.title && <span className="alzi-ground-title"> — {g.title}</span>}
            </p>
            <p className="alzi-ground-plain">💡 {g.plain}</p>
            {g.original && (
              <details className="alzi-ground-original-wrap">
                <summary className="alzi-ground-original-toggle">📋 실제 조문 보기</summary>
                <pre className="alzi-ground-original">{g.original}</pre>
              </details>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
