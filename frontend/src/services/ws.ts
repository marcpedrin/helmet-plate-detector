/**
 * WebSocket client for /ws/events with exponential-backoff reconnect and jitter.
 *
 * The backoff sequence is: 1 s → 2 s → 4 s → 8 s → 10 s (capped), with
 * ±20 % jitter to avoid thundering-herd reconnects from many browser tabs.
 *
 * WHY reconnecting status is "reconnecting" not "closed": the UI shows a
 * RECONNECTING banner (amber) while retrying, and only "closed" when
 * the caller explicitly calls the returned close() function.
 *
 * @module services/ws
 * @example
 * const close = connectEvents(
 *   (msg) => dispatch(msg),
 *   (status) => setStatus(status),
 * )
 * // later:
 * close()
 */
import type { WsMessage } from '@/types/contracts'
import { API_BASE } from './api'

/**
 * Connection state reported to the `onStatus` callback.
 * - `"connecting"` — first attempt or reconnect in progress
 * - `"open"` — connected and receiving messages
 * - `"reconnecting"` — connection lost, will retry with backoff
 * - `"closed"` — permanently closed by caller
 */
export type WsStatus = 'connecting' | 'open' | 'reconnecting' | 'closed'

/** Minimum reconnect delay in milliseconds (1 s). */
export const BACKOFF_MIN_MS = 1_000
/** Maximum reconnect delay in milliseconds (10 s). */
export const BACKOFF_MAX_MS = 10_000
/** Jitter fraction applied to each backoff delay (±20 %). */
export const BACKOFF_JITTER = 0.2

/**
 * Compute the reconnect delay for a given attempt index.
 * Formula: clamp(1000 × 2^attempt, 1000, 10000) ± jitter.
 *
 * @param attempt - Zero-based count of consecutive failed attempts.
 * @returns Delay in milliseconds (includes jitter).
 * @example backoffDelay(0) // ~1000, backoffDelay(3) // ~8000
 */
export function backoffDelay(attempt: number): number {
  const base = Math.min(BACKOFF_MAX_MS, BACKOFF_MIN_MS * 2 ** attempt)
  // WHY jitter: prevents all reconnecting clients from hitting the server at once.
  const jitter = base * BACKOFF_JITTER * (Math.random() * 2 - 1)
  return Math.max(BACKOFF_MIN_MS / 2, Math.round(base + jitter))
}

/**
 * Build the `ws://` or `wss://` URL for `/ws/events` from {@link API_BASE} or the page origin.
 * When API_BASE is empty (same-origin FastAPI build), uses `window.location.origin`.
 *
 * @returns Full WebSocket URL.
 */
export function eventsUrl(): string {
  const base = API_BASE || window.location.origin
  return base.replace(/^http/, 'ws') + '/ws/events'
}

/**
 * Connect to `/ws/events` and keep reconnecting with exponential backoff until explicitly closed.
 *
 * Side effects: opens WebSocket, sets timers on close/error, calls callbacks.
 * All state is local to the closure — safe to call multiple times (each call is independent).
 *
 * @param onMessage - Called with every successfully parsed server message.
 * @param onStatus - Called on every connection state change.
 * @returns A `close()` function that permanently stops reconnecting.
 */
export function connectEvents(
  onMessage: (msg: WsMessage) => void,
  onStatus: (s: WsStatus) => void,
): () => void {
  let ws: WebSocket | null = null
  let attempt = 0
  let timer: ReturnType<typeof setTimeout> | undefined
  let stopped = false

  const open = () => {
    if (stopped) return
    onStatus(attempt === 0 ? 'connecting' : 'reconnecting')
    ws = new WebSocket(eventsUrl())

    ws.onopen = () => {
      attempt = 0
      onStatus('open')
    }

    ws.onmessage = (ev: MessageEvent<string>) => {
      try {
        onMessage(JSON.parse(ev.data) as WsMessage)
      } catch (err) {
        console.warn('[ws] bad message', err)
      }
    }

    ws.onclose = () => {
      if (stopped) {
        onStatus('closed')
        return
      }
      onStatus('reconnecting')
      const delay = backoffDelay(attempt++)
      timer = setTimeout(open, delay)
    }

    ws.onerror = () => ws?.close()
  }

  open()

  return () => {
    stopped = true
    clearTimeout(timer)
    ws?.close()
  }
}
