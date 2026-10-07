/**
 * Single-camera detail page: large stream, camera details, recent violations.
 *
 * Failure states:
 * - Camera loading: skeleton
 * - Camera OFFLINE: large overlay in stream area
 * - Unknown camera ID: friendly 404 card
 *
 * @module pages/CameraDetailPage
 * @example
 * // Registered in App.tsx at route "/cameras/:id"
 */
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, AlertTriangle, VideoOff } from 'lucide-react'
import { CameraStatusBadge } from '@/components/cameras/CameraStatusBadge'
import { PlateBadge } from '@/components/violations/PlateBadge'
import { Skeleton } from '@/components/ui/skeleton'
import { useLiveEvents } from '@/hooks/useLiveEvents'
import { ApiError, apiUrl, getCamera, listViolations } from '@/services/api'
import type { CameraOut, ViolationOut } from '@/types/contracts'
import { formatRelative, formatTime, pct } from '@/utils/format'

/**
 * Camera focus page: full-width live stream + camera metadata + recent violations list.
 *
 * @returns The camera detail page element.
 */
export function CameraDetail() {
  const { id = '' } = useParams()
  const { cameras: liveCams, metrics: liveMetrics } = useLiveEvents()
  const [cam, setCam] = useState<CameraOut | null>(null)
  const [violations, setViolations] = useState<ViolationOut[]>([])
  const [notFound, setNotFound] = useState(false)
  const [loading, setLoading] = useState(true)
  const [imgError, setImgError] = useState(false)

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true)
    const ctrl = new AbortController()
    Promise.all([
      getCamera(id, ctrl.signal),
      listViolations({ camera_id: id, limit: 20 }, ctrl.signal),
    ])
      .then(([camera, page]) => {
        setCam(camera)
        setViolations(page.items)
        setLoading(false)
      })
      .catch((e: unknown) => {
        if (!ctrl.signal.aborted) {
          setNotFound(e instanceof ApiError && e.status === 404)
          setLoading(false)
        }
      })
    return () => ctrl.abort()
  }, [id])

  if (notFound && !cam) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
        <AlertTriangle className="h-10 w-10 text-muted-foreground/40" />
        <div>
          <h1 className="text-base font-semibold">Camera not found</h1>
          <p className="text-sm text-muted-foreground font-mono">{id}</p>
        </div>
        <Link to="/" className="text-sm underline text-muted-foreground hover:text-foreground">← Dashboard</Link>
      </div>
    )
  }

  if (loading && !cam) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="w-full aspect-video rounded-lg max-w-4xl" />
      </div>
    )
  }

  if (!cam) return null

  const live = liveCams[id] ?? cam
  const metrics = liveMetrics[id]
  const isOffline = live.state === 'OFFLINE' || live.state === 'STOPPED'
  const showOverlay = isOffline || imgError

  return (
    <div className="space-y-4 max-w-6xl mx-auto">
      {/* Header */}
      <div>
        <Link to="/" className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground mb-2">
          <ArrowLeft className="h-3.5 w-3.5" />
          Dashboard
        </Link>
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold">{cam.name}</h1>
          <span className="font-mono text-sm text-muted-foreground">{cam.camera_id}</span>
          <CameraStatusBadge state={live.state} />
        </div>
        {cam.location && <p className="text-sm text-muted-foreground">{cam.location}</p>}
        {live.last_error && <p className="text-xs text-starting">{live.last_error}</p>}
      </div>

      {/* Stream */}
      <div className="relative w-full aspect-video max-w-4xl rounded-lg overflow-hidden bg-black border border-border">
        <img
          src={apiUrl(cam.stream_url)}
          alt={`${cam.name} live feed`}
          className={`w-full h-full object-cover ${showOverlay ? 'opacity-10' : ''}`}
          onError={() => setImgError(true)}
          onLoad={() => setImgError(false)}
        />
        {showOverlay && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
            <VideoOff className="h-10 w-10 text-offline" />
            <span className="text-offline font-semibold">CAMERA OFFLINE</span>
            {live.last_error && <span className="text-xs text-muted-foreground">{live.last_error}</span>}
          </div>
        )}

        {/* Metrics overlay */}
        {metrics && !showOverlay && (
          <div className="absolute bottom-0 left-0 right-0 bg-black/60 px-3 py-1.5 flex gap-4 text-xs text-white font-mono">
            <span>{metrics.processing_fps.toFixed(1)} fps AI</span>
            <span>·</span>
            <span>{metrics.riders_in_view} riders</span>
            <span>·</span>
            <span>frame {live.frame_index.toLocaleString()}</span>
          </div>
        )}
      </div>

      {/* Recent violations */}
      <div className="rounded-lg border border-border bg-card">
        <div className="px-4 py-3 border-b border-border">
          <h2 className="text-sm font-semibold">Recent Violations from {cam.camera_id}</h2>
        </div>
        <div className="divide-y divide-border">
          {violations.length === 0 ? (
            <p className="px-4 py-8 text-center text-sm text-muted-foreground">No violations recorded from this camera.</p>
          ) : (
            violations.map((v) => (
              <Link
                key={v.id}
                to={`/violations/${v.id}`}
                className="flex items-center gap-3 px-4 py-3 hover:bg-accent/20 transition-colors"
              >
                <img
                  src={apiUrl(v.evidence.rider_crop_url)}
                  alt="Rider"
                  className="h-12 w-12 rounded object-cover border border-border shrink-0"
                  onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
                />
                <div className="flex-1 min-w-0 space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-muted-foreground">{formatTime(v.timestamp)}</span>
                    <span className="text-xs text-muted-foreground">·</span>
                    <span className="text-xs text-muted-foreground">{formatRelative(v.timestamp)}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <PlateBadge plate={v.plate} status={v.plate_status} />
                    <span className="text-xs text-muted-foreground">helmet {pct(v.helmet_confidence)}</span>
                  </div>
                </div>
                <span className="text-xs text-muted-foreground font-mono shrink-0">#{v.track_id}</span>
              </Link>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
