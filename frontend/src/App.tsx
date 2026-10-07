/**
 * Root application component: routes + app shell.
 *
 * Uses react-router-dom v7 (Routes/Route, no createBrowserRouter needed here since
 * BrowserRouter wraps in main.tsx). Each route is wrapped in a PageErrorBoundary
 * so a render crash in one page never takes down the whole app.
 *
 * Routes:
 *  /                  → DashboardPage
 *  /violations        → ViolationsPage
 *  /violations/:id    → ViolationDetailPage
 *  /cameras/:id       → CameraDetailPage
 *  *                  → NotFoundPage
 *
 * @module App
 */
import { Route, Routes } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { PageErrorBoundary } from '@/components/layout/PageErrorBoundary'
import { CameraDetail } from '@/pages/CameraDetail'
import { DashboardPage } from '@/pages/Dashboard'
import { NotFound } from '@/pages/NotFound'
import { ViolationDetail } from '@/pages/ViolationDetail'
import { Violations } from '@/pages/Violations'

/**
 * Root component: AppShell wraps all routes; each route has an error boundary.
 *
 * @returns The app element.
 */
export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route
          path="/"
          element={<PageErrorBoundary><DashboardPage /></PageErrorBoundary>}
        />
        <Route
          path="/violations"
          element={<PageErrorBoundary><Violations /></PageErrorBoundary>}
        />
        <Route
          path="/violations/:id"
          element={<PageErrorBoundary><ViolationDetail /></PageErrorBoundary>}
        />
        <Route
          path="/cameras/:id"
          element={<PageErrorBoundary><CameraDetail /></PageErrorBoundary>}
        />
        <Route
          path="*"
          element={<PageErrorBoundary><NotFound /></PageErrorBoundary>}
        />
      </Route>
    </Routes>
  )
}
