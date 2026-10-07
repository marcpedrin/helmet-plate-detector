import { describe, expect, it } from 'vitest'
import { applyMessage, type LiveState, MAX_RECENT } from './useLiveEvents'
import type { CameraOut, ViolationOut } from '@/types/contracts'

const baseState: LiveState = {
  status: 'open',
  hello: null,
  cameras: {},
  metrics: {},
  recent: [],
  stats: null,
}

const mockViolation: ViolationOut = {
  id: 'v1',
  camera_id: 'CAM_01',
  track_id: 1,
  violation: 'NO_HELMET',
  plate: null,
  plate_status: 'PENDING',
  plate_confidence: null,
  helmet_confidence: 0.9,
  timestamp: '2026-10-07T10:00:00Z',
  frame_index: 100,
  rider_bbox: [0, 0, 10, 10],
  evidence: { full_frame_url: '', rider_crop_url: '', plate_crop_url: null },
}

const mockCamera: CameraOut = {
  camera_id: 'CAM_01',
  name: 'Test Cam',
  location: '',
  state: 'ONLINE',
  source_fps: 30,
  processing_fps: 5,
  frame_index: 100,
  riders_in_view: 1,
  stream_url: '',
  snapshot_url: '',
  last_error: null,
}

describe('applyMessage (liveEvents reducer)', () => {
  it('upserts violations on violation_created and violation_updated', () => {
    // 1. Created (PENDING)
    const s1 = applyMessage(baseState, { type: 'violation_created', ts: '', data: mockViolation })
    expect(s1.recent).toHaveLength(1)
    expect(s1.recent[0].plate_status).toBe('PENDING')

    // 2. Updated (READ)
    const updated = { ...mockViolation, plate: 'KA01', plate_status: 'READ' as const }
    const s2 = applyMessage(s1, { type: 'violation_updated', ts: '', data: updated })
    
    expect(s2.recent).toHaveLength(1) // merged in place
    expect(s2.recent[0].plate_status).toBe('READ')
    expect(s2.recent[0].plate).toBe('KA01')
  })

  it(`caps recent violations at ${MAX_RECENT}`, () => {
    let state = baseState
    // insert MAX_RECENT + 5
    for (let i = 0; i < MAX_RECENT + 5; i++) {
      state = applyMessage(state, {
        type: 'violation_created',
        ts: '',
        data: { ...mockViolation, id: `v${i}` },
      })
    }
    expect(state.recent).toHaveLength(MAX_RECENT)
    // newest should be first
    expect(state.recent[0].id).toBe(`v${MAX_RECENT + 4}`)
  })

  it('merges camera_metrics into camera state', () => {
    // 1. Initial status
    const s1 = applyMessage(baseState, { type: 'camera_status', ts: '', data: mockCamera })
    expect(s1.cameras['CAM_01'].processing_fps).toBe(5)

    // 2. Metrics update
    const s2 = applyMessage(s1, {
      type: 'camera_metrics',
      ts: '',
      data: { camera_id: 'CAM_01', processing_fps: 6.5, riders_in_view: 3, tracks: [] },
    })

    expect(s2.cameras['CAM_01'].processing_fps).toBe(6.5)
    expect(s2.cameras['CAM_01'].riders_in_view).toBe(3)
  })

  it('updates state on camera OFFLINE', () => {
    const s1 = applyMessage(baseState, { type: 'camera_status', ts: '', data: mockCamera })
    const offlineCam = { ...mockCamera, state: 'OFFLINE' as const, last_error: 'timeout' }
    const s2 = applyMessage(s1, { type: 'camera_status', ts: '', data: offlineCam })
    
    expect(s2.cameras['CAM_01'].state).toBe('OFFLINE')
    expect(s2.cameras['CAM_01'].last_error).toBe('timeout')
  })
})
