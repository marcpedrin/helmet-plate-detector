/**
 * KPI stats bar: Total violations, Plates read (n + %), Riders in view, Cameras online, Uptime.
 * Data comes from the live WebSocket stats payload.
 *
 * @module components/stats/StatsBar
 * @example
 * <StatsBar stats={stats} />
 */
import { Activity, Camera, Clock, Shield } from 'lucide-react'
import { formatUptime } from '@/utils/format'
import type { StatsOut } from '@/types/contracts'

/** One KPI tile. */
const KpiTile = ({
  icon: Icon,
  label,
  value,
  sub,
  accent,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string | number
  sub?: string
  accent?: boolean
}) => (
  <div className={`kpi-tile flex gap-3 items-start ${accent ? 'border-offline/40' : ''}`}>
    <div className={`mt-0.5 rounded-md p-1.5 ${accent ? 'bg-offline/15 text-offline' : 'bg-accent text-muted-foreground'}`}>
      <Icon className="h-4 w-4" aria-hidden />
    </div>
    <div className="min-w-0">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={`text-lg font-semibold font-mono leading-tight ${accent ? 'text-offline' : 'text-foreground'}`}>
        {value}
      </p>
      {sub && <p className="text-[10px] text-muted-foreground">{sub}</p>}
    </div>
  </div>
)

/** Props for {@link StatsBar}. */
export interface StatsBarProps {
  /** Latest stats; null while loading. */
  stats: StatsOut | null
}

/**
 * Row of KPI tiles showing key dashboard metrics.
 * Shows "—" for all values while stats are loading.
 *
 * @param props - See {@link StatsBarProps}.
 * @returns The stats bar element.
 */
export const StatsBar = ({ stats }: StatsBarProps) => {
  const total = stats?.total_violations ?? '—'
  const platesRead = stats?.plates_read ?? 0
  const finalised = (stats?.plates_read ?? 0) + (stats?.plates_unreadable ?? 0)
  const platePct = finalised > 0 ? `${Math.round((platesRead / finalised) * 100)}%` : '—'
  const riders = stats?.riders_in_view ?? '—'
  const cameras = stats ? `${stats.cameras_online}/${stats.cameras_total}` : '—'
  const uptime = stats ? formatUptime(stats.uptime_s) : '—'

  return (
    <div
      aria-label="Dashboard statistics"
      className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5"
    >
      <KpiTile icon={Shield} label="Total Violations" value={total} accent={typeof total === 'number' && total > 0} />
      <KpiTile icon={Shield} label="Plates Read" value={platesRead} sub={`${platePct} of finalised`} />
      <KpiTile icon={Activity} label="Riders in View" value={riders} sub="live count" />
      <KpiTile icon={Camera} label="Cameras Online" value={cameras} />
      <KpiTile icon={Clock} label="Uptime" value={uptime} />
    </div>
  )
}
