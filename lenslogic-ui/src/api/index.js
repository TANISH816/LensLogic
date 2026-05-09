import axios from 'axios'

const BASE = 'http://localhost:8000'

// ── Organizer ─────────────────────────────────────────────────────────────────

/**
 * Upload photos and get a Group ID back.
 * Encoding runs in the background on the server.
 */
export async function uploadPhotos(files, eventName = '', onProgress) {
  const formData = new FormData()
  files.forEach(f => formData.append('files', f))

  const res = await axios.post(
    `${BASE}/upload?event_name=${encodeURIComponent(eventName)}`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: e => {
        if (onProgress) onProgress(Math.round((e.loaded / e.total) * 100))
      }
    }
  )
  return res.data
}

/**
 * Poll /status/:groupId to track encoding progress.
 */
export async function getGroupStatus(groupId) {
  const res = await axios.get(`${BASE}/status/${groupId}`)
  return res.data
}

// ── Guest ─────────────────────────────────────────────────────────────────────

/**
 * Submit a selfie + Group ID to find matching photos.
 */
export async function matchFace(groupId, selfieFile) {
  const formData = new FormData()
  formData.append('selfie', selfieFile)

  const res = await axios.post(
    `${BASE}/match?group_id=${groupId}`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  )
  return res.data
}