import { useRef, useState } from 'react'

export default function UploadZone({ onFiles, multiple = true, label }) {
  const inputRef = useRef()
  const [isDragging, setIsDragging] = useState(false)

  function handleFiles(fileList) {
    const files = Array.from(fileList).filter(f => f.type.startsWith('image/'))
    if (files.length) onFiles(files)
  }

  function onDragOver(e) {
    e.preventDefault()
    setIsDragging(true)
  }

  function onDragLeave(e) {
    e.preventDefault()
    setIsDragging(false)
  }

  function onDrop(e) {
    e.preventDefault()
    setIsDragging(false)
    handleFiles(e.dataTransfer.files)
  }

  function onChange(e) {
    handleFiles(e.target.files)
    e.target.value = ''   // reset so same file can be re-selected
  }

  return (
    <div
      className={`dropzone ${isDragging ? 'active' : ''}`}
      onClick={() => inputRef.current.click()}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        multiple={multiple}
        style={{ display: 'none' }}
        onChange={onChange}
      />
      <span className="dropzone-icon">{isDragging ? '📂' : '🖼️'}</span>
      <p className="dropzone-text">
        {isDragging
          ? <strong>Drop it!</strong>
          : <><strong>{label || 'Click or drag photos here'}</strong><br />Supports JPG, PNG, WEBP</>
        }
      </p>
    </div>
  )
}