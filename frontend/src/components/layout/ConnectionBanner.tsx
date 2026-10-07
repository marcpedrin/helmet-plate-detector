/**
 * Full-width banner shown when the WebSocket is reconnecting or the backend is unreachable.
 *
 * States rendered:
 * - WS not open → amber "RECONNECTING…" bar
 * - Backend health fails → red "Backend unreachable. Retrying…" bar
 * - Both OK → renders nothing (null)
 *
 * @module components/layout/ConnectionBanner
 * @example
 * <ConnectionBanner wsStatus={status} backendDown={isDown} />
 */
import { WifiOff } from 'lucide-react'
import type { WsStatus } from '@/services/ws'

/**
 * Props for the ConnectionBanner.
 *
 * @param wsStatus - Current WebSocket connection status.
 * @param backendDown - True when /api/health is unreachable.
 */
export const ConnectionBanner = ({
  wsStatus,
  backendDown,
}: {
  wsStatus: WsStatus
  backendDown: boolean
}) => {
  if (backendDown) {
    return (
      <div className="flex items-center gap-2 bg-offline/20 border-b border-offline/40 px-4 py-1.5 text-sm text-offline font-medium">
        <WifiOff className="h-4 w-4 flex-shrink-0" />
        <span>Backend unreachable. Retrying…</span>
      </div>
    )
  }
  if (wsStatus !== 'open') {
    return (
      <div className="flex items-center gap-2 bg-starting/10 border-b border-starting/30 px-4 py-1.5 text-sm text-starting font-medium">
        <span className="h-2 w-2 rounded-full bg-starting animate-pulse" />
        <span>
          {wsStatus === 'connecting' ? 'Connecting to live feed…' : 'RECONNECTING… Live data may be delayed.'}
        </span>
      </div>
    )
  }
  return null
}
