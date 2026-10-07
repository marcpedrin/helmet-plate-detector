/**
 * Compact violation card for the alert feed sidebar.
 *
 * Shows rider crop thumbnail, "NO HELMET" badge, PlateBadge, camera ID,
 * relative time, and helmet confidence.
 * Updates in-place when `violation_updated` arrives via the WS (plate fills in).
 * Clicking navigates to /violations/:id.
 *
 * @module components/violations/ViolationCard
 * @example
 * <ViolationCard violation={v} isNew={true} />
 */
import { useNavigate } from 'react-router-dom'
import { AlertTriangle, Clock } from 'lucide-react'
import { PlateBadge } from './PlateBadge'
import { apiUrl } from '@/services/api'
import { formatRelative, pct } from '@/utils/format'
import type { ViolationOut } from '@/types/contracts'

/** Props for {@link ViolationCard}. */
export interface ViolationCardProps {
  /** The violation data (may update when plate finalises). */
  violation: ViolationOut
  /** When true, applies the slide-in animation (for newly arrived violations). */
  isNew?: boolean
}

/**
 * Compact alert-feed violation card.
 *
 * @param props - See {@link ViolationCardProps}.
 * @returns The card element.
 */
export const ViolationCard = ({ violation: v, isNew }: ViolationCardProps) => {
  const navigate = useNavigate()

  return (
    <article
      role="button"
      tabIndex={0}
      aria-label={`Violation from ${v.camera_id} at ${v.timestamp}`}
      className={`flex gap-2.5 rounded-lg border border-border bg-card p-2.5 cursor-pointer hover:bg-accent/30 focus:outline-none focus:ring-1 focus:ring-ring transition-colors ${
        isNew ? 'slide-in' : ''
      }`}
      onClick={() => navigate(`/violations/${v.id}`)}
      onKeyDown={(e) => e.key === 'Enter' && navigate(`/violations/${v.id}`)}
    >
      {/* Rider crop thumbnail */}
      <div className="shrink-0 h-14 w-14 rounded overflow-hidden bg-muted">
        <img
          src={apiUrl(v.evidence.rider_crop_url)}
          alt="Rider evidence thumbnail"
          className="h-full w-full object-cover"
          onError={(e) => {
            ;(e.target as HTMLImageElement).src = ''
            ;(e.target as HTMLImageElement).style.display = 'none'
          }}
        />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 space-y-0.5">
        <div className="flex items-center gap-1.5">
          <span className="flex items-center gap-1 rounded-full bg-offline/20 border border-offline/40 text-offline px-1.5 py-0.5 text-[10px] font-semibold tracking-wide">
            <AlertTriangle className="h-2.5 w-2.5" aria-hidden />
            NO HELMET
          </span>
          <span className="text-xs text-muted-foreground font-mono">{v.camera_id}</span>
        </div>

        <PlateBadge plate={v.plate} status={v.plate_status} confidence={v.plate_confidence} />

        <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
          <span className="flex items-center gap-0.5">
            <Clock className="h-2.5 w-2.5" aria-hidden />
            {formatRelative(v.timestamp)}
          </span>
          <span>·</span>
          <span>helmet {pct(v.helmet_confidence)}</span>
          <span>·</span>
          <span className="font-mono">#{v.track_id}</span>
        </div>
      </div>
    </article>
  )
}
