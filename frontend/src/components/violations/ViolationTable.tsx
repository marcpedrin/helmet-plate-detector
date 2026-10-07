/**
 * Violations table with camera filter tabs, pagination, and live-merge of WS items.
 *
 * Columns: Time, Camera, Track, Plate, Plate Status, Helmet conf, Evidence thumb.
 * Pagination: 25 items per page.
 * Camera filter: "All" + one tab per camera.
 *
 * @module components/violations/ViolationTable
 * @example
 * <ViolationTable />
 */
import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { PlateBadge } from './PlateBadge'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useLiveEvents } from '@/hooks/useLiveEvents'
import { listViolations } from '@/services/api'
import { apiUrl } from '@/services/api'
import type { ViolationOut, ViolationPage } from '@/types/contracts'
import { formatTime, pct } from '@/utils/format'

const PAGE_SIZE = 25

/**
 * Paginated violations table with camera filter tabs and live WS item merging.
 *
 * @returns The violations table element.
 */
export const ViolationTable = () => {
  const { cameras, recent } = useLiveEvents()
  const cameraIds = Object.keys(cameras).sort()

  const [cameraFilter, setCameraFilter] = useState<string>('all')
  const [page, setPage] = useState<ViolationPage | null>(null)
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(true)

  const fetchPage = useCallback(
    (off: number, camId?: string) => {
      setLoading(true)
      const ctrl = new AbortController()
      listViolations(
        { camera_id: camId !== 'all' ? camId : undefined, limit: PAGE_SIZE, offset: off },
        ctrl.signal,
      )
        .then((p) => { setPage(p); setLoading(false) })
        .catch(() => { setLoading(false) })
      return ctrl
    },
    [],
  )

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    const ctrl = fetchPage(offset, cameraFilter)
    return () => ctrl.abort()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cameraFilter, fetchPage])

  // Refetch when new live events arrive (only first page)
  const latestLive = recent[0]
  useEffect(() => {
    if (offset === 0) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      const ctrl = fetchPage(0, cameraFilter)
      return () => ctrl.abort()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [latestLive?.id, latestLive?.plate_status])

  const items: ViolationOut[] = page?.items ?? []
  const total = page?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1

  const goTo = (newOffset: number) => {
    setOffset(newOffset)
    fetchPage(newOffset, cameraFilter)
  }

  return (
    <div className="space-y-3">
      {/* Camera filter tabs */}
      <Tabs value={cameraFilter} onValueChange={(v) => { setCameraFilter(v); setOffset(0); }}>
        <TabsList className="h-8">
          <TabsTrigger value="all" className="text-xs px-3">All</TabsTrigger>
          {cameraIds.map((id) => (
            <TabsTrigger key={id} value={id} className="text-xs px-3 font-mono">{id}</TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {/* Table */}
      <div className="rounded-lg border border-border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent border-border">
              <TableHead className="text-xs">Time</TableHead>
              <TableHead className="text-xs">Camera</TableHead>
              <TableHead className="text-xs">Track</TableHead>
              <TableHead className="text-xs">Plate</TableHead>
              <TableHead className="text-xs">Status</TableHead>
              <TableHead className="text-xs">Helmet</TableHead>
              <TableHead className="text-xs">Evidence</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading && items.length === 0 ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i} className="border-border">
                  {Array.from({ length: 7 }).map((__, j) => (
                    <TableCell key={j}><div className="h-4 w-full rounded bg-muted animate-pulse" /></TableCell>
                  ))}
                </TableRow>
              ))
            ) : items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-muted-foreground py-12 text-sm">
                  No violations recorded yet.
                </TableCell>
              </TableRow>
            ) : (
              items.map((v) => (
                <TableRow key={v.id} className="border-border hover:bg-accent/20">
                  <TableCell className="font-mono text-xs">
                    <Link to={`/violations/${v.id}`} className="hover:text-foreground text-muted-foreground hover:underline">
                      {formatTime(v.timestamp)}
                    </Link>
                  </TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">{v.camera_id}</TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">#{v.track_id}</TableCell>
                  <TableCell>
                    <PlateBadge plate={v.plate} status={v.plate_status} confidence={v.plate_confidence} />
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground font-mono">{v.plate_status}</TableCell>
                  <TableCell className="text-xs font-mono text-muted-foreground">{pct(v.helmet_confidence)}</TableCell>
                  <TableCell>
                    <Link to={`/violations/${v.id}`}>
                      <img
                        src={apiUrl(v.evidence.rider_crop_url)}
                        alt="Rider evidence"
                        className="h-10 w-10 rounded object-cover border border-border hover:scale-110 transition-transform"
                        onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
                      />
                    </Link>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{total} total violations</span>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              disabled={currentPage <= 1}
              onClick={() => goTo(Math.max(0, offset - PAGE_SIZE))}
              aria-label="Previous page"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="px-2">Page {currentPage} / {totalPages}</span>
            <Button
              variant="ghost"
              size="sm"
              disabled={currentPage >= totalPages}
              onClick={() => goTo(offset + PAGE_SIZE)}
              aria-label="Next page"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
