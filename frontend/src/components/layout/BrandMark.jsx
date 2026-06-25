import { useSettings } from '../../contexts/SettingsContext'

// Renders the admin-uploaded site logo when one is configured, otherwise the
// text wordmark each surface passes as `fallback`. Keeps the header, footer and
// admin sidebar in sync from a single source of truth (SettingsContext).
//
// Pass `footer` to use the dedicated footer brand logo when set; it falls back
// to the header logo, and finally to the text wordmark.
export default function BrandMark({ fallback, className = 'logo-img', footer = false }) {
  const { logoUrl, footerLogoUrl } = useSettings()
  const src = footer ? footerLogoUrl || logoUrl : logoUrl
  if (src) return <img src={src} alt="Proppietario" className={className} />
  return fallback
}
