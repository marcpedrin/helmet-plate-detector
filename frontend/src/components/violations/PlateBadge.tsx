/**
 * Styled number-plate badge matching Indian registration plate appearance.
 *
 * States rendered:
 * - READ → white-background plate with black monospace text, "IND" micro-label, formatted text
 * - PENDING → skeleton "Reading plate…"
 * - UNREADABLE → muted "OCR: UNKNOWN"
 * - NOT_DETECTED → muted "Plate not visible"
 *
 * @module components/violations/PlateBadge
 * @example
 * <PlateBadge plate="KA01AB1234" status="READ" confidence={0.93} />
 * <PlateBadge plate={null} status="PENDING" confidence={null} />
 */
import { Skeleton } from '@/components/ui/skeleton'
import { formatPlateFull } from '@/utils/format'
import type { PlateStatus } from '@/types/contracts'

/** Props for {@link PlateBadge}. */
export interface PlateBadgeProps {
  /** Plate text (may be null when not yet read). */
  plate: string | null
  /** Current plate recognition status. */
  status: PlateStatus
  /** Confidence 0–1 (optional, shown when READ). */
  confidence?: number | null
}

/**
 * Indian-style number plate badge with four recognition states.
 *
 * @param props - See {@link PlateBadgeProps}.
 * @returns A styled plate element.
 */
export const PlateBadge = ({ plate, status, confidence }: PlateBadgeProps) => {
  if (status === 'READ' && plate) {
    return (
      <span className="plate-badge" data-testid="plate-read">
        <span className="ind-label">IND</span>
        {formatPlateFull(plate)}
        {confidence != null && (
          <span className="ml-1 text-[10px] text-gray-500 font-normal">{Math.round(confidence * 100)}%</span>
        )}
      </span>
    )
  }
  if (status === 'PENDING') {
    return (
      <span className="flex items-center gap-1.5 text-xs text-muted-foreground" data-testid="plate-pending">
        <Skeleton className="h-3.5 w-24 rounded" />
        <span>Reading plate…</span>
      </span>
    )
  }
  if (status === 'UNREADABLE') {
    return (
      <span className="text-xs text-muted-foreground font-mono" data-testid="plate-unreadable">
        OCR: UNKNOWN
      </span>
    )
  }
  // NOT_DETECTED
  return (
    <span className="text-xs text-muted-foreground" data-testid="plate-not-detected">
      Plate not visible
    </span>
  )
}
