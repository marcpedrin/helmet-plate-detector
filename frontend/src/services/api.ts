/**
 * Typed REST client for every backend endpoint (see docs/CONTRACTS.md).
 * @module services/api
 */
import type { CameraOut, HealthOut, StatsOut, ViolationOut, ViolationPage } from '@/types/contracts'

/** Backend origin. Empty string = same origin (Vite dev proxy or FastAPI-served build). */
export const API_BASE: string = import.meta.env.VITE_API_BASE ?? ''

/** Error thrown for non-2xx responses. */
export class ApiError extends Error {
  readonly status: number
  readonly path: string

  /**
   * @param status HTTP status code.
   * @param path Request path.
   */
  constructor(status: number, path: string) {
    super(`API ${status} on ${path}`)
    this.status = status
    this.path = path
  }
}

/**
 * Prefix a backend-relative URL (e.g. `stream_url`, evidence URLs) with {@link API_BASE}.
 * @param path Path starting with `/`, or an absolute URL (returned unchanged).
 * @returns Absolute or same-origin URL usable in `<img src>`.
 */
export function apiUrl(path: string): string {
  return /^https?:\/\//.test(path) ? path : `${API_BASE}${path}`
}

async function get<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(apiUrl(path), { signal })
  if (!res.ok) throw new ApiError(res.status, path)
  return (await res.json()) as T
}

/** Query parameters of {@link listViolations}. */
export interface ViolationQuery {
  camera_id?: string
  limit?: number
  offset?: number
}

/**
 * GET /api/health.
 * @param signal Optional abort signal.
 * @returns Health, mode and model states.
 */
export function getHealth(signal?: AbortSignal): Promise<HealthOut> {
  return get('/api/health', signal)
}

/**
 * GET /api/cameras.
 * @param signal Optional abort signal.
 * @returns All cameras in config order.
 */
export function listCameras(signal?: AbortSignal): Promise<CameraOut[]> {
  return get('/api/cameras', signal)
}

/**
 * GET /api/cameras/{id}.
 * @param cameraId Camera id, e.g. `CAM_01`.
 * @param signal Optional abort signal.
 * @returns One camera.
 */
export function getCamera(cameraId: string, signal?: AbortSignal): Promise<CameraOut> {
  return get(`/api/cameras/${encodeURIComponent(cameraId)}`, signal)
}

/**
 * GET /api/violations.
 * @param query Optional camera filter and paging.
 * @param signal Optional abort signal.
 * @returns A page of violations, newest first.
 */
export function listViolations(query: ViolationQuery = {}, signal?: AbortSignal): Promise<ViolationPage> {
  const params = new URLSearchParams()
  if (query.camera_id) params.set('camera_id', query.camera_id)
  if (query.limit !== undefined) params.set('limit', String(query.limit))
  if (query.offset !== undefined) params.set('offset', String(query.offset))
  const qs = params.toString()
  return get(`/api/violations${qs ? `?${qs}` : ''}`, signal)
}

/**
 * GET /api/violations/{id}.
 * @param id Violation id.
 * @param signal Optional abort signal.
 * @returns One violation.
 */
export function getViolation(id: string, signal?: AbortSignal): Promise<ViolationOut> {
  return get(`/api/violations/${encodeURIComponent(id)}`, signal)
}

/**
 * GET /api/stats.
 * @param signal Optional abort signal.
 * @returns Dashboard counters.
 */
export function getStats(signal?: AbortSignal): Promise<StatsOut> {
  return get('/api/stats', signal)
}
