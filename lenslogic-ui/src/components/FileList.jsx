import { useState, useEffect } from 'react'

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

/**
 * FileList shows each uploaded file with:
 * - Filename + size
 * - Face detection status per file (scanning / found N / no face)
 *
 * faceResults: { [filename]: { status: 'scanning'|'done'|'error', count: number } }
 */
export default function FileList({ files, faceResults = {} }) {
  if (!files.length) return null

  const totalFaces = Object.values(faceResults)
    .filter(r => r.status === 'done')
    .reduce((sum, r) => sum + r.count, 0)

  const doneCount = Object.values(faceResults).filter(r => r.status === 'done').length
  const noFaceCount = Object.values(faceResults).filter(r => r.status === 'done' && r.count === 0).length

  return (
    <div style={{ marginTop: 24 }}>
      {/* Summary stats */}
      <div className="stats-row">
        <div className="stat-box">
          <div className="stat-val">{files.length}</div>
          <div className="stat-key">Photos Selected</div>
        </div>
        <div className="stat-box">
          <div className="stat-val">{doneCount}</div>
          <div className="stat-key">Analysed</div>
        </div>
        <div className="stat-box">
          <div className="stat-val">{totalFaces}</div>
          <div className="stat-key">Faces Found</div>
        </div>
        <div className="stat-box">
          <div className="stat-val" style={{ color: noFaceCount > 0 ? 'var(--red)' : 'var(--green)' }}>
            {noFaceCount}
          </div>
          <div className="stat-key">No Face</div>
        </div>
      </div>

      {/* Per-file list */}
      <div className="file-list">
        {files.map((file, i) => {
          const result = faceResults[file.name]
          return (
            <div className="file-item" key={i} style={{ animationDelay: `${i * 0.04}s` }}>
              <span className="file-item-name">
                {file.name.length > 36 ? file.name.slice(0, 33) + '…' : file.name}
              </span>
              <span className="file-item-size">{formatSize(file.size)}</span>
              <FaceBadge result={result} />
            </div>
          )
        })}
      </div>
    </div>
  )
}

function FaceBadge({ result }) {
  if (!result) {
    return <span className="file-item-face face-scanning">—</span>
  }
  if (result.status === 'scanning') {
    return <span className="file-item-face face-scanning pulse">Scanning…</span>
  }
  if (result.status === 'done' && result.count > 0) {
    return (
      <span className="file-item-face face-found">
        {result.count} face{result.count > 1 ? 's' : ''} ✓
      </span>
    )
  }
  if (result.status === 'done' && result.count === 0) {
    return <span className="file-item-face face-none">No face</span>
  }
  return <span className="file-item-face face-none">Error</span>
}