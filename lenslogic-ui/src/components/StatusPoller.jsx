import { useEffect, useState, useRef } from 'react'
import { getGroupStatus } from '../api'

/**
 * Polls /status/:groupId every 3 seconds.
 * Shows encoding progress with a live counter.
 * Calls onDone() when the count stabilises (no new encodings for 2 polls).
 */
export default function StatusPoller({ groupId, totalPhotos, onDone }) {
  const [encodings, setEncodings] = useState(0)
  const [done, setDone]           = useState(false)
  const prevCount                  = useRef(0)
  const stableRounds               = useRef(0)

  useEffect(() => {
    if (!groupId) return
    const interval = setInterval(async () => {
      try {
        const data = await getGroupStatus(groupId)
        const count = data.total_encodings ?? 0
        setEncodings(count)

        // Consider done when count > 0 and hasn't changed for 2 polls
        if (count > 0 && count === prevCount.current) {
          stableRounds.current++
          if (stableRounds.current >= 2) {
            setDone(true)
            clearInterval(interval)
            onDone && onDone(data)
          }
        } else {
          stableRounds.current = 0
        }
        prevCount.current = count
      } catch (e) {
        // ignore polling errors
      }
    }, 3000)

    return () => clearInterval(interval)
  }, [groupId])

  return (
    <div className="card" style={{ marginTop: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <span className="section-label" style={{ margin: 0 }}>Encoding Progress</span>
        {done
          ? <span className="badge badge-done">✓ Complete</span>
          : <span className="badge badge-processing"><span className="pulse">●</span> Processing</span>
        }
      </div>

      <div style={{ fontSize: 13, color: 'var(--grey4)', marginBottom: 12 }}>
        {done
          ? `All faces encoded — ${encodings} face encoding${encodings !== 1 ? 's' : ''} stored.`
          : `Encoding faces… ${encodings} stored so far across ${totalPhotos} photo${totalPhotos !== 1 ? 's' : ''}.`
        }
      </div>

      <div className="progress-bar-wrap">
        <div
          className="progress-bar-fill"
          style={{ width: done ? '100%' : encodings > 0 ? '60%' : '5%' }}
        />
      </div>

      {!done && (
        <p style={{ fontSize: 12, color: 'var(--grey4)', fontFamily: 'var(--font-mono)' }}>
          Guests can start using the Group ID right away — more photos become searchable as encoding progresses.
        </p>
      )}
    </div>
  )
}