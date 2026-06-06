import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { searchProperties, getBanners, getFeatured } from '../api/properties'
import PropertyCard from '../components/property/PropertyCard'
import Spinner from '../components/ui/Spinner'

export default function HomePage() {
  const navigate = useNavigate()
  const [featured, setFeatured] = useState([])
  const [banners, setBanners] = useState([])
  const [loading, setLoading] = useState(true)
  const [q, setQ] = useState('')

  useEffect(() => {
    Promise.all([
      getFeatured('home').catch(() => ({ data: [] })),
      getBanners('HOME_HERO').catch(() => ({ data: [] })),
    ]).then(([feat, ban]) => {
      setFeatured(feat.data || [])
      setBanners(ban.data || [])
    }).finally(() => setLoading(false))
  }, [])

  const search = (e) => {
    e.preventDefault()
    navigate(`/propiedades${q ? `?q=${encodeURIComponent(q)}` : ''}`)
  }

  return (
    <>
      <Helmet>
        <title>Listing Colombia — Propiedades en venta y arriendo</title>
        <meta name="description" content="Encuentra tu propiedad ideal en Colombia. Apartamentos, casas y locales en venta y arriendo en Bogotá y más ciudades." />
      </Helmet>

      {/* Hero */}
      <section style={styles.hero}>
        {banners[0] && (
          <a href={banners[0].cta_url || '#'} target="_blank" rel="noopener noreferrer" style={styles.bannerLink}>
            <img src={banners[0].image_desktop_url} alt={banners[0].title} style={styles.heroBanner} />
          </a>
        )}
        <div style={styles.heroContent}>
          <h1 style={styles.heroTitle}>Encuentra tu propiedad ideal en Colombia</h1>
          <form onSubmit={search} style={styles.searchBar}>
            <input
              style={styles.searchInput}
              placeholder="Barrio, ciudad, tipo de inmueble…"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
            <button type="submit" style={styles.searchBtn}>Buscar</button>
          </form>
        </div>
      </section>

      {/* Featured */}
      <section style={styles.section}>
        <h2 style={styles.sectionTitle}>Propiedades destacadas</h2>
        {loading ? (
          <Spinner />
        ) : featured.length === 0 ? (
          <p style={styles.empty}>No hay propiedades destacadas en este momento.</p>
        ) : (
          <div style={styles.grid}>
            {featured.map((fp) => fp.property && (
              <PropertyCard key={fp.id} property={fp.property} />
            ))}
          </div>
        )}
      </section>

      {/* CTA */}
      <section style={styles.ctaSection}>
        <h2 style={styles.ctaTitle}>¿Tienes una propiedad para vender o rentar?</h2>
        <p style={styles.ctaText}>Publica gratis y llega a miles de compradores.</p>
        <button onClick={() => navigate('/registro')} style={styles.ctaBtn}>
          Publicar propiedad
        </button>
      </section>
    </>
  )
}

const styles = {
  hero: { position: 'relative', borderRadius: 12, overflow: 'hidden', marginBottom: '2.5rem', minHeight: 280, background: '#1a1a2e', display: 'flex', alignItems: 'center' },
  heroBanner: { position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', opacity: 0.35 },
  bannerLink: { position: 'absolute', inset: 0 },
  heroContent: { position: 'relative', zIndex: 1, padding: '3rem 2rem', width: '100%' },
  heroTitle: { color: '#fff', fontSize: 'clamp(1.5rem,4vw,2.5rem)', margin: '0 0 1.5rem', fontWeight: 700 },
  searchBar: { display: 'flex', maxWidth: 600, gap: 0 },
  searchInput: { flex: 1, padding: '12px 16px', fontSize: 16, border: 'none', borderRadius: '8px 0 0 8px', outline: 'none' },
  searchBtn: { background: '#e94560', color: '#fff', border: 'none', padding: '12px 24px', borderRadius: '0 8px 8px 0', fontSize: 16, fontWeight: 600, cursor: 'pointer' },
  section: { marginBottom: '3rem' },
  sectionTitle: { fontSize: 22, color: '#1a1a2e', marginBottom: '1.25rem' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(280px,1fr))', gap: '1.5rem' },
  empty: { color: '#888', textAlign: 'center', padding: '2rem' },
  ctaSection: { background: '#1a1a2e', borderRadius: 12, padding: '3rem 2rem', textAlign: 'center', marginBottom: '2rem' },
  ctaTitle: { color: '#fff', fontSize: 22, margin: '0 0 .5rem' },
  ctaText: { color: '#ccc', marginBottom: '1.5rem' },
  ctaBtn: { background: '#e94560', color: '#fff', border: 'none', borderRadius: 8, padding: '12px 32px', fontSize: 16, fontWeight: 600, cursor: 'pointer' },
}
