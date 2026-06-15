import { Link } from 'react-router-dom'

const CITIES = ['Miami', 'Nueva York', 'Dallas', 'Austin', 'Orlando']

export default function USASection() {
  return (
    <section style={s.section}>
      <div style={s.inner}>
        <div style={s.content}>
          <p style={s.eyebrow}>MERCADO USA</p>
          <h2 style={s.h2}>Tu patrimonio sin fronteras</h2>
          <p style={s.subtitle}>
            Invertir en bienes raíces en Estados Unidos es más accesible de lo que crees.
            Te guiamos desde la estructura legal hasta el cierre.
          </p>
          <div style={s.cities}>
            {CITIES.map(c => (
              <span key={c} style={s.chip}>{c}</span>
            ))}
          </div>
          <Link to="/propiedades?q=usa" style={s.cta}>
            Explorar mercado USA →
          </Link>
        </div>
      </div>
    </section>
  )
}

const s = {
  section: {
    background: 'linear-gradient(90deg, #081D67 0%, #0251FD 100%)',
    width: '100%',
  },
  inner: {
    maxWidth: 1280,
    margin: '0 auto',
    padding: '8rem 4rem',
  },
  content: { maxWidth: 640 },
  eyebrow: {
    fontFamily: "'Inter', sans-serif",
    fontWeight: 600,
    fontSize: 12,
    letterSpacing: '0.1em',
    textTransform: 'uppercase',
    color: 'rgba(255,255,255,0.65)',
    marginBottom: '1rem',
  },
  h2: {
    fontFamily: "'Montserrat', sans-serif",
    fontWeight: 800,
    fontSize: 'clamp(28px, 4vw, 48px)',
    color: '#fff',
    lineHeight: 1.1,
    marginBottom: '1.25rem',
  },
  subtitle: {
    fontSize: 18,
    color: 'rgba(255,255,255,0.8)',
    lineHeight: 1.65,
    marginBottom: '2rem',
  },
  cities: {
    display: 'flex',
    gap: '0.75rem',
    flexWrap: 'wrap',
    marginBottom: '2.5rem',
  },
  chip: {
    background: 'rgba(255,255,255,0.15)',
    color: '#fff',
    borderRadius: 999,
    padding: '6px 16px',
    fontSize: 14,
    fontWeight: 600,
    border: '1px solid rgba(255,255,255,0.25)',
    fontFamily: "'Montserrat', sans-serif",
  },
  cta: {
    display: 'inline-block',
    background: '#fff',
    color: '#0251FD',
    fontFamily: "'Montserrat', sans-serif",
    fontWeight: 700,
    fontSize: 15,
    padding: '16px 28px',
    borderRadius: 12,
    textDecoration: 'none',
    letterSpacing: '-0.2px',
  },
}
