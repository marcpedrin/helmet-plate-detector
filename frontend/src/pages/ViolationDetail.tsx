/**
 * Evidence viewer skeleton for one violation.
 * @module pages/ViolationDetail
 */
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useLiveEvents } from '@/hooks/useLiveEvents'
import { apiUrl, getViolation } from '@/services/api'
import type { ViolationOut } from '@/types/contracts'
import { formatConfidence, formatPlate, formatTime } from '@/utils/format'

/**
 * Shows the full frame, rider crop and plate crop of one violation; live-updates the plate.
 * @returns The violation detail page.
 */
export function ViolationDetail() {
  const { id = '' } = useParams()
  const { recent } = useLiveEvents()
  const [fetched, setFetched] = useState<ViolationOut | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const ctrl = new AbortController()
    getViolation(id, ctrl.signal)
      .then(setFetched)
      .catch((e: Error) => !ctrl.signal.aborted && setError(e.message))
    return () => ctrl.abort()
  }, [id])

  const v = recent.find((r) => r.id === id) ?? fetched
  if (error && !v) return <p>Could not load violation: {error}</p>
  if (!v) return <p>Loading…</p>

  return (
    <div className="space-y-3">
      <Link to="/violations" className="text-sm underline">
        ← all violations
      </Link>
      <h1 className="text-lg font-semibold">
        {v.violation} · {v.camera_id} · track #{v.track_id} · {formatTime(v.timestamp)}
      </h1>
      <p className="text-sm">
        Plate: <b>{formatPlate(v.plate, v.plate_status)}</b> ({v.plate_status}, {formatConfidence(v.plate_confidence)}) ·
        helmet confidence {formatConfidence(v.helmet_confidence)} · frame {v.frame_index}
      </p>
      <div className="grid gap-3 md:grid-cols-[2fr_1fr]">
        <img src={apiUrl(v.evidence.full_frame_url)} alt="full frame" className="w-full rounded" />
        <div className="space-y-3">
          <img src={apiUrl(v.evidence.rider_crop_url)} alt="rider crop" className="max-h-80 rounded" />
          {v.evidence.plate_crop_url && (
            <img src={apiUrl(v.evidence.plate_crop_url)} alt="plate crop" className="rounded" />
          )}
        </div>
      </div>
      <p className="text-muted-foreground text-xs">
        Prototype for demonstration. Detections are probabilistic and require human review; not admissible enforcement
        evidence.
      </p>
    </div>
  )
}
