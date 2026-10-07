import { describe, expect, it } from 'vitest'
import { applyMessage, type LiveState } from '@/hooks/useLiveEvents'
import { backoffDelay } from '@/services/ws'
import type { ViolationOut } from '@/types/contracts'
import { formatConfidence, formatPlate, formatUptime } from './format'

describe('format', () => {
  it('formats confidence', () => {
    expect(formatConfidence(0.873)).toBe('87%')
    expect(formatConfidence(null)).toBe('—')
  })

  it('formats plates by status', () => {
    expect(formatPlate('KA01AB1234', 'READ')).toBe('KA01AB1234')
    expect(formatPlate(null, 'PENDING')).toBe('reading…')
    expect(formatPlate(null, 'UNREADABLE')).toBe('unreadable')
  })

  it('formats uptime', () => {
    expect(formatUptime(12)).toBe('12s')
    expect(formatUptime(184)).toBe('3m 04s')
    expect(formatUptime(3720)).toBe('1h 02m')
  })
})

describe('ws backoff', () => {
  it('grows from 1 s to a 10 s cap', () => {
    expect([0, 1, 2, 3, 4, 10].map(backoffDelay)).toEqual([1000, 2000, 4000, 8000, 10000, 10000])
  })
})

describe('applyMessage', () => {
  const base: LiveState = { status: 'open', hello: null, cameras: {}, metrics: {}, recent: [], stats: null }
  const v: ViolationOut = {
    id: 'a', camera_id: 'CAM_01', track_id: 1, violation: 'NO_HELMET', plate: null, plate_status: 'PENDING',
    plate_confidence: null, helmet_confidence: 0.8, timestamp: '2026-10-07T10:00:00Z', frame_index: 1,
    rider_bbox: [0, 0, 1, 1], evidence: { full_frame_url: '/f', rider_crop_url: '/r', plate_crop_url: null },
  }

  it('updates a violation in place on violation_updated', () => {
    const s1 = applyMessage(base, { type: 'violation_created', ts: '', data: v })
    const s2 = applyMessage(s1, { type: 'violation_updated', ts: '', data: { ...v, plate: 'KA01AB1234', plate_status: 'READ' } })
    expect(s2.recent).toHaveLength(1)
    expect(s2.recent[0].plate).toBe('KA01AB1234')
  })
})
