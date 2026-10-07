/**
 * React error boundary for page-level crash isolation.
 * Shows a friendly error card instead of a blank screen.
 * Wraps each page route so one broken page never crashes the whole app.
 *
 * @module components/layout/PageErrorBoundary
 * @example
 * <PageErrorBoundary>
 *   <DashboardPage />
 * </PageErrorBoundary>
 */
import { Component, type ErrorInfo, type ReactNode } from 'react'
import { AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface Props {
  children: ReactNode
}

interface State {
  error: Error | null
}

/**
 * Error boundary component that catches render errors in its subtree.
 * Renders a friendly card with the error message and a reload button.
 *
 * @example
 * <PageErrorBoundary>
 *   <MyPage />
 * </PageErrorBoundary>
 */
export class PageErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { error: null }
  }

  /**
   * Update state when an error is caught.
   *
   * @param error - The caught error.
   * @returns New state with the error.
   */
  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  /**
   * Log error details for debugging.
   *
   * @param error - The caught error.
   * @param info - React error info including component stack.
   */
  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[PageErrorBoundary]', error, info)
  }

  /**
   * @returns The error card or the children subtree.
   */
  render() {
    if (this.state.error) {
      return (
        <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
          <AlertTriangle className="h-10 w-10 text-offline" aria-hidden />
          <div>
            <h2 className="text-base font-semibold">Something went wrong</h2>
            <p className="text-sm text-muted-foreground mt-1">{this.state.error.message}</p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => this.setState({ error: null })}
          >
            Try again
          </Button>
        </div>
      )
    }
    return this.props.children
  }
}
