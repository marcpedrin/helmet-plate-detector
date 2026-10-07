/**
 * Violations list skeleton (table, newest first).
 * @module pages/Violations
 */
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useLiveEvents } from '@/hooks/useLiveEvents'
import { listViolations } from '@/services/api'
import type { ViolationPage } from '@/types/contracts'
import { formatConfidence, formatPlate, formatTime } from '@/utils/format'

/**
 * Lists the latest 100 violations; refetches whenever a live violation event arrives.
 * @returns The violations page.
 */
export function Violations() {
  const { recent } = useLiveEvents()
  const [page, setPage] = useState<ViolationPage | null>(null)
  const latest = recent[0]

  useEffect(() => {
    const ctrl = new AbortController()
    listViolations({ limit: 100 }, ctrl.signal).then(setPage).catch(() => {})
    return () => ctrl.abort()
  }, [latest?.id, latest?.plate_status])

  return (
    <div>
      <h1 className="mb-2 text-lg font-semibold">Violations ({page?.total ?? '…'})</h1>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Time</TableHead>
            <TableHead>Camera</TableHead>
            <TableHead>Track</TableHead>
            <TableHead>Plate</TableHead>
            <TableHead>Helmet conf</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {page?.items.map((v) => (
            <TableRow key={v.id}>
              <TableCell>
                <Link to={`/violations/${v.id}`} className="underline">
                  {formatTime(v.timestamp)}
                </Link>
              </TableCell>
              <TableCell>{v.camera_id}</TableCell>
              <TableCell>#{v.track_id}</TableCell>
              <TableCell>{formatPlate(v.plate, v.plate_status)}</TableCell>
              <TableCell>{formatConfidence(v.helmet_confidence)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
