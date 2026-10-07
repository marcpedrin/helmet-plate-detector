import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PlateBadge } from './PlateBadge'

describe('PlateBadge', () => {
  it('renders READ state with formatted plate', () => {
    render(<PlateBadge plate="KA01AB1234" status="READ" confidence={0.99} />)
    expect(screen.getByTestId('plate-read')).toHaveTextContent('KA 01 AB 1234')
    expect(screen.getByTestId('plate-read')).toHaveTextContent('99%')
  })

  it('renders PENDING state', () => {
    render(<PlateBadge plate={null} status="PENDING" />)
    expect(screen.getByTestId('plate-pending')).toHaveTextContent('Reading plate…')
  })

  it('renders UNREADABLE state', () => {
    render(<PlateBadge plate={null} status="UNREADABLE" />)
    expect(screen.getByTestId('plate-unreadable')).toHaveTextContent('OCR: UNKNOWN')
  })

  it('renders NOT_DETECTED state', () => {
    render(<PlateBadge plate={null} status="NOT_DETECTED" />)
    expect(screen.getByTestId('plate-not-detected')).toHaveTextContent('Plate not visible')
  })
})
