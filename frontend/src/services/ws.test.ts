import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { connectEvents, backoffDelay, BACKOFF_MIN_MS, BACKOFF_MAX_MS, BACKOFF_JITTER } from './ws'

describe('WebSocket Backoff', () => {
  it('calculates delays with jitter', () => {
    // The delay should be clamp(1000 * 2^n) ± 20%
    // We can test bounds
    for (let i = 0; i < 5; i++) {
      const delay = backoffDelay(i)
      const base = Math.min(BACKOFF_MAX_MS, BACKOFF_MIN_MS * 2 ** i)
      const min = base * (1 - BACKOFF_JITTER)
      const max = base * (1 + BACKOFF_JITTER)
      expect(delay).toBeGreaterThanOrEqual(min)
      expect(delay).toBeLessThanOrEqual(max)
    }

    // Attempt 10 should be capped
    const capped = backoffDelay(10)
    expect(capped).toBeGreaterThanOrEqual(BACKOFF_MAX_MS * (1 - BACKOFF_JITTER))
    expect(capped).toBeLessThanOrEqual(BACKOFF_MAX_MS * (1 + BACKOFF_JITTER))
  })
})

describe('connectEvents', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('stops reconnecting when close() is called', () => {
    // Mock WebSocket
    const closeMock = vi.fn()
    const instances: FakeWS[] = []
    class FakeWS {
      onclose: (() => void) | null = null
      onerror: (() => void) | null = null
      close = closeMock
      constructor() {
        instances.push(this)
      }
    }
    vi.stubGlobal('WebSocket', FakeWS)

    let wsStatus = ''
    const close = connectEvents(
      () => {},
      (status) => { wsStatus = status }
    )

    expect(wsStatus).toBe('connecting')
    
    close()
    
    // Simulate a close event occurring after we told it to stop
    // (e.g. the browser dispatching it asynchronously)
    const ws = instances[0]
    if (ws && ws.onclose) {
      ws.onclose()
    }

    expect(wsStatus).toBe('closed')

    // Fast forward time, ensure no new WebSocket was created
    vi.advanceTimersByTime(20000)
    expect(instances).toHaveLength(1) // only the initial one
  })
})
