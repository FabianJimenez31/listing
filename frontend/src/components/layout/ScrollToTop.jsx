import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

/**
 * Resets the window scroll to the top on every route (pathname) change.
 *
 * Without this, react-router keeps the previous scroll position, so opening a
 * property detail from a scrolled-down list lands mid-page (over the contact
 * box) instead of at the top, where the gallery carousel lives. Keyed on
 * `pathname` only, so in-page query-string changes (e.g. search filters on
 * /propiedades) don't yank the user back to the top.
 *
 * `behavior: 'instant'` overrides the global `scroll-behavior: smooth`
 * (index.css) — on a route change we want an immediate jump, not an animated
 * slide up the previous page.
 */
export default function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' })
  }, [pathname])
  return null
}
