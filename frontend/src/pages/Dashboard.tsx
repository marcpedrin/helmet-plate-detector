/**
 * Main dashboard page: StatsBar + 2-column layout (CameraGrid | AlertFeed) + collapsible ViolationsChart.
 * Live violations arrive via WebSocket; toasts notify on new events.
 *
 * WHY toasts: judges need an audio/visual cue without having to watch the feed.
 * Max 3 toasts visible to avoid flooding during busy demo periods.
 *
 * @module pages/DashboardPage
 * @example
 * // Registered in App.tsx at route "/"
 */
import { useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { AlertFeed } from '@/components/violations/AlertFeed'
import { CameraGrid } from '@/components/cameras/CameraGrid'
import { StatsBar } from '@/components/stats/StatsBar'
import { ViolationsChart } from '@/components/stats/ViolationsChart'
import { Button } from '@/components/ui/button'
import { useLiveEvents } from '@/hooks/useLiveEvents'
import { listCameras } from '@/services/api'
import type { CameraOut } from '@/types/contracts'

/**
 * Dashboard: live stats, 2×2 camera grid, alert feed sidebar, collapsible charts.
 *
 * @returns The dashboard page element.
 */
export function DashboardPage() {
  const { recent, stats, cameras: liveCams } = useLiveEvents()
  const [cameras, setCameras] = useState<CameraOut[]>([])
  const [chartOpen, setChartOpen] = useState(false)
  const prevTopRef = useRef<string | undefined>(undefined)
  const toastCountRef = useRef(0)

  useEffect(() => {
    const ctrl = new AbortController()
    listCameras(ctrl.signal).then(setCameras).catch(() => {})
    return () => ctrl.abort()
  }, [])

  // Merge live camera updates into REST-loaded list
  const mergedCameras = cameras.map((c) => ({ ...c, ...(liveCams[c.camera_id] ?? {}) }))

  // Toast on new violations (max 3 active)
  useEffect(() => {
    const latest = recent[0]
    if (!latest || latest.id === prevTopRef.current) return
    prevTopRef.current = latest.id

    // WHY max 3: avoid flooding the judge's screen during demo with rapid violations
    if (toastCountRef.current < 3) {
      toastCountRef.current++
      const camName = liveCams[latest.camera_id]?.name ?? latest.camera_id
      toast.error(`No helmet · ${camName} · #${latest.track_id}`, {
        description: `Track ${latest.track_id} — ${latest.plate_status === 'PENDING' ? 'plate reading…' : (latest.plate ?? 'no plate')}`,
        action: {
          label: 'View',
          onClick: () => { window.location.href = `/violations/${latest.id}` },
        },
        duration: 6000,
        onDismiss: () => { toastCountRef.current = Math.max(0, toastCountRef.current - 1) },
        onAutoClose: () => { toastCountRef.current = Math.max(0, toastCountRef.current - 1) },
      })
    }
  }, [recent, liveCams])

  return (
    <div className="flex flex-col gap-3">
      {/* KPI row */}
      <StatsBar stats={stats} />

      {/* Main 2-column layout */}
      <div className="grid gap-3 lg:grid-cols-[1fr_320px] xl:grid-cols-[1fr_360px]">
        {/* Left: cameras */}
        <div className="min-w-0 space-y-3">
          <CameraGrid cameras={mergedCameras as CameraOut[]} />

          {/* Collapsible charts */}
          <div className="rounded-lg border border-border bg-card">
            <button
              className="flex w-full items-center justify-between px-3 py-2.5 text-sm font-medium hover:bg-accent/20 transition-colors rounded-lg"
              onClick={() => setChartOpen((o) => !o)}
              aria-expanded={chartOpen}
              aria-controls="violations-chart"
            >
              <span>Violation Trends</span>
              {chartOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>
            {chartOpen && (
              <div id="violations-chart" className="px-3 pb-3">
                <ViolationsChart violations={recent} stats={stats} />
              </div>
            )}
          </div>
        </div>

        {/* Right: alert feed */}
        <div className="rounded-lg border border-border bg-card overflow-hidden" style={{ maxHeight: '75vh' }}>
          <AlertFeed violations={recent} />
        </div>
      </div>

      {/* Chart expand button for small screens */}
      <div className="lg:hidden">
        <Button
          variant="ghost"
          size="sm"
          className="w-full text-xs"
          onClick={() => setChartOpen((o) => !o)}
        >
          {chartOpen ? 'Hide' : 'Show'} violation trends
        </Button>
      </div>
    </div>
  )
}
