import { Link } from 'react-router-dom'

export default function CTASection() {
  return (
    <section style={s.section}>
      <div style={s.inner}>
        <h2 style={s.h2}>
          Invertir con información<br />es invertir mejor.
        </h2>
        <p style={s.subtitle}>
          Agenda una asesoría personalizada. Sin costo. Sin compromiso.
        </p>
        <Link to="/registro" style={s.cta}>
          Agenda tu asesoría
        </Link>
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
    textAlign: 'center',
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
    marginBottom: '2.5rem',
  },
  cta: {
    display: 'inline-block',
    background: '#fff',
    color: '#0251FD',
    fontFamily: "'Montserrat', sans-serif",
    fontWeight: 700,
    fontSize: 16,
    padding: '18px 40px',
    borderRadius: 12,
    textDecoration: 'none',
    letterSpacing: '-0.2px',
  },
}
