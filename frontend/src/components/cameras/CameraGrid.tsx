/**
 * Responsive 2×2 grid of {@link CameraCard} tiles.
 *
 * WHY we limit to 4 MJPEG streams at once: browsers allow only ~6 HTTP/1.1
 * connections per host. Streams never close their connection, so rendering more
 * than 4 would starve API/WebSocket calls.
 * See ADR: MJPEG connection cap.
 *
 * Layout: 2 columns on ≥ md, 1 column below 900 px.
 *
 * @module components/cameras/CameraGrid
 * @example
 * <CameraGrid cameras={cams} liveState={live} />
 */
import { CameraCard } from './CameraCard'
import { useLiveEvents } from '@/hooks/useLiveEvents'
import type { CameraOut } from '@/types/contracts'

/** Props for {@link CameraGrid}. */
export interface CameraGridProps {
  /** Cameras to display (usually 4; extras are silently truncated). */
  cameras: CameraOut[]
}

/**
 * 2×2 grid of camera tiles (max 4 MJPEG streams to avoid connection starvation).
 *
 * @param props - See {@link CameraGridProps}.
 * @returns The grid element.
 */
export const CameraGrid = ({ cameras }: CameraGridProps) => {
  const { cameras: liveCameras, recent } = useLiveEvents()

  // WHY .slice(0, 4): safety cap — never render more than 4 MJPEG streams
  const visible = cameras.slice(0, 4)

  return (
    <section
      aria-label="Live camera feeds"
      className="grid grid-cols-1 gap-3 md:grid-cols-2"
    >
      {visible.map((cam) => (
        <CameraCard
          key={cam.camera_id}
          camera={cam}
          liveCamera={liveCameras[cam.camera_id]}
          recentViolations={recent}
        />
      ))}
      {visible.length === 0 && (
        <p className="col-span-2 text-center text-muted-foreground py-12 text-sm">
          No cameras available. Is the backend running?
        </p>
      )}
    </section>
  )
}
