import { useState, useRef } from 'react'
import UploadZone from '../components/UploadZone'
import FileList   from '../components/FileList'
import StatusPoller from '../components/StatusPoller'
import { uploadPhotos } from '../api'

export default function OrganizerPage() {
  const [files,       setFiles]       = useState([])
  const [faceResults, setFaceResults] = useState({})   // per-file face counts
  const [eventName,   setEventName]   = useState('')
  const [uploading,   setUploading]   = useState(false)
  const [uploadPct,   setUploadPct]   = useState(0)
  const [groupId,     setGroupId]     = useState(null)
  const [totalPhotos, setTotalPhotos] = useState(0)
  const [error,       setError]       = useState('')

  // ── When files are picked ────────────────────────────────────────────────

  function handleFiles(newFiles) {
    setFiles(newFiles)
    setGroupId(null)
    setError('')

    // Mark every file as "scanning" immediately
    const initial = {}
    newFiles.forEach(f => { initial[f.name] = { status: 'scanning', count: 0 } })
    setFaceResults(initial)

    // Read each file as an image, draw on canvas, count faces using a
    // simple heuristic: we detect flesh-tone blobs.
    // For a real count we just send to the backend — here we do a quick
    // client-side check to give instant visual feedback per file.
    newFiles.forEach(file => {
      const reader = new FileReader()
      reader.onload = e => {
        const img = new Image()
        img.onload = () => {
          // We approximate by checking image dimensions (portrait = likely face).
          // Real count comes from the backend after upload.
          // For now just mark as "unknown / to be confirmed by server".
          // We update this once the server finishes encoding.
          setFaceResults(prev => ({
            ...prev,
            [file.name]: { status: 'done', count: '?' }
          }))
        }
        img.src = e.target.result
      }
      reader.readAsDataURL(file)
    })
  }

  // ── Upload ───────────────────────────────────────────────────────────────

  async function handleUpload() {
    if (!files.length) return
    setUploading(true)
    setError('')
    setUploadPct(0)

    try {
      const data = await uploadPhotos(files, eventName, pct => setUploadPct(pct))
      setGroupId(data.group_id)
      setTotalPhotos(data.total_photos)
    } catch (e) {
      setError(e?.response?.data?.detail || 'Upload failed. Is the backend running?')
    } finally {
      setUploading(false)
    }
  }

  // ── When encoding is done, update face counts from status ────────────────

  function handleEncodingDone(status) {
    // status.total_encodings = total face rows across all photos
    // We can't get per-file breakdown from status alone (would need a new endpoint),
    // so we mark all files as done with a shared note.
    setFaceResults(prev => {
      const updated = { ...prev }
      files.forEach(f => {
        if (updated[f.name]?.count === '?') {
          updated[f.name] = { status: 'done', count: '✓' }
        }
      })
      return updated
    })
  }

  const canUpload = files.length > 0 && !uploading && !groupId

  return (
    <div className="page">
      <div className="section-label">Organizer</div>
      <h1 className="section-title">Upload Event Photos</h1>

      {/* Event name */}
      <div className="input-group">
        <label className="input-label">Event Name (optional)</label>
        <input
          className="input"
          style={{ textTransform: 'none', letterSpacing: 0 }}
          placeholder="e.g. Raj & Priya Wedding 2025"
          value={eventName}
          onChange={e => setEventName(e.target.value)}
          disabled={!!groupId}
        />
      </div>

      {/* Drop zone */}
      {!groupId && (
        <UploadZone
          onFiles={handleFiles}
          label={files.length ? `${files.length} photo${files.length > 1 ? 's' : ''} selected — drop more or click to replace` : undefined}
        />
      )}

      {/* Per-file list with face status */}
      <FileList files={files} faceResults={faceResults} />

      {/* Upload button */}
      {!groupId && files.length > 0 && (
        <div style={{ marginTop: 24, display: 'flex', alignItems: 'center', gap: 16 }}>
          <button className="btn btn-primary" onClick={handleUpload} disabled={!canUpload}>
            {uploading ? <><span className="spinner" /> Uploading {uploadPct}%</> : '↑ Upload & Generate Group ID'}
          </button>
          <button className="btn btn-outline" onClick={() => { setFiles([]); setFaceResults({}) }}>
            Clear
          </button>
        </div>
      )}

      {error && <div className="alert alert-error">{error}</div>}

      {/* Group ID display */}
      {groupId && (
        <>
          <div className="group-id-box">
            <div className="group-id-label">Share this Group ID with your guests</div>
            <div className="group-id-value">{groupId}</div>
            <div className="group-id-sub">
              {totalPhotos} photo{totalPhotos !== 1 ? 's' : ''} uploaded · faces are being encoded in the background
            </div>
          </div>

          {/* Live encoding progress */}
          <StatusPoller
            groupId={groupId}
            totalPhotos={totalPhotos}
            onDone={handleEncodingDone}
          />

          <div style={{ marginTop: 20 }}>
            <button className="btn btn-outline" onClick={() => {
              setFiles([]); setFaceResults({}); setGroupId(null); setEventName(''); setTotalPhotos(0)
            }}>
              + New Event
            </button>
          </div>
        </>
      )}
    </div>
  )
}