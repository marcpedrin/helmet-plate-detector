/**
 * Typed REST client for every backend endpoint (see docs/CONTRACTS.md).
 *
 * All functions throw {@link ApiError} on non-2xx responses.
 * Use {@link apiUrl} to prefix any backend-relative path (stream_url, evidence URLs).
 *
 * @module services/api
 * @example
 * import { getHealth, apiUrl } from '@/services/api'
 * const health = await getHealth()
 * const src = apiUrl('/api/cameras/CAM_01/stream.mjpg')
 */
import type { CameraOut, HealthOut, StatsOut, ViolationOut, ViolationPage } from '@/types/contracts'

/**
 * Backend origin.
 * Empty string = same origin (Vite dev proxy or FastAPI-served build).
 * Set VITE_API_BASE=http://localhost:8000 in frontend/.env to point at a separate backend.
 */
export const API_BASE: string = import.meta.env.VITE_API_BASE ?? ''

/**
 * Typed API error for non-2xx responses.
 *
 * @example
 * try { await getViolation('bad-id') } catch (e) {
 *   if (e instanceof ApiError && e.status === 404) // not found
 * }
 */
export class ApiError extends Error {
  /** HTTP status code. */
  readonly status: number
  /** Request path. */
  readonly path: string

  /**
   * @param status - HTTP status code.
   * @param path - Request path.
   */
  constructor(status: number, path: string) {
    super(`API ${status} on ${path}`)
    this.status = status
    this.path = path
    this.name = 'ApiError'
  }
}

/**
 * Prefix a backend-relative URL with {@link API_BASE}.
 * Absolute URLs (starting with `http`) are returned unchanged.
 *
 * @param path - Path starting with `/`, e.g. stream_url or an evidence URL.
 * @returns Absolute or same-origin URL usable in `<img src>`.
 * @example apiUrl('/api/cameras/CAM_01/stream.mjpg')
 */
export function apiUrl(path: string): string {
  return /^https?:\/\//.test(path) ? path : `${API_BASE}${path}`
}

/** @deprecated Alias kept for backward-compat; prefer {@link apiUrl}. */
export const assetUrl = apiUrl

async function get<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(apiUrl(path), { signal })
  if (!res.ok) throw new ApiError(res.status, path)
  return (await res.json()) as T
}

/** Query parameters for {@link listViolations}. */
export interface ViolationQuery {
  /** Filter to a specific camera. */
  camera_id?: string
  /** Page size (1-200, default 50). */
  limit?: number
  /** Page offset (default 0). */
  offset?: number
}

/**
 * GET /api/health — health, mode and model states.
 *
 * @param signal - Optional abort signal.
 * @returns Health, mode and model states.
 */
export function getHealth(signal?: AbortSignal): Promise<HealthOut> {
  return get('/api/health', signal)
}

/**
 * GET /api/cameras — all cameras in config order.
 *
 * @param signal - Optional abort signal.
 * @returns Array of camera objects.
 */
export function listCameras(signal?: AbortSignal): Promise<CameraOut[]> {
  return get('/api/cameras', signal)
}

/**
 * GET /api/cameras/{id} — one camera.
 *
 * @param cameraId - Camera id, e.g. `"CAM_01"`.
 * @param signal - Optional abort signal.
 * @returns One camera object.
 * @throws {ApiError} 404 if not found.
 */
export function getCamera(cameraId: string, signal?: AbortSignal): Promise<CameraOut> {
  return get(`/api/cameras/${encodeURIComponent(cameraId)}`, signal)
}

/**
 * GET /api/violations — paginated list of violations, newest first.
 *
 * @param query - Optional camera filter and paging.
 * @param signal - Optional abort signal.
 * @returns A page of violations.
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
 * GET /api/violations/{id} — one violation.
 *
 * @param id - Violation id.
 * @param signal - Optional abort signal.
 * @returns One violation object.
 * @throws {ApiError} 404 if not found.
 */
export function getViolation(id: string, signal?: AbortSignal): Promise<ViolationOut> {
  return get(`/api/violations/${encodeURIComponent(id)}`, signal)
}

/**
 * GET /api/stats — aggregate dashboard counters.
 *
 * @param signal - Optional abort signal.
 * @returns Current dashboard statistics.
 */
export function getStats(signal?: AbortSignal): Promise<StatsOut> {
  return get('/api/stats', signal)
}
