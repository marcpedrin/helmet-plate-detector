/**
 * 404 Not Found page.
 *
 * @module pages/NotFoundPage
 */
import { Link } from 'react-router-dom'
import { Compass } from 'lucide-react'
import { Button } from '@/components/ui/button'

/**
 * Friendly 404 page with a link back to the dashboard.
 *
 * @returns The not-found page element.
 */
export function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center gap-6 py-24 text-center">
      <Compass className="h-12 w-12 text-muted-foreground/30" aria-hidden />
      <div>
        <h1 className="text-2xl font-semibold">Page not found</h1>
        <p className="text-sm text-muted-foreground mt-2">
          The page you were looking for doesn't exist.
        </p>
      </div>
      <Button asChild variant="outline" size="sm">
        <Link to="/">← Return to Dashboard</Link>
      </Button>
    </div>
  )
}
