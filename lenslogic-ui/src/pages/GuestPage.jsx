import { useState } from 'react'
import UploadZone from '../components/UploadZone'
import PhotoGrid  from '../components/PhotoGrid'
import { matchFace } from '../api'

export default function GuestPage() {
  const [groupId,  setGroupId]  = useState('')
  const [selfie,   setSelfie]   = useState(null)
  const [preview,  setPreview]  = useState(null)
  const [loading,  setLoading]  = useState(false)
  const [result,   setResult]   = useState(null)   // { matched_photos, message, total_matched, total_searched }
  const [error,    setError]    = useState('')

  function handleSelfie([file]) {
    setSelfie(file)
    setPreview(URL.createObjectURL(file))
    setResult(null)
    setError('')
  }

  async function handleMatch() {
    if (!groupId.trim() || !selfie) return
    setLoading(true)
    setError('')
    setResult(null)

    try {
      const data = await matchFace(groupId.trim().toUpperCase(), selfie)
      setResult(data)
    } catch (e) {
      const msg = e?.response?.data?.detail || 'Something went wrong. Check the Group ID and try again.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const canMatch = groupId.trim().length > 0 && selfie && !loading

  return (
    <div className="page">
      <div className="section-label">Guest</div>
      <h1 className="section-title">Find My Photos</h1>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>

        {/* Left: Group ID + selfie */}
        <div>
          <div className="input-group">
            <label className="input-label">Group ID</label>
            <input
              className="input"
              placeholder="e.g. A3F9B2C1"
              value={groupId}
              maxLength={8}
              onChange={e => { setGroupId(e.target.value.toUpperCase()); setResult(null) }}
            />
          </div>

          <div style={{ marginBottom: 8 }}>
            <label className="input-label">Your Selfie</label>
          </div>
          <UploadZone
            onFiles={handleSelfie}
            multiple={false}
            label={selfie ? `${selfie.name} — click to change` : 'Upload a clear selfie of yourself'}
          />

          {preview && (
            <img src={preview} alt="Selfie preview" className="selfie-preview" />
          )}

          <div style={{ marginTop: 20 }}>
            <button className="btn btn-primary" onClick={handleMatch} disabled={!canMatch}>
              {loading
                ? <><span className="spinner" /> Searching…</>
                : '🔍 Find My Photos'
              }
            </button>
          </div>

          {error && <div className="alert alert-error">{error}</div>}

          {result && (
            <div className={`alert ${result.total_matched > 0 ? 'alert-success' : 'alert-info'}`}>
              {result.message}
              {result.total_searched > 0 && (
                <div style={{ marginTop: 4, fontSize: 12, opacity: 0.8 }}>
                  Searched {result.total_searched.toLocaleString()} face encodings
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right: Tips */}
        <div className="card" style={{ height: 'fit-content' }}>
          <div className="section-label" style={{ marginBottom: 12 }}>Tips for best results</div>
          {[
            ['💡', 'Good lighting', 'Make sure your face is clearly lit — avoid backlight'],
            ['👤', 'Solo selfie', 'Only one face in the selfie works best'],
            ['📐', 'Face forward', 'Look directly at the camera, avoid extreme angles'],
            ['🔑', 'Correct Group ID', 'Double-check the 8-character code from the organizer'],
            ['⏳', 'Give it a moment', 'If the event just started, photos may still be encoding'],
          ].map(([icon, title, desc]) => (
            <div key={title} style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
              <span style={{ fontSize: 20 }}>{icon}</span>
              <div>
                <div style={{ fontWeight: 500, fontSize: 13, marginBottom: 2 }}>{title}</div>
                <div style={{ fontSize: 12, color: 'var(--grey4)', lineHeight: 1.5 }}>{desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Results */}
      {result?.matched_photos?.length > 0 && (
        <>
          <div className="divider" />
          <PhotoGrid photos={result.matched_photos} />
        </>
      )}
    </div>
  )
}