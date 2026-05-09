import { useState } from 'react'
import OrganizerPage from './pages/OrganizerPage'
import GuestPage     from './pages/GuestPage'

export default function App() {
  const [tab, setTab] = useState('organizer')

  return (
    <div className="app">
      <nav className="nav">
        <div className="nav-logo">LENSLOGIC</div>
        <div className="nav-tabs">
          <button
            className={`nav-tab ${tab === 'organizer' ? 'active' : ''}`}
            onClick={() => setTab('organizer')}
          >
            Organizer
          </button>
          <button
            className={`nav-tab ${tab === 'guest' ? 'active' : ''}`}
            onClick={() => setTab('guest')}
          >
            Guest
          </button>
        </div>
      </nav>

      {tab === 'organizer' ? <OrganizerPage /> : <GuestPage />}
    </div>
  )
}