const SERVICES = [
  {
    icon: '◈',
    title: 'Asesoría de inversión',
    desc: 'Te acompañamos en cada decisión patrimonial con análisis de mercado y estrategia personalizada.',
  },
  {
    icon: '⊞',
    title: 'Propiedades en Colombia',
    desc: 'Portafolio curado en Bogotá, Medellín y principales ciudades con el mejor potencial de valorización.',
  },
  {
    icon: '⊡',
    title: 'Mercado USA',
    desc: 'Accede a Miami, Nueva York, Dallas, Austin y Orlando con estructura legal y fiscal optimizada.',
  },
  {
    icon: '◎',
    title: 'Gestión patrimonial',
    desc: 'Wealth management inmobiliario para portafolios multi-activo en USD y COP.',
  },
  {
    icon: '⊕',
    title: 'Desarrollos',
    desc: 'Proyectos en preventa con retornos superiores al mercado secundario. Selección rigurosa.',
  },
]

export default function ServicesSection() {
  return (
    <section id="servicios" style={s.section}>
      <div style={s.inner}>
        <p style={s.eyebrow}>CÓMO TRABAJAMOS</p>
        <h2 style={s.h2}>Cómo construimos tu patrimonio</h2>
        <p style={s.intro}>
          Cinco líneas de negocio especializadas. Un solo asesor que entiende el panorama completo.
        </p>
        <div className="services-grid">
          {SERVICES.map(({ icon, title, desc }) => (
            <div key={title} className="service-item" style={s.item}>
              <span style={s.icon} aria-hidden="true">{icon}</span>
              <h3 style={s.itemTitle}>{title}</h3>
              <p style={s.itemDesc}>{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

const s = {
  section: {
    background: '#F4F6FB',
    width: '100%',
  },
  inner: {
    maxWidth: 1280,
    margin: '0 auto',
    padding: '8rem 4rem',
  },
  eyebrow: {
    fontFamily: "'Inter', sans-serif",
    fontWeight: 600,
    fontSize: 12,
    letterSpacing: '0.1em',
    textTransform: 'uppercase',
    color: '#0251FD',
    marginBottom: '1rem',
  },
  h2: {
    fontFamily: "'Montserrat', sans-serif",
    fontWeight: 700,
    fontSize: 'clamp(28px, 4vw, 48px)',
    color: '#081D67',
    lineHeight: 1.1,
    marginBottom: '1rem',
  },
  intro: {
    fontSize: 18,
    color: '#4A5680',
    marginBottom: '3.5rem',
    maxWidth: 540,
  },
  item: {
    background: '#fff',
    borderRadius: 24,
    padding: '2rem',
    boxShadow: '0 8px 24px rgba(8,29,103,0.06)',
  },
  icon: {
    display: 'block',
    fontSize: 28,
    color: '#0251FD',
    marginBottom: '1.25rem',
  },
  itemTitle: {
    fontFamily: "'Montserrat', sans-serif",
    fontWeight: 700,
    fontSize: 18,
    color: '#081D67',
    marginBottom: '0.75rem',
  },
  itemDesc: {
    fontSize: 15,
    color: '#4A5680',
    lineHeight: 1.65,
  },
}
