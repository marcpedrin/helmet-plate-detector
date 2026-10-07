/**
 * Single-camera skeleton: large live stream + that camera's violations.
 * @module pages/CameraDetail
 */
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useLiveEvents } from '@/hooks/useLiveEvents'
import { apiUrl, getCamera, listViolations } from '@/services/api'
import type { CameraOut, ViolationOut } from '@/types/contracts'
import { formatPlate, formatTime } from '@/utils/format'

/**
 * Camera page.
 * @returns The camera detail page.
 */
export function CameraDetail() {
  const { id = '' } = useParams()
  const live = useLiveEvents()
  const [cam, setCam] = useState<CameraOut | null>(null)
  const [items, setItems] = useState<ViolationOut[]>([])

  useEffect(() => {
    const ctrl = new AbortController()
    getCamera(id, ctrl.signal).then(setCam).catch(() => {})
    listViolations({ camera_id: id, limit: 20 }, ctrl.signal).then((p) => setItems(p.items)).catch(() => {})
    return () => ctrl.abort()
  }, [id])

  if (!cam) return <p>Loading camera {id}…</p>
  const status = live.cameras[id] ?? cam
  const m = live.metrics[id]

  return (
    <div className="space-y-3">
      <h1 className="text-lg font-semibold">
        {cam.camera_id} · {cam.name} <span className="text-muted-foreground text-sm">({status.state})</span>
      </h1>
      {status.last_error && <p className="text-sm text-amber-500">{status.last_error}</p>}
      <img src={apiUrl(cam.stream_url)} alt={`${cam.name} live`} className="w-full max-w-5xl rounded bg-black" />
      <p className="text-sm">
        {m ? `${m.processing_fps.toFixed(1)} fps · ${m.riders_in_view} riders · tracks: ${m.tracks.map((t) => `#${t.track_id} ${t.helmet}`).join(', ')}` : 'no metrics yet'}
      </p>
      <ul className="text-sm">
        {items.map((v) => (
          <li key={v.id}>
            <Link to={`/violations/${v.id}`} className="underline">
              {formatTime(v.timestamp)} · {formatPlate(v.plate, v.plate_status)}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}
