/**
 * Two recharts charts:
 * 1. Bar chart — violations per camera.
 * 2. Area chart — violations per minute over the last 30 minutes, computed client-side.
 *
 * Both charts are computed from the in-memory violations list; no additional API calls.
 *
 * @module components/stats/ViolationsChart
 * @example
 * <ViolationsChart violations={recent} stats={stats} />
 */
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { StatsOut, ViolationOut } from '@/types/contracts'

/** Props for {@link ViolationsChart}. */
export interface ViolationsChartProps {
  /** In-memory violations for time-series computation. */
  violations: ViolationOut[]
  /** Stats payload for per-camera bar data. */
  stats: StatsOut | null
}

/** Build last-30-min area chart data from violation timestamps. */
function buildTimeSeries(violations: ViolationOut[]): Array<{ time: string; count: number }> {
  const now = Date.now()
  // 30 one-minute buckets, oldest first
  const buckets: Record<number, number> = {}
  for (let i = 0; i < 30; i++) {
    buckets[i] = 0
  }
  for (const v of violations) {
    const ageMin = (now - new Date(v.timestamp).getTime()) / 60_000
    const bucket = Math.floor(ageMin)
    if (bucket >= 0 && bucket < 30) {
      buckets[29 - bucket] = (buckets[29 - bucket] ?? 0) + 1
    }
  }
  return Object.entries(buckets).map(([i, count]) => ({
    time: `-${29 - Number(i)}m`,
    count,
  }))
}

const CHART_COLORS = {
  bar: '#ef4444',
  area: '#ef4444',
  grid: 'rgba(255,255,255,0.06)',
  text: 'rgba(255,255,255,0.45)',
}

/**
 * Violations-per-camera bar chart and last-30-min area chart.
 * Both are computed from props — no additional fetch.
 *
 * @param props - See {@link ViolationsChartProps}.
 * @returns The charts element.
 */
export const ViolationsChart = ({ violations, stats }: ViolationsChartProps) => {
  const perCamera = stats
    ? Object.entries(stats.violations_by_camera).map(([cam, count]) => ({ cam, count }))
    : []

  const timeSeries = buildTimeSeries(violations)

  const axisStyle = { fontSize: 10, fill: CHART_COLORS.text }
  const tooltipStyle = {
    backgroundColor: '#1a1c23',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: 6,
    fontSize: 11,
    color: '#eef0f5',
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {/* Per-camera bar */}
      <div className="rounded-lg border border-border bg-card p-3">
        <p className="text-xs font-medium text-muted-foreground mb-3">Violations by Camera</p>
        {perCamera.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-muted-foreground/40 text-xs">No data yet</div>
        ) : (
          <ResponsiveContainer width="100%" height={120}>
            <BarChart data={perCamera} margin={{ top: 4, right: 4, bottom: 0, left: -16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} vertical={false} />
              <XAxis dataKey="cam" tick={axisStyle} />
              <YAxis allowDecimals={false} tick={axisStyle} />
              <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
              <Bar dataKey="count" fill={CHART_COLORS.bar} radius={[3, 3, 0, 0]} name="Violations" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Per-minute area */}
      <div className="rounded-lg border border-border bg-card p-3">
        <p className="text-xs font-medium text-muted-foreground mb-3">Violations / min (last 30 min)</p>
        <ResponsiveContainer width="100%" height={120}>
          <AreaChart data={timeSeries} margin={{ top: 4, right: 4, bottom: 0, left: -16 }}>
            <defs>
              <linearGradient id="viol-area-grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={CHART_COLORS.area} stopOpacity={0.3} />
                <stop offset="95%" stopColor={CHART_COLORS.area} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} vertical={false} />
            <XAxis
              dataKey="time"
              tick={axisStyle}
              interval={9}
              tickFormatter={(v) => v}
            />
            <YAxis allowDecimals={false} tick={axisStyle} />
            <Tooltip contentStyle={tooltipStyle} cursor={{ stroke: CHART_COLORS.area, strokeWidth: 1 }} />
            <Area
              type="monotone"
              dataKey="count"
              stroke={CHART_COLORS.area}
              strokeWidth={2}
              fill="url(#viol-area-grad)"
              name="Violations"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
