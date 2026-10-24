import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { Footer } from './components/Footer'
import { Header } from './components/Header'
import { DialoguePage } from './pages/DialoguePage'
import { FaqPage } from './pages/FaqPage'
import { HomePage } from './pages/HomePage'
import { PerspectivesPage } from './pages/PerspectivesPage'
import { RecordsPage } from './pages/RecordsPage'
import { SummaryPage } from './pages/SummaryPage'

export default function App() {
  const location = useLocation()
  const isDialogue = location.pathname.startsWith('/dialogue')

  return (
    <div className="app-shell">
      <Header />
      <main
        style={
          isDialogue
            ? { flex: 1, minHeight: 0, height: 'calc(100vh - 72px)', overflow: 'hidden', display: 'flex', flexDirection: 'column' }
            : { flex: 1 }
        }
      >
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/perspectives/:sessionId" element={<PerspectivesPage />} />
          <Route path="/dialogue/:sessionId" element={<DialoguePage />} />
          <Route path="/summary/:sessionId" element={<SummaryPage />} />
          <Route path="/records" element={<RecordsPage />} />
          <Route path="/faq" element={<FaqPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      {!isDialogue && <Footer />}
    </div>
  )
}
