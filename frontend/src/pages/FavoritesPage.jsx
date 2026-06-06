import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../contexts/AuthContext'
import { getFavorites, removeFavorite } from '../api/favorites'
import PropertyCard from '../components/property/PropertyCard'
import Spinner from '../components/ui/Spinner'
import Pagination from '../components/ui/Pagination'

export default function FavoritesPage() {
  const { user, loading: authLoading } = useAuth()
  const navigate = useNavigate()
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)

  const load = (p = page) => {
    setLoading(true)
    getFavorites({ page: p, page_size: 12 })
      .then(setResult)
      .catch(() => null)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (!authLoading) {
      if (!user) { navigate('/login'); return }
    }
    if (user) load()
  }, [user, authLoading, page])

  const handleRemove = (propertyId) => {
    removeFavorite(propertyId)
      .then(() => load())
      .catch(() => null)
  }

  if (authLoading || loading) return <Spinner />

  const properties = result?.data || []

  return (
    <>
      <Helmet>
        <title>Mis Favoritos | Listing</title>
        <meta name="robots" content="noindex" />
      </Helmet>

      <div style={s.header}>
        <h1 style={s.h1}>Mis Favoritos</h1>
        <span style={s.count}>{result?.meta?.total ?? 0} propiedades</span>
      </div>

      {properties.length === 0 ? (
        <div style={s.empty}>
          <p style={{ fontSize: 18, color: '#555', marginBottom: '1rem' }}>
            Aún no tienes propiedades favoritas.
          </p>
          <button onClick={() => navigate('/propiedades')} style={s.cta}>
            Explorar propiedades
          </button>
        </div>
      ) : (
        <>
          <div style={s.grid}>
            {properties.map((fav) => {
              const prop = fav.property || fav
              return (
                <div key={fav.id || prop.id} style={{ position: 'relative' }}>
                  <PropertyCard property={prop} />
                  <button
                    style={s.removeBtn}
                    onClick={() => handleRemove(prop.id)}
                    title="Quitar de favoritos"
                  >
                    ♥ Quitar
                  </button>
                </div>
              )
            })}
          </div>
          <Pagination meta={result?.meta} onPage={(p) => setPage(p)} />
        </>
      )}
    </>
  )
}

const s = {
  header: { display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' },
  h1: { fontSize: 24, color: '#1a1a2e', margin: 0 },
  count: { fontSize: 14, color: '#888', background: '#f5f5f5', padding: '4px 10px', borderRadius: 20 },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1.5rem', marginBottom: '2rem' },
  removeBtn: {
    position: 'absolute', top: 10, right: 10,
    background: 'rgba(255,255,255,0.9)', border: '1px solid #e94560',
    color: '#e94560', borderRadius: 20, padding: '4px 10px',
    fontSize: 12, fontWeight: 600, cursor: 'pointer',
  },
  empty: { textAlign: 'center', padding: '4rem 1rem' },
  cta: { background: '#e94560', color: '#fff', border: 'none', borderRadius: 8, padding: '12px 24px', fontSize: 16, fontWeight: 600, cursor: 'pointer' },
}
