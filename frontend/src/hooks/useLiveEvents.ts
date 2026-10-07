/**
 * Live state from /ws/events, shared through React context.
 * Wrap the app in {@link LiveEventsProvider}; read with {@link useLiveEvents}.
 * @module hooks/useLiveEvents
 */
import { createContext, createElement, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { connectEvents, type WsStatus } from '@/services/ws'
import type { CameraMetricsMsg, CameraOut, HelloMsg, StatsOut, ViolationOut, WsMessage } from '@/types/contracts'

/** Maximum number of recent violations kept in memory. */
export const MAX_RECENT = 50

/** Everything the UI needs from the realtime stream. */
export interface LiveState {
  status: WsStatus
  hello: HelloMsg | null
  cameras: Record<string, CameraOut>
  metrics: Record<string, CameraMetricsMsg>
  /** Newest first, max {@link MAX_RECENT}; updated in place on violation_updated. */
  recent: ViolationOut[]
  stats: StatsOut | null
}

const initialState: LiveState = { status: 'connecting', hello: null, cameras: {}, metrics: {}, recent: [], stats: null }

/**
 * Pure reducer applying one server message to the live state (exported for tests).
 * @param state Current state.
 * @param msg Server message.
 * @returns Next state.
 */
export function applyMessage(state: LiveState, msg: WsMessage): LiveState {
  switch (msg.type) {
    case 'hello':
      return { ...state, hello: msg.data }
    case 'camera_status':
      return { ...state, cameras: { ...state.cameras, [msg.data.camera_id]: msg.data } }
    case 'camera_metrics':
      return { ...state, metrics: { ...state.metrics, [msg.data.camera_id]: msg.data } }
    case 'violation_created':
    case 'violation_updated': {
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
 * Provider opening one WebSocket for the whole app.
 * @param props.children Subtree that can call {@link useLiveEvents}.
 * @returns The provider element.
 */
export function LiveEventsProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<LiveState>(initialState)
  useEffect(
    () =>
      connectEvents(
        (msg) => setState((s) => applyMessage(s, msg)),
        (status) => setState((s) => ({ ...s, status })),
      ),
    [],
  )
  const value = useMemo(() => state, [state])
  return createElement(LiveEventsContext.Provider, { value }, children)
}

/**
 * Read the live realtime state.
 * @returns The current {@link LiveState}.
 */
export function useLiveEvents(): LiveState {
  return useContext(LiveEventsContext)
}
