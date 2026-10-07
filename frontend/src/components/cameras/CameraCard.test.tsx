import { describe, expect, it } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { CameraCard } from './CameraCard'
import type { CameraOut } from '@/types/contracts'

const mockCamera: CameraOut = {
  camera_id: 'CAM_01',
  name: 'Test Cam',
  location: '',
  state: 'ONLINE',
  source_fps: 30,
  processing_fps: 5,
  frame_index: 100,
  riders_in_view: 1,
  stream_url: '/stream',
  snapshot_url: '',
  last_error: null,
}

describe('CameraCard', () => {
  it('shows CAMERA OFFLINE when state is OFFLINE', () => {
    render(
      <MemoryRouter>
        <CameraCard camera={{ ...mockCamera, state: 'OFFLINE' }} recentViolations={[]} />
      </MemoryRouter>
    )
    expect(screen.getByTestId('offline-overlay')).toHaveTextContent('CAMERA OFFLINE')
  })

  it('shows offline overlay when image fails to load', () => {
    render(
      <MemoryRouter>
        <CameraCard camera={mockCamera} recentViolations={[]} />
      </MemoryRouter>
    )
    
    expect(screen.queryByTestId('offline-overlay')).toBeNull()
    
    // Simulate image error
    const img = screen.getByAltText('Test Cam live feed')
    fireEvent.error(img)
    
    expect(screen.getByTestId('offline-overlay')).toHaveTextContent('CAMERA OFFLINE')
  })

  it('clears src on unmount to close MJPEG connection', () => {
    const { unmount } = render(
      <MemoryRouter>
        <CameraCard camera={mockCamera} recentViolations={[]} />
      </MemoryRouter>
    )
    
    const img = screen.getByAltText('Test Cam live feed') as HTMLImageElement
    expect(img.src).toContain('/stream')
    
    unmount()
    
    // Once unmounted, the effect cleanup should set src to '' or origin/"" 
    expect(img.src).toMatch(/^(http:\/\/localhost:\d+\/)?$/)
  })
})
