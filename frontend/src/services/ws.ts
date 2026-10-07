/**
 * WebSocket client for /ws/events with exponential-backoff reconnect.
 * @module services/ws
 */
import type { WsMessage } from '@/types/contracts'
import { API_BASE } from './api'

/** Connection state reported to `onStatus`. */
export type WsStatus = 'connecting' | 'open' | 'closed'

/** Minimum and maximum reconnect delays in milliseconds. */
export const BACKOFF_MIN_MS = 1_000
export const BACKOFF_MAX_MS = 10_000

/**
 * Compute the reconnect delay for a given attempt: 1 s, 2 s, 4 s, 8 s, then 10 s.
 * @param attempt Zero-based number of consecutive failed attempts.
 * @returns Delay in milliseconds.
 */
export function backoffDelay(attempt: number): number {
  return Math.min(BACKOFF_MAX_MS, BACKOFF_MIN_MS * 2 ** attempt)
}

/**
 * Build the ws:// or wss:// URL for /ws/events from {@link API_BASE} or the page origin.
 * @returns WebSocket URL.
 */
export function eventsUrl(): string {
  const base = API_BASE || window.location.origin
  return base.replace(/^http/, 'ws') + '/ws/events'
}

/**
 * Connect to /ws/events and keep reconnecting with backoff (1 s → 10 s) until closed.
 * @param onMessage Called with every parsed server message.
 * @param onStatus Called on every connection state change.
 * @returns A function that closes the connection permanently.
 */
export function connectEvents(onMessage: (msg: WsMessage) => void, onStatus: (s: WsStatus) => void): () => void {
  let ws: WebSocket | null = null
  let attempt = 0
  let timer: ReturnType<typeof setTimeout> | undefined
  let stopped = false

  const open = () => {
    onStatus('connecting')
    ws = new WebSocket(eventsUrl())
    ws.onopen = () => {
      attempt = 0
      onStatus('open')
    }
    ws.onmessage = (ev: MessageEvent<string>) => {
      try {
        onMessage(JSON.parse(ev.data) as WsMessage)
      } catch (err) {
        console.warn('bad WS message', err)
      }
    }
    ws.onclose = () => {
      onStatus('closed')
      if (stopped) return
      timer = setTimeout(open, backoffDelay(attempt++))
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
