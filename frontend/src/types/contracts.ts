/**
 * CONTRACT — owner: Marc. Change only via a contracts/* PR.
 *
 * Field-for-field mirror of backend/app/core/schemas.py (pydantic) and the enums in
 * backend/app/core/types.py. Timestamps are ISO-8601 UTC strings. Do not edit in
 * feature PRs; see docs/CONTRACTS.md.
 * @module contracts
 */

/** Lifecycle state of one virtual camera. */
export type CameraState = 'STARTING' | 'ONLINE' | 'OFFLINE' | 'STOPPED'
/** Helmet classification of one rider/head. */
export type HelmetStatus = 'HELMET' | 'NO_HELMET' | 'UNKNOWN'
/** Outcome of number-plate reading for one violation. */
export type PlateStatus = 'PENDING' | 'READ' | 'UNREADABLE' | 'NOT_DETECTED'
/** Load state of an ML model. */
export type ModelState = 'LOADED' | 'MOCK' | 'NOT_LOADED' | 'ERROR'

/** URLs (under /evidence) of the evidence JPEGs for one violation. */
export interface EvidenceUrls {
  full_frame_url: string
  rider_crop_url: string
  plate_crop_url: string | null
}

/** One stored violation (REST + violation_* WS messages). */
export interface ViolationOut {
  id: string
  camera_id: string
  track_id: number
  violation: 'NO_HELMET'
  plate: string | null
  plate_status: PlateStatus
  plate_confidence: number | null
  helmet_confidence: number
  /** ISO-8601 UTC */
  timestamp: string
  frame_index: number
  rider_bbox: number[]
  evidence: EvidenceUrls
}

/** A page of violations, newest first. */
export interface ViolationPage {
  items: ViolationOut[]
  total: number
  limit: number
  offset: number
}

/** Aggregate counters computed by the repository. */
export interface RepositoryCounts {
  total: number
  by_camera: Record<string, number>
  plates_read: number
  plates_unreadable: number
}

/** One camera with runtime state and pipeline metrics. */
export interface CameraOut {
  camera_id: string
  name: string
  location: string
  state: CameraState
  source_fps: number
  processing_fps: number
  frame_index: number
  riders_in_view: number
  stream_url: string
  snapshot_url: string
  last_error: string | null
}

/** Load state of each model family. */
export interface ModelsHealth {
  detector: ModelState
  helmet: ModelState
  plate_detector: ModelState
  ocr: ModelState
}

/** Response of GET /api/health. */
export interface HealthOut {
  status: 'ok' | 'degraded'
  mode: 'live' | 'mock'
  models: ModelsHealth
  version: string
}

/** Response of GET /api/stats and payload of `stats` WS messages. */
export interface StatsOut {
  total_violations: number
  violations_by_camera: Record<string, number>
  plates_read: number
  plates_unreadable: number
  riders_in_view: number
  cameras_online: number
  cameras_total: number
  uptime_s: number
}

/** One tracked rider drawn on the live overlay. */
export interface TrackOverlay {
  track_id: number
  bbox: number[]
  helmet: HelmetStatus
}

/** Payload of `camera_metrics` WS messages. */
export interface CameraMetricsMsg {
  camera_id: string
  processing_fps: number
  riders_in_view: number
  tracks: TrackOverlay[]
}

/** All WS message types. */
export type WsMessageType =
  | 'hello'
  | 'camera_status'
  | 'camera_metrics'
  | 'violation_created'
  | 'violation_updated'
  | 'stats'

/** Envelope wrapping every /ws/events message (generic over the payload). */
export interface WsEnvelope<T = Record<string, unknown>> {
  type: WsMessageType
  /** ISO-8601 UTC */
  ts: string
  data: T
}

/** Payload of the `hello` message. */
export interface HelloMsg {
  mode: 'live' | 'mock'
  version: string
  cameras: string[]
}

/** Discriminated union of every message the server sends, for exhaustive handling. */
export type WsMessage =
  | (WsEnvelope<HelloMsg> & { type: 'hello' })
  | (WsEnvelope<CameraOut> & { type: 'camera_status' })
  | (WsEnvelope<CameraMetricsMsg> & { type: 'camera_metrics' })
  | (WsEnvelope<ViolationOut> & { type: 'violation_created' | 'violation_updated' })
  | (WsEnvelope<StatsOut> & { type: 'stats' })
