/**
 * Violations list page: ViolationTable with camera filter tabs and pagination.
 *
 * @module pages/ViolationsPage
 * @example
 * // Registered in App.tsx at route "/violations"
 */
import { ViolationTable } from '@/components/violations/ViolationTable'

/**
 * Violations list page.
 *
 * @returns The violations page element.
 */
export function Violations() {
  return (
    <div className="space-y-3">
      <div>
        <h1 className="text-lg font-semibold">Violations</h1>
        <p className="text-sm text-muted-foreground">All recorded no-helmet violations, newest first.</p>
      </div>
      <ViolationTable />
    </div>
  )
}
