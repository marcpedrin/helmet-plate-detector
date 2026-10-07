/**
 * Coloured badge showing a camera's lifecycle state.
 *
 * States rendered:
 * - ONLINE → green
 * - STARTING → amber
 * - OFFLINE / STOPPED → red
 *
 * @module components/cameras/CameraStatusBadge
 * @example
 * <CameraStatusBadge state={cam.state} />
 */
import type { CameraState } from '@/types/contracts'

const STATE_CONFIG: Record<CameraState, { label: string; cls: string }> = {
  ONLINE:   { label: 'ONLINE',   cls: 'bg-online/20 text-online border-online' },
  STARTING: { label: 'STARTING', cls: 'bg-starting/20 text-starting border-starting' },
  OFFLINE:  { label: 'OFFLINE',  cls: 'bg-offline/20 text-offline border-offline' },
  STOPPED:  { label: 'STOPPED',  cls: 'bg-offline/20 text-offline border-offline' },
}

/**
 * Small inline badge for camera lifecycle state.
 *
 * @param props.state - Camera lifecycle state.
 * @returns A styled badge span.
 */
export const CameraStatusBadge = ({ state }: { state: CameraState }) => {
  const { label, cls } = STATE_CONFIG[state] ?? STATE_CONFIG.OFFLINE
  return (
    <span className={`rounded border px-1.5 py-0.5 text-[10px] font-semibold font-mono tracking-wider ${cls}`}>
      {label}
    </span>
  )
}
