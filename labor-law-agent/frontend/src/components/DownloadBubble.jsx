import { resolveUrl } from '../api/client.js'

/**
 * @param {{ content: string, download_url: string|null }} props
 */
export default function DownloadBubble({ content, download_url }) {
  const url = resolveUrl(download_url)

  return (
    <div className="alzi-row alzi-row--bot">
      <div className="alzi-avatar" aria-hidden="true">A</div>
      <div className="alzi-bubble alzi-bubble--bot alzi-bubble--download">
        <p className="alzi-consultation-text">{content}</p>
        {url && (
          <a
            className="alzi-download-btn"
            href={url}
            download
            rel="noopener noreferrer"
          >
            📥 진정서 다운로드
          </a>
        )}
      </div>
    </div>
  )
}
