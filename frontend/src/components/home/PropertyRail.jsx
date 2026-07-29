import { useRef } from 'react'
import { Link } from 'react-router-dom'
import PropertyCard from '../property/PropertyCard'

export default function PropertyRail({ title, seeAllHref, items = [], loading = false }) {
  const railRef = useRef(null)

  const scroll = (dir) => {
    if (!railRef.current) return
    const first = railRef.current.firstChild
    const cardW = first ? first.getBoundingClientRect().width : 360
    railRef.current.scrollBy({ left: dir * (cardW + 20), behavior: 'smooth' })
  }

  if (!loading && items.length === 0) return null

  return (
    <section style={s.section}>
      <div style={s.inner}>
        <div style={s.header}>
          <h2 style={s.h2}>{title}</h2>
          <div style={s.headerRight}>
            {seeAllHref && (
              <Link to={seeAllHref} style={s.seeAll}>Ver todas →</Link>
            )}
            {items.length > 1 && (
              <div style={s.arrows}>
                <button
                  style={s.arrow}
                  onClick={() => scroll(-1)}
                  aria-label="Anterior"
                >‹</button>
                <button
                  style={s.arrow}
                  onClick={() => scroll(1)}
                  aria-label="Siguiente"
                >›</button>
              </div>
            )}
          </div>
        </div>

        {loading ? (
          <div style={s.skeletons}>
            {[1, 2, 3].map(i => (
              <div key={i} className="skeleton rail-card" style={s.skeletonCard} />
            ))}
          </div>
        ) : (
          <div ref={railRef} className="rail-scroll" role="region" aria-label={title}>
            {items.map(p => (
              <div key={p.id} className="rail-card">
                <PropertyCard property={p} />
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}

const s = {
  section: {
    padding: '5rem 0',
    width: '100%',
    background: '#fff',
  },
  inner: {
    maxWidth: 1280,
    margin: '0 auto',
    padding: '0 4rem',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '2rem',
    flexWrap: 'wrap',
    gap: '1rem',
  },
  h2: {
    fontFamily: "'Montserrat', sans-serif",
    fontWeight: 700,
    fontSize: 'clamp(22px, 3vw, 36px)',
    color: '#081D67',
    lineHeight: 1.1,
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '1.5rem',
  },
  seeAll: {
    color: '#0251FD',
    fontWeight: 600,
    fontSize: 15,
    textDecoration: 'none',
  },
  arrows: { display: 'flex', gap: '0.5rem' },
  arrow: {
    width: 40,
    height: 40,
    borderRadius: '50%',
    background: '#DDE8FF',
    border: 'none',
    cursor: 'pointer',
    fontSize: 20,
    color: '#0251FD',
    fontWeight: 700,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'background 150ms',
    lineHeight: 1,
  },
  skeletons: { display: 'flex', gap: '1.25rem', overflow: 'hidden' },
  skeletonCard: { height: 280, flexShrink: 0 },
}
