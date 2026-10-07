/**
 * Small display formatters.
 * @module utils/format
 */
import type { PlateStatus } from '@/types/contracts'

/**
 * Format a 0..1 confidence as a percentage.
 * @param value Confidence, or null.
 * @returns e.g. `"87%"`, or `"—"` for null.
 */
export function formatConfidence(value: number | null | undefined): string {
  return value === null || value === undefined ? '—' : `${Math.round(value * 100)}%`
}

/**
 * Format an ISO timestamp as local time (HH:MM:SS).
 * @param iso ISO-8601 string.
 * @returns Local time string.
 */
export function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour12: false })
}

/**
 * Human-readable plate label.
 * @param plate Plate text (may be null).
 * @param status Plate status.
 * @returns Plate text when READ, otherwise a status label.
 */
export function formatPlate(plate: string | null, status: PlateStatus): string {
  if (status === 'READ' && plate) return plate
  return { PENDING: 'reading…', READ: '—', UNREADABLE: 'unreadable', NOT_DETECTED: 'no plate' }[status]
}

/**
 * Format seconds as `1h 02m`, `3m 04s` or `12s`.
 * @param seconds Duration in seconds.
 * @returns Compact duration.
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
