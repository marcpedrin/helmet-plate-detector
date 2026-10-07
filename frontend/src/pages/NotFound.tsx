/**
 * 404 page.
 * @module pages/NotFound
 */
import { Link } from 'react-router-dom'

/**
 * Rendered for unknown routes.
 * @returns The not-found page.
 */
export function NotFound() {
  return (
    <p>
      Page not found. <Link to="/" className="underline">Back to the dashboard</Link>
    </p>
  )
}
