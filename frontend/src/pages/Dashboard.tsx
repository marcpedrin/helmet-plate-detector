/**
 * Dashboard skeleton: 2x2 live MJPEG grid + latest violations + stats.
 * Deliberately plain: Harish owns the real UI.
 * @module pages/Dashboard
 */
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useLiveEvents } from '@/hooks/useLiveEvents'
import { apiUrl, listCameras, listViolations } from '@/services/api'
import type { CameraOut, ViolationOut } from '@/types/contracts'
import { formatConfidence, formatPlate, formatTime, formatUptime } from '@/utils/format'

/**
 * Home page.
 * @returns The dashboard.
 */
export function Dashboard() {
  const live = useLiveEvents()
  const [cameras, setCameras] = useState<CameraOut[]>([])
  const [initial, setInitial] = useState<ViolationOut[]>([])

  useEffect(() => {
    const ctrl = new AbortController()
    listCameras(ctrl.signal).then(setCameras).catch(() => {})
    listViolations({ limit: 20 }, ctrl.signal).then((p) => setInitial(p.items)).catch(() => {})
    return () => ctrl.abort()
  }, [])

  const seen = new Set(live.recent.map((v) => v.id))
  const violations = [...live.recent, ...initial.filter((v) => !seen.has(v.id))].slice(0, 20)
  const stats = live.stats

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
      <section className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {cameras.map((cam) => {
          const state = live.cameras[cam.camera_id]?.state ?? cam.state
          const m = live.metrics[cam.camera_id]
          return (
            <Card key={cam.camera_id} className="gap-2 overflow-hidden py-2">
              <CardHeader className="px-3">
                <CardTitle className="flex items-center justify-between text-sm">
                  <Link to={`/cameras/${cam.camera_id}`}>
                    {cam.camera_id} · {cam.name}
                  </Link>
                  <Badge variant={state === 'ONLINE' ? 'secondary' : 'destructive'}>{state}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="px-3">
                <img src={apiUrl(cam.stream_url)} alt={`${cam.name} live`} className="aspect-video w-full rounded bg-black" />
                <p className="text-muted-foreground mt-1 text-xs">
                  {m ? `${m.processing_fps.toFixed(1)} fps · ${m.riders_in_view} riders` : 'no metrics yet'}
                </p>
              </CardContent>
            </Card>
          )
        })}
      </section>

      <aside className="space-y-4">
        <Card className="py-3">
          <CardContent className="grid grid-cols-2 gap-2 px-3 text-sm">
            <span>Violations</span>
            <b>{stats?.total_violations ?? '—'}</b>
            <span>Plates read</span>
            <b>{stats?.plates_read ?? '—'}</b>
            <span>Unreadable</span>
            <b>{stats?.plates_unreadable ?? '—'}</b>
            <span>Cameras online</span>
            <b>{stats ? `${stats.cameras_online}/${stats.cameras_total}` : '—'}</b>
            <span>Uptime</span>
            <b>{stats ? formatUptime(stats.uptime_s) : '—'}</b>
          </CardContent>
        </Card>

        <Card className="py-3">
          <CardHeader className="px-3">
            <CardTitle className="text-sm">Latest violations</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 px-3">
            {violations.length === 0 && <p className="text-muted-foreground text-sm">Waiting for violations…</p>}
            {violations.map((v) => (
              <Link key={v.id} to={`/violations/${v.id}`} className="hover:bg-muted flex items-center gap-2 rounded p-1">
                <img src={apiUrl(v.evidence.rider_crop_url)} alt="rider" className="h-12 w-12 rounded object-cover" />
                <div className="text-xs">
                  <div className="font-medium">
                    {v.camera_id} · {formatTime(v.timestamp)}
                  </div>
                  <div>
                    plate: <b>{formatPlate(v.plate, v.plate_status)}</b> · helmet conf {formatConfidence(v.helmet_confidence)}
                  </div>
                </div>
              </Link>
            ))}
          </CardContent>
        </Card>
      </aside>
    </div>
  )
}
