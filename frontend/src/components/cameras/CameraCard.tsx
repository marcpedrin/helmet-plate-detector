/**
 * Individual camera card with live MJPEG stream, status badge, and metrics strip.
 *
 * States rendered:
 * - ONLINE → live <img> MJPEG stream
 * - STARTING → "CONNECTING…" skeleton overlay
 * - OFFLINE or img onError → "CAMERA OFFLINE" overlay + last_error text, auto-retries every 3 s
 *
 * WHY img src="" on unmount: browsers keep an HTTP/1.1 connection open for MJPEG indefinitely.
 * Clearing src closes the connection so it doesn't starve API calls (connection cap is ~6).
 * See ADR: MJPEG <img> vs canvas/WebRTC.
 *
 * WHY 3 s retry: short enough to recover quickly when a camera comes back online,
 * not so short as to cause a reconnect storm.
 *
 * Red pulse appears for 5 s after a violation arrives from this camera.
 *
 * @module components/cameras/CameraCard
 * @example
 * <CameraCard camera={cam} liveState={live} recentViolations={[v1]} />
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertTriangle, VideoOff } from 'lucide-react'
import { CameraStatusBadge } from './CameraStatusBadge'
import { Skeleton } from '@/components/ui/skeleton'
import { apiUrl } from '@/services/api'
import type { CameraOut, ViolationOut } from '@/types/contracts'
import type { LiveCamera } from '@/hooks/useLiveEvents'

/** Props for {@link CameraCard}. */
export interface CameraCardProps {
  /** Static + live camera data. */
  camera: CameraOut
  /** Live-merged camera state (from context); if undefined, falls back to `camera`. */
  liveCamera?: LiveCamera
  /** Recent violations (all cameras) — used to detect violations from this camera in last 5 s. */
  recentViolations: ViolationOut[]
}

/**
 * 16:9 camera tile with MJPEG stream, status badge, metrics footer, and offline handling.
 * Clicking the tile navigates to /cameras/:id.
 *
 * @param props - See {@link CameraCardProps}.
 * @returns The camera card element.
 */
export const CameraCard = ({ camera, liveCamera, recentViolations }: CameraCardProps) => {
  const navigate = useNavigate()
  const merged = liveCamera ?? camera
  const state = merged.state
  const imgRef = useRef<HTMLImageElement>(null)
  const retryTimerRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined)
  const [imgError, setImgError] = useState(false)

  const [hasRecentViolation, setHasRecentViolation] = useState(false)

  // Detect if a violation from this camera arrived in the last 5 s
  useEffect(() => {
    const isRecent = recentViolations.some((v) => {
      if (v.camera_id !== camera.camera_id) return false
      const age = Date.now() - new Date(v.timestamp).getTime()
      return age < 5_000
    })
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setHasRecentViolation(isRecent)
  }, [recentViolations, camera.camera_id])

  const streamSrc = apiUrl(camera.stream_url)

  // Retry handler: re-sets the src with a cache-busting timestamp
  const retry = useCallback(() => {
    if (!imgRef.current) return
    imgRef.current.src = `${streamSrc}?t=${Date.now()}`
    setImgError(false)
  }, [streamSrc])

  // Start retry interval when OFFLINE or image error occurs
  useEffect(() => {
    const isDown = state === 'OFFLINE' || state === 'STOPPED' || imgError
    if (isDown) {
      retryTimerRef.current = setInterval(retry, 3_000)
    } else {
      clearInterval(retryTimerRef.current)
    }
    return () => clearInterval(retryTimerRef.current)
  }, [state, imgError, retry])

  // WHY: clear src on unmount to close the MJPEG HTTP connection
  useEffect(() => {
    const img = imgRef.current
    return () => {
      if (img) {
        img.src = ''
      }
    }
  }, [])

  const isOffline = state === 'OFFLINE' || state === 'STOPPED'
  const isStarting = state === 'STARTING'
  const showOfflineOverlay = isOffline || imgError

  return (
    <article
      role="button"
      tabIndex={0}
      aria-label={`Camera ${camera.camera_id}: ${camera.name}, ${state}`}
      className={`relative overflow-hidden rounded-lg border border-border bg-card cursor-pointer transition-all hover:border-border/80 focus:outline-none focus:ring-2 focus:ring-ring ${
        hasRecentViolation ? 'violation-glow border-offline/60' : ''
      }`}
      onClick={() => navigate(`/cameras/${camera.camera_id}`)}
      onKeyDown={(e) => e.key === 'Enter' && navigate(`/cameras/${camera.camera_id}`)}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border">
        <div className="flex items-center gap-2 min-w-0">
          <span className="font-mono text-xs text-muted-foreground shrink-0">{camera.camera_id}</span>
          <span className="text-xs font-medium truncate">{camera.name}</span>
          {camera.location && (
            <span className="text-xs text-muted-foreground truncate hidden sm:block">· {camera.location}</span>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {hasRecentViolation && <span className="pulse-dot" title="Recent violation" />}
          <CameraStatusBadge state={state} />
        </div>
      </div>

      {/* Stream area */}
      <div className="stream-wrapper">
        {/* MJPEG img — always rendered but hidden behind overlay when offline */}
        {!isStarting && (
          <img
            ref={imgRef}
            src={streamSrc}
            alt={`${camera.name} live feed`}
            className={showOfflineOverlay ? 'opacity-10' : ''}
            onError={() => setImgError(true)}
            onLoad={() => setImgError(false)}
          />
        )}

        {/* STARTING skeleton */}
        {isStarting && (
          <div className="stream-overlay">
            <Skeleton className="absolute inset-0 rounded-none" />
            <span className="relative z-10 text-xs text-muted-foreground font-mono animate-pulse">CONNECTING…</span>
          </div>
        )}

        {/* OFFLINE overlay */}
        {showOfflineOverlay && (
          <div className="stream-overlay" data-testid="offline-overlay">
            <VideoOff className="h-8 w-8 text-offline" aria-hidden />
            <span className="text-sm font-semibold text-offline">CAMERA OFFLINE</span>
            {merged.last_error && (
              <span className="text-xs text-muted-foreground text-center px-4 max-w-full truncate">{merged.last_error}</span>
            )}
          </div>
        )}

        {/* Violation indicator overlay */}
        {hasRecentViolation && !showOfflineOverlay && (
          <div className="absolute top-2 right-2 z-10">
            <span className="flex items-center gap-1 rounded-full bg-offline/80 px-2 py-0.5 text-[10px] text-white font-semibold">
              <AlertTriangle className="h-3 w-3" aria-hidden />
              VIOLATION
            </span>
          </div>
        )}
      </div>

      {/* Metrics footer */}
      <div className="flex items-center gap-3 px-3 py-1.5 text-xs text-muted-foreground">
        {liveCamera !== undefined ? (
          <>
            <span>
              <span className="font-mono text-foreground">{liveCamera.processing_fps.toFixed(1)}</span>
              {' '}fps AI
            </span>
            <span className="text-border">·</span>
            <span>
              <span className="font-mono text-foreground">{liveCamera.riders_in_view}</span>
              {' '}riders
            </span>
          </>
        ) : (
          <span className="text-muted-foreground/50">no metrics yet</span>
        )}
        {merged.frame_index > 0 && (
          <>
            <span className="text-border">·</span>
            <span className="font-mono">frame {merged.frame_index.toLocaleString()}</span>
          </>
        )}
      </div>
    </article>
  )
}
