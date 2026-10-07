/**
 * Live alert feed sidebar showing the latest 30 violations.
 *
 * Items slide in when new violations arrive from the WebSocket.
 * Updates in-place when `violation_updated` changes a plate status.
 * Empty state: "No violations yet. Monitoring 4 cameras".
 *
 * @module components/violations/AlertFeed
 * @example
 * <AlertFeed violations={recent} />
 */
import { useEffect, useRef, useState } from 'react'
import { Bell } from 'lucide-react'
import { ViolationCard } from './ViolationCard'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { ViolationOut } from '@/types/contracts'

/** Maximum number of items shown in the alert feed. */
const FEED_MAX = 30

/** Props for {@link AlertFeed}. */
export interface AlertFeedProps {
  /** Latest violations, newest first. */
  violations: ViolationOut[]
}

/**
 * Scrollable live violation feed with new-item animation.
 * Shows the most recent {@link FEED_MAX} violations.
 *
 * @param props - See {@link AlertFeedProps}.
 * @returns The alert feed element.
 */
export const AlertFeed = ({ violations }: AlertFeedProps) => {
  const visible = violations.slice(0, FEED_MAX)
  const [newIds, setNewIds] = useState<Set<string>>(new Set())
  const prevTopRef = useRef<string | undefined>(undefined)

  // Track which IDs are newly arrived to animate slide-in
  useEffect(() => {
    const latestId = violations[0]?.id
    if (latestId && latestId !== prevTopRef.current) {
      prevTopRef.current = latestId
      setNewIds((prev) => {
        const next = new Set(prev)
        next.add(latestId)
        // Clear after animation completes
        setTimeout(() => setNewIds((s) => { const n = new Set(s); n.delete(latestId); return n }), 600)
        return next
      })
    }
  }, [violations])

  return (
    <aside aria-label="Live violation feed" className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-border shrink-0">
        <Bell className="h-4 w-4 text-offline" aria-hidden />
        <span className="text-sm font-semibold">Alert Feed</span>
        {visible.length > 0 && (
          <span className="ml-auto rounded-full bg-offline text-white text-[10px] font-bold px-1.5 py-0.5 min-w-[18px] text-center">
            {visible.length}
          </span>
        )}
      </div>

      {/* List */}
      <ScrollArea className="flex-1 custom-scrollbar">
        <div className="space-y-1.5 p-2">
          {visible.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-12 text-center">
              <Bell className="h-8 w-8 text-muted-foreground/30" />
              <p className="text-sm text-muted-foreground">No violations yet.</p>
              <p className="text-xs text-muted-foreground/70">Monitoring 4 cameras</p>
            </div>
          ) : (
            visible.map((v) => (
              <ViolationCard
                key={v.id}
                violation={v}
                isNew={newIds.has(v.id)}
              />
            ))
          )}
        </div>
      </ScrollArea>
    </aside>
  )
}
