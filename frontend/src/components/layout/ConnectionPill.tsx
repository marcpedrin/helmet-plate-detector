/**
 * WebSocket connection status pill shown in the top bar.
 *
 * States rendered:
 * - open → green pill "LIVE"
 * - connecting → amber blinking pill "CONNECTING"
 * - reconnecting → amber blinking pill "RECONNECTING"
 * - closed → red pill "OFFLINE"
 *
 * @module components/layout/ConnectionPill
 * @example
 * <ConnectionPill status={wsStatus} />
 */
import type { WsStatus } from '@/services/ws'

const STATUS_CONFIG: Record<WsStatus, { label: string; cls: string; pulse: boolean }> = {
  open: { label: 'LIVE', cls: 'bg-online/20 text-online border-online', pulse: false },
  connecting: { label: 'CONNECTING', cls: 'bg-starting/20 text-starting border-starting', pulse: true },
  reconnecting: { label: 'RECONNECTING', cls: 'bg-starting/20 text-starting border-starting', pulse: true },
  closed: { label: 'OFFLINE', cls: 'bg-offline/20 text-offline border-offline', pulse: false },
}

/**
 * Pill badge showing the WebSocket connection state.
 *
 * @param props.status - Current WS connection status.
 * @returns A styled pill element.
 */
export const ConnectionPill = ({ status }: { status: WsStatus }) => {
  const cfg = STATUS_CONFIG[status]
  return (
    <span
      className={`flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-mono font-semibold tracking-wider ${cfg.cls}`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${status === 'open' ? 'bg-online' : status === 'closed' ? 'bg-offline' : 'bg-starting'} ${cfg.pulse ? 'animate-pulse' : ''}`}
      />
      {cfg.label}
    </span>
  )
}
