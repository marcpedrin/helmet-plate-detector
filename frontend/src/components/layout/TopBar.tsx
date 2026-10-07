/**
 * Top navigation bar with product name, nav links, model status chips, and connection pill.
 *
 * Shows a "MOCK DATA" badge when the backend is running in mock mode.
 *
 * @module components/layout/TopBar
 * @example
 * <TopBar health={health} wsStatus={status} />
 */
import { NavLink } from 'react-router-dom'
import { Shield } from 'lucide-react'
import { ConnectionPill } from './ConnectionPill'
import { ModelStatus } from './ModelStatus'
import type { HealthOut } from '@/types/contracts'
import type { WsStatus } from '@/services/ws'

/**
 * Application top navigation bar.
 *
 * @param props.health - Current health response; null while loading.
 * @param props.wsStatus - WebSocket connection status.
 * @returns The top bar element.
 */
export const TopBar = ({ health, wsStatus }: { health: HealthOut | null; wsStatus: WsStatus }) => {
  const isMock = health?.mode === 'mock'

  return (
    <header className="sticky top-0 z-40 flex h-12 items-center gap-4 border-b border-border bg-card/80 backdrop-blur-sm px-4">
      {/* Brand */}
      <NavLink to="/" className="flex items-center gap-2 font-semibold text-sm text-foreground shrink-0">
        <Shield className="h-4 w-4 text-offline" aria-hidden />
        <span className="tracking-tight">Helmet &amp; Plate Detector</span>
      </NavLink>

      {/* Nav */}
      <nav className="flex gap-1 text-xs" aria-label="Main navigation">
        {([
          { to: '/', label: 'Dashboard', end: true },
          { to: '/violations', label: 'Violations', end: false },
        ] as const).map(({ to, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `rounded px-2.5 py-1 font-medium transition-colors ${
                isActive
                  ? 'bg-accent text-accent-foreground'
                  : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
              }`
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Right-side status row */}
      <div className="ml-auto flex items-center gap-3">
        {/* WHY: Model status chips help judges see at a glance whether mock or real models are running */}
        <ModelStatus health={health} />

        {isMock && (
          <span className="rounded-full border border-mock px-2 py-0.5 text-xs font-semibold tracking-wider"
            style={{ color: 'var(--mock-accent)', borderColor: 'color-mix(in oklch, var(--mock-accent) 40%, transparent)' }}>
            MOCK DATA
          </span>
        )}

        <ConnectionPill status={wsStatus} />
      </div>
    </header>
  )
}
