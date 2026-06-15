import { Link } from 'react-router-dom'

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
    title: 'Proppietario',
    links: [
      ['Inmobiliarias', '/inmobiliarias'],
      ['Proyectos', '/proyectos'],
      ['Blog de inversión', '/blog'],
      ['Preguntas frecuentes', '/blog'],
    ],
  },
]

const Social = ({ label, children }) => (
  <a href="#" aria-label={label} onClick={(e) => e.preventDefault()}>{children}</a>
)

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="wrap">
        <div className="foot-grid">
          <div className="foot-brand">
            <Link to="/" className="logo"><span className="dot">P</span>Proppietario</Link>
            <p>Construimos patrimonio con información, estrategia y acompañamiento. Colombia y Estados Unidos.</p>
            <div className="socials">
              <Social label="Instagram">
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="3" y="3" width="18" height="18" rx="5" /><circle cx="12" cy="12" r="4" /><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none" /></svg>
              </Social>
              <Social label="LinkedIn">
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="3" y="3" width="18" height="18" rx="3" /><path d="M7 10v7M7 7v.01M11 17v-4a2 2 0 0 1 4 0v4M11 11v6" /></svg>
              </Social>
              <Social label="YouTube">
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="2" y="5" width="20" height="14" rx="4" /><path d="m10 9 5 3-5 3z" fill="currentColor" stroke="none" /></svg>
              </Social>
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

        <div className="foot-bottom">
          <span>© 2026 Proppietario. Todos los derechos reservados. · Bogotá · Miami</span>
          <span style={{ display: 'flex', gap: 20 }}>
            <Link to="/blog">Privacidad</Link>
            <Link to="/blog">Términos de uso</Link>
            <Link to="/blog">Política de cookies</Link>
          </span>
        </div>
      </div>
    </footer>
  )
}
