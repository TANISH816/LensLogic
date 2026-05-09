import { useState } from 'react'

export default function PhotoGrid({ photos }) {
  const [lightbox, setLightbox] = useState(null)

  if (!photos.length) return (
    <div className="empty">
      <span className="empty-icon">🔍</span>
      <p className="empty-text">No matching photos found.<br />Try a clearer selfie or check your Group ID.</p>
    </div>
  )

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
        <span className="section-label" style={{ margin: 0 }}>Your Photos</span>
        <span style={{ fontSize: 12, color: 'var(--grey4)', fontFamily: 'var(--font-mono)' }}>
          {photos.length} match{photos.length !== 1 ? 'es' : ''}
        </span>
      </div>

      <div className="photo-grid">
        {photos.map((url, i) => (
          <div
            className="photo-card"
            key={i}
            style={{ animationDelay: `${i * 0.05}s` }}
            onClick={() => setLightbox(url)}
          >
            <img src={url} alt={`Match ${i + 1}`} loading="lazy" />
            <div className="photo-card-overlay">
              <a
                href={url}
                download
                className="photo-card-dl"
                onClick={e => e.stopPropagation()}
              >
                ↓ Download
              </a>
            </div>
          </div>
        ))}
      </div>

      {lightbox && (
        <div className="lightbox" onClick={() => setLightbox(null)}>
          <button className="lightbox-close" onClick={() => setLightbox(null)}>✕</button>
          <img src={lightbox} alt="Full size" onClick={e => e.stopPropagation()} />
        </div>
      )}
    </>
  )
}