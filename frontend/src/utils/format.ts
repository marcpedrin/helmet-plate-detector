/**
 * Small display formatters for the dashboard UI.
 *
 * @module utils/format
 * @example
 * import { formatPlate, formatTime, pct } from '@/utils/format'
 * formatPlate('KA01AB1234', 'READ') // → 'KA 01 AB 1234'
 * pct(0.934) // → '93%'
 */
import type { PlateStatus } from '@/types/contracts'

/**
 * Format a 0..1 confidence value as a percentage string.
 *
 * @param value - Confidence between 0 and 1, or null/undefined.
 * @returns e.g. `"87%"`, or `"—"` when null/undefined.
 * @example pct(0.934) // → '93%'
 */
export function pct(value: number | null | undefined): string {
  return value === null || value === undefined ? '—' : `${Math.round(value * 100)}%`
}

/** @deprecated Use {@link pct} – kept for backward-compat with existing skeleton. */
export const formatConfidence = pct

/**
 * Format an ISO-8601 UTC timestamp as local time (HH:mm:ss, 24-hour).
 *
 * @param iso - ISO-8601 UTC string.
 * @returns e.g. `"14:03:07"`.
 */
export function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour12: false })
}

/**
 * Format an ISO-8601 UTC timestamp as a human-readable relative string
 * (e.g. "just now", "2 min ago", "1 h ago").
 *
 * @param iso - ISO-8601 UTC string.
 * @returns Relative time description.
 */
export function formatRelative(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (diff < 10) return 'just now'
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  return `${Math.floor(diff / 3600)}h ago`
}

/**
 * Format an Indian vehicle registration plate with spaces.
 *
 * Rules applied (all case-insensitive, result is uppercase):
 *  - Old style `KA01AB1234` → `KA 01 AB 1234`
 *  - Delhi `DL3CAB1234` → `DL 3C AB 1234`
 *  - BH series `22BH1234AB` → `22 BH 1234 AB`
 *  - Unknown patterns → returned unchanged.
 *
 * @param text - Raw plate string (may be null).
 * @param status - Plate recognition status.
 * @returns Formatted plate or a status label when not READ.
 * @example
 * formatPlateFull('KA01AB1234') // → 'KA 01 AB 1234'
 * formatPlateFull('22BH1234AB') // → '22 BH 1234 AB'
 */
export function formatPlateFull(text: string): string {
  const t = text.trim().toUpperCase()

  // BH series: digits BH digits alpha (e.g. 22BH1234AB)
  const bh = t.match(/^(\d{2})(BH)(\d{4})([A-Z]{1,2})$/)
  if (bh) return `${bh[1]} ${bh[2]} ${bh[3]} ${bh[4]}`

  // Delhi-style: state (2 chars) + district (2 chars, may include digit) + series (2 alpha) + number (4 digits)
  // e.g. DL3CAB1234 → DL 3C AB 1234
  const dl = t.match(/^([A-Z]{2})(\d[A-Z0-9])([A-Z]{2})(\d{4})$/)
  if (dl) return `${dl[1]} ${dl[2]} ${dl[3]} ${dl[4]}`

  // Standard: state (2) + district (2 digits) + series (2 alpha) + number (4 digits)
  const std = t.match(/^([A-Z]{2})(\d{2})([A-Z]{1,3})(\d{4})$/)
  if (std) return `${std[1]} ${std[2]} ${std[3]} ${std[4]}`

  return t // unknown pattern — passthrough
}

/**
 * Human-readable plate label, applying {@link formatPlateFull} when READ.
 *
 * @param plate - Plate text (may be null).
 * @param status - Plate recognition status.
 * @returns Formatted plate when READ; otherwise a short status label.
 */
export function formatPlate(plate: string | null, status: PlateStatus): string {
  if (status === 'READ' && plate) return formatPlateFull(plate)
  return { PENDING: 'reading…', READ: '—', UNREADABLE: 'unreadable', NOT_DETECTED: 'no plate' }[status]
}

/**
 * Format seconds as a compact duration string: `"1h 02m"`, `"3m 04s"`, or `"12s"`.
 *
 * @param seconds - Duration in seconds (positive integer).
 * @returns Compact human-readable duration.
 */
export function formatUptime(seconds: number): string {
  const s = Math.floor(seconds)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const r = s % 60
  if (h) return `${h}h ${String(m).padStart(2, '0')}m`
  if (m) return `${m}m ${String(r).padStart(2, '0')}s`
  return `${r}s`
}
