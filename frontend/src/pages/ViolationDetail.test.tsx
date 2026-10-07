import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { ViolationDetail } from './ViolationDetail'
import { LiveEventsProvider } from '@/hooks/useLiveEvents'
import * as api from '@/services/api'
import type { ViolationOut } from '@/types/contracts'

const mockViolation: ViolationOut = {
  id: 'v123',
  camera_id: 'CAM_01',
  track_id: 1,
  violation: 'NO_HELMET',
  plate: null,
  plate_status: 'UNREADABLE',
  plate_confidence: null,
  helmet_confidence: 0.9,
  timestamp: '2026-10-07T10:00:00Z',
  frame_index: 100,
  rider_bbox: [0, 0, 10, 10],
  evidence: { full_frame_url: '/full.jpg', rider_crop_url: '/rider.jpg', plate_crop_url: null },
}

vi.mock('@/services/api', async (importOriginal) => {
  const mod = await importOriginal<typeof import('@/services/api')>()
  return {
    ...mod,
    getViolation: vi.fn(),
    listCameras: vi.fn().mockResolvedValue([]),
    listViolations: vi.fn().mockResolvedValue({ items: [], total: 0 }),
    getStats: vi.fn().mockResolvedValue({}),
  }
})
// Mock WS to avoid connection errors in tests
vi.mock('@/services/ws', () => ({
  connectEvents: () => () => {},
}))

describe('ViolationDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders evidence and UNREADABLE state', async () => {
    vi.mocked(api.getViolation).mockResolvedValue(mockViolation)

    render(
      <MemoryRouter initialEntries={['/violations/v123']}>
        <LiveEventsProvider>
          <Routes>
            <Route path="/violations/:id" element={<ViolationDetail />} />
          </Routes>
        </LiveEventsProvider>
      </MemoryRouter>
    )

    // Wait for fetch to complete
    await waitFor(() => {
      expect(screen.getByText(/No-helmet violation/i)).toBeInTheDocument()
    })

    // Evidence renders (images)
    expect(screen.getByAltText(/Full frame with detection boxes/i)).toBeInTheDocument()
    expect(screen.getByAltText(/Rider crop/i)).toBeInTheDocument()

    // Plate badge shows OCR UNKNOWN
    expect(screen.getByTestId('plate-unreadable')).toHaveTextContent('OCR: UNKNOWN')
  })

  it('renders not found state when API returns 404', async () => {
    vi.mocked(api.getViolation).mockRejectedValue(new api.ApiError(404, '/api/violations/v123'))

    render(
      <MemoryRouter initialEntries={['/violations/v123']}>
        <LiveEventsProvider>
          <Routes>
            <Route path="/violations/:id" element={<ViolationDetail />} />
          </Routes>
        </LiveEventsProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Violation not found')).toBeInTheDocument()
      expect(screen.getByText('v123')).toBeInTheDocument()
    })
  })
})
