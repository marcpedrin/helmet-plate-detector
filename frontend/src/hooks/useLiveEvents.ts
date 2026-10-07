/**
 * Live state from /ws/events, shared through React context.
 *
 * Architecture:
 *   WS messages → {@link applyMessage} pure reducer → React state → context → hooks
 *
 * On every (re)connect the provider refetches cameras, violations and stats
 * to fill any gap caused by the disconnection.
 *
 * WHY pure reducer: makes the state logic unit-testable without React or a
 * real WebSocket. Tests import `applyMessage` directly.
 *
 * Wrap the app in {@link LiveEventsProvider}; read with {@link useLiveEvents}.
 *
 * @module hooks/useLiveEvents
 * @example
 * // In a component:
 * const { status, cameras, recent, stats } = useLiveEvents()
 */
import {
  createContext,
  createElement,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { listCameras, listViolations, getStats } from '@/services/api'
import { connectEvents, type WsStatus } from '@/services/ws'
import type { CameraMetricsMsg, CameraOut, HelloMsg, StatsOut, TrackOverlay, ViolationOut, WsMessage } from '@/types/contracts'

/** Maximum number of recent violations kept in memory. */
export const MAX_RECENT = 200

/**
 * Extended camera state that also holds live track overlays from camera_metrics messages.
 */
export type LiveCamera = CameraOut & { tracks: TrackOverlay[] }

/**
 * Everything the UI needs from the realtime stream.
 * All fields are replaced atomically (spread update) so components re-render predictably.
 */
export interface LiveState {
  /** WebSocket connection status. */
  status: WsStatus
  /** Payload of the initial `hello` message (contains mode and version). */
  hello: HelloMsg | null
  /** Live camera states, keyed by camera_id. Merges camera_status + camera_metrics. */
  cameras: Record<string, LiveCamera>
  /** Latest camera metrics, keyed by camera_id (≤ 2 Hz per camera). */
  metrics: Record<string, CameraMetricsMsg>
  /** Recent violations, newest first, capped at {@link MAX_RECENT}. Updated in-place on violation_updated. */
  recent: ViolationOut[]
  /** Latest stats payload. */
  stats: StatsOut | null
}

const initialState: LiveState = {
  status: 'connecting',
  hello: null,
  cameras: {},
  metrics: {},
  recent: [],
  stats: null,
}

/**
 * Pure reducer applying one server message to the live state.
 * Exported for unit tests; do not call from components — use the context hook instead.
 *
 * @param state - Current live state.
 * @param msg - Parsed server message.
 * @returns Next live state (new object reference on any change).
 */
export function applyMessage(state: LiveState, msg: WsMessage): LiveState {
  switch (msg.type) {
    case 'hello':
      return { ...state, hello: msg.data }

    case 'camera_status': {
      const existing = state.cameras[msg.data.camera_id]
      return {
        ...state,
        cameras: {
          ...state.cameras,
          [msg.data.camera_id]: { ...msg.data, tracks: existing?.tracks ?? [] },
        },
      }
    }

    case 'camera_metrics': {
      const existing = state.cameras[msg.data.camera_id]
      return {
        ...state,
        metrics: { ...state.metrics, [msg.data.camera_id]: msg.data },
        cameras: {
          ...state.cameras,
          [msg.data.camera_id]: existing
            ? { ...existing, processing_fps: msg.data.processing_fps, riders_in_view: msg.data.riders_in_view, tracks: msg.data.tracks }
            : { ...(state.cameras[msg.data.camera_id] ?? ({} as LiveCamera)), processing_fps: msg.data.processing_fps, riders_in_view: msg.data.riders_in_view, tracks: msg.data.tracks },
        },
      }
    }

    case 'violation_created':
    case 'violation_updated': {
      // WHY upsert: violation_updated arrives ~2 s after violation_created with the same id
      // but a finalised plate. We replace in-place so ViolationCard updates without
      // adding a duplicate row.
      const rest = state.recent.filter((v) => v.id !== msg.data.id)
      return { ...state, recent: [msg.data, ...rest].slice(0, MAX_RECENT) }
    }

    case 'stats':
      return { ...state, stats: msg.data }

    default:
      return state
  }
}

const LiveEventsContext = createContext<LiveState>(initialState)

/**
 * Provider that opens one WebSocket for the entire app.
 * On every reconnect, refetches cameras, recent violations, and stats to fill any gap.
 *
 * @param props.children - Subtree that can call {@link useLiveEvents}.
 * @returns The provider element.
 */
export function LiveEventsProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<LiveState>(initialState)
  const refetchRef = useRef<() => void>(() => {})

  // Refetch bootstrap data to fill gaps after reconnect
  const refetch = () => {
    const ctrl = new AbortController()
    const sig = ctrl.signal
    Promise.all([
      listCameras(sig),
      listViolations({ limit: 50 }, sig),
      getStats(sig),
    ])
      .then(([cameras, page, stats]) => {
        setState((s) => {
          // Merge camera REST response into live state (don't override WS data if newer)
          const merged: Record<string, LiveCamera> = { ...s.cameras }
          for (const cam of cameras) {
            if (!merged[cam.camera_id]) {
              merged[cam.camera_id] = { ...cam, tracks: [] }
            }
          }
          // Merge violations (live items take priority — they may be more recent)
          const liveIds = new Set(s.recent.map((v) => v.id))
          const extra = page.items.filter((v) => !liveIds.has(v.id))
          const merged_recent = [...s.recent, ...extra].slice(0, MAX_RECENT)
          return {
            ...s,
            cameras: merged,
            recent: merged_recent,
            stats: s.stats ?? stats,
          }
        })
      })
      .catch(() => {}) // Backend may be offline; WS backoff handles retry
    return () => ctrl.abort()
  }

  useEffect(() => {
    refetchRef.current = refetch
  })

  useEffect(() => {
    // Refetch on initial mount
    refetchRef.current()

    const close = connectEvents(
      (msg) => setState((s) => applyMessage(s, msg)),
      (status) => {
        setState((s) => ({ ...s, status }))
        // WHY refetch on reconnect: the WS gap may have missed violation_created events.
        if (status === 'open') {
          refetchRef.current()
        }
      },
    )
    return close
  }, [])

  const value = useMemo(() => state, [state])
  return createElement(LiveEventsContext.Provider, { value }, children)
}

/**
 * Read the live realtime state from context.
 * Must be used inside {@link LiveEventsProvider}.
 *
 * @returns The current {@link LiveState}.
 */
export function useLiveEvents(): LiveState {
  return useContext(LiveEventsContext)
}
