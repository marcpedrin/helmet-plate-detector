/**
 * Violation detail page: evidence viewer + metadata + live plate finalisation.
 *
 * Live behaviour: when the WS pushes `violation_updated` with a finalised plate while
 * this page is open, the plate badge updates immediately without a page reload.
 *
 * Failure states:
 * - Loading: skeleton cards
 * - 404: friendly "not found" card with a back link
 * - Evidence 404: neutral "Image unavailable" placeholder (handled in EvidenceViewer)
 * - Plate UNREADABLE: "OCR: UNKNOWN" label
 *
 * @module pages/ViolationDetailPage
 * @example
 * // Registered in App.tsx at route "/violations/:id"
 */
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, AlertTriangle } from 'lucide-react'
import { EvidenceViewer } from '@/components/violations/EvidenceViewer'
import { PlateBadge } from '@/components/violations/PlateBadge'
import { Skeleton } from '@/components/ui/skeleton'
import { useLiveEvents } from '@/hooks/useLiveEvents'
import { ApiError, getViolation } from '@/services/api'
import type { ViolationOut } from '@/types/contracts'
import { formatTime, pct } from '@/utils/format'

/** One metadata row. */
const MetaRow = ({ label, value }: { label: string; value: React.ReactNode }) => (
  <div className="flex flex-wrap gap-1 justify-between border-b border-border py-2 text-sm last:border-0">
    <span className="text-muted-foreground">{label}</span>
    <span className="font-mono text-right">{value}</span>
  </div>
)

/**
 * Violation detail page with evidence viewer and live plate updates.
 *
 * @returns The violation detail page element.
 */
export function ViolationDetail() {
  const { id = '' } = useParams()
  const { recent } = useLiveEvents()
  const [fetched, setFetched] = useState<ViolationOut | null>(null)
  const [notFound, setNotFound] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true)
    setNotFound(false)
    const ctrl = new AbortController()
    getViolation(id, ctrl.signal)
      .then((v) => { setFetched(v); setLoading(false) })
      .catch((e: unknown) => {
        if (!ctrl.signal.aborted) {
          setNotFound(e instanceof ApiError && e.status === 404)
          setLoading(false)
        }
      })
    return () => ctrl.abort()
  }, [id])

  // Live override: the WS may have a more recent version (e.g. plate finalised)
  const liveVersion = recent.find((r) => r.id === id)
  const v = liveVersion ?? fetched

  // Not found state
  if (notFound && !v) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
        <AlertTriangle className="h-10 w-10 text-muted-foreground/40" aria-hidden />
        <div>
          <h1 className="text-base font-semibold">Violation not found</h1>
          <p className="text-sm text-muted-foreground mt-1 font-mono">{id}</p>
        </div>
        <Link to="/violations" className="text-sm underline text-muted-foreground hover:text-foreground">
          ← Back to all violations
        </Link>
      </div>
    )
  }

  // Loading state
  if (loading && !v) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-96" />
        <div className="grid gap-3 md:grid-cols-[2fr_1fr_1fr]">
          <Skeleton className="aspect-video rounded-lg" />
          <Skeleton className="aspect-video rounded-lg" />
          <Skeleton className="aspect-video rounded-lg" />
        </div>
      </div>
    )
  }

  if (!v) return null

  const cameraName = v.camera_id

  return (
    <div className="space-y-4 max-w-6xl mx-auto">
      {/* Header */}
      <div>
        <Link
          to="/violations"
          className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground mb-3"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          All violations
        </Link>
        <div className="flex flex-wrap items-center gap-3">
          <span className="flex items-center gap-1.5 rounded-full bg-offline/20 border border-offline/40 text-offline px-3 py-1 text-sm font-semibold">
            <AlertTriangle className="h-4 w-4" aria-hidden />
            No-helmet violation
          </span>
          <span className="text-muted-foreground text-sm">·</span>
          <span className="font-mono text-sm text-muted-foreground">{cameraName}</span>
          <span className="text-muted-foreground text-sm">·</span>
          <span className="text-sm text-muted-foreground">{formatTime(v.timestamp)}</span>
        </div>
      </div>

      {/* Evidence panels */}
      <EvidenceViewer violation={v} />

      {/* Details table */}
      <div className="rounded-lg border border-border bg-card">
        <div className="px-4 py-3 border-b border-border">
          <h2 className="text-sm font-semibold">Incident Details</h2>
        </div>
        <div className="px-4 divide-y divide-transparent">
          <MetaRow label="Camera" value={<span className="font-mono">{v.camera_id}</span>} />
          <MetaRow label="Track ID" value={<span className="font-mono">#{v.track_id}</span>} />
          <MetaRow label="Time (local)" value={<span className="font-mono">{formatTime(v.timestamp)}</span>} />
          <MetaRow label="Time (ISO UTC)" value={<span className="font-mono text-xs">{v.timestamp}</span>} />
          <MetaRow label="Helmet confidence" value={<span className="font-mono">{pct(v.helmet_confidence)}</span>} />
          <MetaRow
            label="Plate"
            value={<PlateBadge plate={v.plate} status={v.plate_status} confidence={v.plate_confidence} />}
          />
          <MetaRow label="Plate status" value={<span className="font-mono">{v.plate_status}</span>} />
          <MetaRow label="Frame index" value={<span className="font-mono">{v.frame_index.toLocaleString()}</span>} />
          <MetaRow label="Violation ID" value={<span className="font-mono text-xs break-all">{v.id}</span>} />
        </div>
      </div>

      {/* Disclaimer */}
      <p className="text-xs text-muted-foreground border border-border rounded-lg px-4 py-3 bg-muted/20">
        Prototype for demonstration. Detections are probabilistic and require human review;
        not admissible enforcement evidence. All processing is local.
      </p>
    </div>
  )
}
