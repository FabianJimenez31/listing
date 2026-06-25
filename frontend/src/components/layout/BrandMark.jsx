import { useSettings } from '../../contexts/SettingsContext'

// Renders the admin-uploaded site logo when one is configured, otherwise the
// text wordmark each surface passes as `fallback`. Keeps the header, footer and
// admin sidebar in sync from a single source of truth (SettingsContext).
export default function BrandMark({ fallback, className = 'logo-img' }) {
  const { logoUrl } = useSettings()
  if (logoUrl) return <img src={logoUrl} alt="Proppietario" className={className} />
  return fallback
}
