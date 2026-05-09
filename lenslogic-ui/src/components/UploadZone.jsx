import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'

export default function UploadZone({ onFiles, accept = { 'image/*': [] }, multiple = true, label }) {
  const onDrop = useCallback(accepted => {
    if (accepted.length) onFiles(accepted)
  }, [onFiles])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept, multiple
  })

  return (
    <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
      <input {...getInputProps()} />
      <span className="dropzone-icon">{isDragActive ? '📂' : '🖼️'}</span>
      <p className="dropzone-text">
        {isDragActive
          ? <strong>Drop it!</strong>
          : <><strong>{label || 'Click or drag photos here'}</strong><br />Supports JPG, PNG, WEBP</>
        }
      </p>
    </div>
  )
}