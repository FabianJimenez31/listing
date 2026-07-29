import { Link } from 'react-router-dom'
import BrandMark from './BrandMark'
import { useSettings } from '../../contexts/SettingsContext'

const COLS = [
  {
    title: 'Venta',
    links: [
      ['Apartamentos en Bogotá', '/propiedades?operation_type=sale&q=Bogotá'],
      ['Casas en Medellín', '/propiedades?operation_type=sale&q=Medellín'],
      ['Apartamentos en Cali', '/propiedades?operation_type=sale&q=Cali'],
      ['Oficinas en Bogotá', '/propiedades?operation_type=sale&property_kind=office'],
    ],
  },
  {
    title: 'Arriendo',
    links: [
      ['Apartamentos en Bogotá', '/propiedades?operation_type=rent&q=Bogotá'],
      ['Casas en Medellín', '/propiedades?operation_type=rent&q=Medellín'],
      ['Locales comerciales', '/propiedades?operation_type=rent&property_kind=commercial'],
      ['Apartaestudios', '/propiedades?operation_type=rent&property_kind=apartment'],
    ],
  },
  {
    title: 'Mercado USA',
    links: [
      ['Condos en Miami', '/usa?q=Miami'],
      ['Renta en Austin', '/usa?q=Austin'],
      ['Inversión en Nueva York', '/usa?q=Nueva York'],
      ['Proyectos en preventa', '/proyectos?country=us'],
    ],
  },
  {
    title: 'Proppia',
    links: [
      ['Crédito hipotecario', '/credito-hipotecario'],
      ['Inmobiliarias', '/inmobiliarias'],
      ['Proyectos', '/proyectos'],
      ['Blog de inversión', '/blog'],
    ],
  },
]

const IG_ICON = (
  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="3" y="3" width="18" height="18" rx="5" /><circle cx="12" cy="12" r="4" /><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none" /></svg>
)
const LI_ICON = (
  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="3" y="3" width="18" height="18" rx="3" /><path d="M7 10v7M7 7v.01M11 17v-4a2 2 0 0 1 4 0v4M11 11v6" /></svg>
)
const YT_ICON = (
  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="2" y="5" width="20" height="14" rx="4" /><path d="m10 9 5 3-5 3z" fill="currentColor" stroke="none" /></svg>
)

// Defaults preserve the previous hard-coded footer until an admin edits it.
const DEFAULT_TAGLINE = 'Construimos patrimonio con información, estrategia y acompañamiento. Colombia y Estados Unidos.'
const DEFAULT_COPYRIGHT = '© 2026 Proppia. Todos los derechos reservados. · Bogotá · Miami'

const Social = ({ label, url, children }) => (
  <a
    href={url || '#'}
    aria-label={label}
    {...(url ? { target: '_blank', rel: 'noreferrer' } : { onClick: (e) => e.preventDefault() })}
  >
    {children}
  </a>
)

const isExternal = (url) => /^https?:\/\//i.test(url || '')
// Sin documento cargado no se pinta el enlace (antes caía al blog, que confundía).
const LegalLink = ({ to, children }) => {
  if (!to) return null
  return isExternal(to)
    ? <a href={to} target="_blank" rel="noreferrer">{children}</a>
    : <Link to={to}>{children}</Link>
}

export default function Footer() {
  const { settings } = useSettings()
  const s = settings || {}
  const footerLogos = s.footer_logos || []

  return (
    <footer className="site-footer">
      <div className="wrap">
        <div className="foot-grid">
          <div className="foot-brand">
            <Link to="/" className="logo"><BrandMark footer fallback={<><span className="dot">P</span>Proppia</>} /></Link>
            <p>{s.footer_tagline || DEFAULT_TAGLINE}</p>
            <div className="socials">
              <Social label="Instagram" url={s.social_instagram}>{IG_ICON}</Social>
              <Social label="LinkedIn" url={s.social_linkedin}>{LI_ICON}</Social>
              <Social label="YouTube" url={s.social_youtube}>{YT_ICON}</Social>
            </div>
          </div>

          {COLS.map((col) => (
            <div className="foot-col" key={col.title}>
              <h5>{col.title}</h5>
              {col.links.map(([label, to]) => (
                <Link key={label} to={to}>{label}</Link>
              ))}
            </div>
          ))}
        </div>

        {footerLogos.length > 0 && (
          <div className="foot-logos">
            {footerLogos.map((logo, i) =>
              logo.link ? (
                <a key={i} href={logo.link} target="_blank" rel="noreferrer" title={logo.name}>
                  <img src={logo.image_url} alt={logo.name || 'Aliado'} />
                </a>
              ) : (
                <img key={i} src={logo.image_url} alt={logo.name || 'Aliado'} title={logo.name} />
              ),
            )}
          </div>
        )}

        <div className="foot-bottom">
          <span>{s.copyright_text || DEFAULT_COPYRIGHT}</span>
          <span style={{ display: 'flex', gap: 20 }}>
            <LegalLink to={s.legal_privacy_url}>Privacidad</LegalLink>
            <LegalLink to={s.legal_terms_url}>Términos de uso</LegalLink>
            <LegalLink to={s.legal_cookies_url}>Política de cookies</LegalLink>
          </span>
        </div>
      </div>
    </footer>
  )
}
