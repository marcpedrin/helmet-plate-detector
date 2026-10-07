/**
 * Application shell: TopBar + ConnectionBanner + <Outlet /> + footer disclaimer.
 *
 * Polls /api/health every 10 s to detect backend outages.
 * Provides the `backendDown` state to the ConnectionBanner.
 *
 * Footer disclaimer is required on every page by the acceptance criteria
 * (6.1 / 8.5): "Prototype for demonstration. Detections are probabilistic…"
 *
 * @module components/layout/AppShell
 * @example
 * // In App.tsx:
 * <AppShell />
 */
import { useEffect, useState } from 'react'
import { Outlet } from 'react-router-dom'
import { ConnectionBanner } from './ConnectionBanner'
import { TopBar } from './TopBar'
import { useLiveEvents } from '@/hooks/useLiveEvents'
import { getHealth } from '@/services/api'
import type { HealthOut } from '@/types/contracts'

/**
 * Root layout wrapping all pages.
 * Polls health every 10 s to drive the backend-down banner.
 *
 * @returns The shell element containing the page outlet.
 */
export const AppShell = () => {
  const { status } = useLiveEvents()
  const [health, setHealth] = useState<HealthOut | null>(null)
  const [backendDown, setBackendDown] = useState(false)

  useEffect(() => {
    let cancelled = false
    const check = async () => {
      try {
        const h = await getHealth()
        if (!cancelled) {
          setHealth(h)
          setBackendDown(false)
        }
      } catch {
        if (!cancelled) setBackendDown(true)
      }
    }
    check()
    // WHY 10 s: frequent enough to detect outages quickly, not so frequent as to spam logs.
    const interval = setInterval(check, 10_000)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [])

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <TopBar health={health} wsStatus={status} />
      <ConnectionBanner wsStatus={status} backendDown={backendDown} />

      <main className="flex-1 overflow-auto p-3 md:p-4">
        <Outlet />
      </main>

      <footer className="border-t border-border px-4 py-2 text-center text-xs text-muted-foreground">
        Prototype for demonstration. Detections are probabilistic and require human review;
        not admissible enforcement evidence. All processing is local.
      </footer>
    </div>
  )
}
