import { describe, expect, it } from 'vitest'
import { formatPlateFull, formatUptime, pct } from './format'

describe('format', () => {
  it('formats percentages (pct)', () => {
    expect(pct(0.873)).toBe('87%')
    expect(pct(null)).toBe('—')
  })

  it('formats plates using full format logic', () => {
    expect(formatPlateFull('KA01AB1234')).toBe('KA 01 AB 1234')
    expect(formatPlateFull('22BH1234A')).toBe('22 BH 1234 A')
    expect(formatPlateFull('ABC12')).toBe('ABC12')
  })

  it('formats uptime', () => {
    expect(formatUptime(12)).toBe('12s')
    expect(formatUptime(184)).toBe('3m 04s')
    expect(formatUptime(3720)).toBe('1h 02m')
  })
})
