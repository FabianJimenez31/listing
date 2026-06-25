import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { getSettings } from '../api/settings'

// Global, public site branding (currently the logo). Fetched once on load so
// the header/footer/panel can render the uploaded logo for every visitor, with
// the text wordmark as the fallback while loading or when no logo is set.
const SettingsContext = createContext(null)

export function SettingsProvider({ children }) {
  const [settings, setSettings] = useState(null)

  const refresh = useCallback(() =>
    getSettings().then(setSettings).catch(() => null), [])

  useEffect(() => { refresh() }, [refresh])

  const logoUrl = settings?.logo_url || null
  // Footer brand logo falls back to the header logo when not configured.
  const footerLogoUrl = settings?.footer_logo_url || null

  return (
    <SettingsContext.Provider value={{ settings, logoUrl, footerLogoUrl, setSettings, refresh }}>
      {children}
    </SettingsContext.Provider>
  )
}

export function useSettings() {
  return useContext(SettingsContext) ?? { settings: null, logoUrl: null, footerLogoUrl: null, setSettings: () => {}, refresh: () => {} }
}
