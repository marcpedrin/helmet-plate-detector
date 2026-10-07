/**
 * Routes + app shell (header with connection/mode status).
 * @module App
 */
import { NavLink, Route, Routes } from 'react-router-dom'
import { Badge } from '@/components/ui/badge'
import { useLiveEvents } from '@/hooks/useLiveEvents'
import { CameraDetail } from '@/pages/CameraDetail'
import { Dashboard } from '@/pages/Dashboard'
import { NotFound } from '@/pages/NotFound'
import { ViolationDetail } from '@/pages/ViolationDetail'
import { Violations } from '@/pages/Violations'

/**
 * Root component: shell + routes `/`, `/violations`, `/violations/:id`, `/cameras/:id`, `*`.
 * @returns The app.
 */
export default function App() {
  const { status, hello } = useLiveEvents()
  return (
    <div className="bg-background text-foreground min-h-screen">
      <header className="flex items-center gap-4 border-b px-4 py-2">
        <span className="font-semibold">Helmet &amp; Plate Detector</span>
        <nav className="flex gap-3 text-sm">
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          <NavLink to="/violations">Violations</NavLink>
        </nav>
        <div className="ml-auto flex gap-2">
          {hello?.mode === 'mock' && <Badge variant="destructive">MOCK DATA</Badge>}
          <Badge variant={status === 'open' ? 'secondary' : 'outline'}>ws: {status}</Badge>
        </div>
      </header>
      <main className="p-4">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/violations" element={<Violations />} />
          <Route path="/violations/:id" element={<ViolationDetail />} />
          <Route path="/cameras/:id" element={<CameraDetail />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
    </div>
  )
}
