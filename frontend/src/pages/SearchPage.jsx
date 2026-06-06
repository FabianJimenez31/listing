import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { searchProperties } from '../api/properties'
import PropertyCard from '../components/property/PropertyCard'
import PropertyFilters from '../components/property/PropertyFilters'
import Pagination from '../components/ui/Pagination'
import Spinner from '../components/ui/Spinner'

export default function SearchPage() {
  const [searchParams] = useSearchParams()
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const params = Object.fromEntries(searchParams.entries())

  useEffect(() => {
    setLoading(true)
    setError(null)
    searchProperties({ page_size: 12, ...params })
      .then(setResult)
      .catch((e) => setError(e.message || 'Error al buscar propiedades'))
      .finally(() => setLoading(false))
  }, [searchParams.toString()])

  const handlePage = (page) => {
    const next = new URLSearchParams(searchParams)
    next.set('page', page)
    window.location.search = next.toString()
  }

  const q = params.q || ''
  const total = result?.meta?.total ?? 0

  return (
    <>
      <Helmet>
        <title>{q ? `"${q}" — Propiedades` : 'Propiedades'} | Listing</title>
        <meta name="description" content={`Resultados de búsqueda de propiedades. ${total} resultados encontrados.`} />
      </Helmet>

      <h1 style={styles.heading}>
        {q ? `Resultados para "${q}"` : 'Propiedades'}
        {result && <span style={styles.count}> — {total} resultado{total !== 1 ? 's' : ''}</span>}
      </h1>

      <div style={styles.layout}>
        <aside style={styles.sidebar}>
          <PropertyFilters />
        </aside>

        <div style={styles.main}>
          {loading ? (
            <Spinner />
          ) : error ? (
            <p style={styles.error}>{error}</p>
          ) : result?.data?.length === 0 ? (
            <div style={styles.empty}>
              <p>No se encontraron propiedades con los filtros seleccionados.</p>
            </div>
          ) : (
            <>
              <div style={styles.grid}>
                {result.data.map((p) => <PropertyCard key={p.id} property={p} />)}
              </div>
              <Pagination meta={result.meta} onPage={handlePage} />
            </>
          )}
        </div>
      </div>
    </>
  )
}

const styles = {
  heading: { fontSize: 22, color: '#1a1a2e', marginBottom: '1.5rem' },
  count: { fontSize: 16, color: '#888', fontWeight: 400 },
  layout: { display: 'grid', gridTemplateColumns: '240px 1fr', gap: '1.5rem', alignItems: 'start' },
  sidebar: {},
  main: {},
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(270px,1fr))', gap: '1.25rem' },
  empty: { background: '#fff', borderRadius: 10, padding: '3rem', textAlign: 'center', color: '#888' },
  error: { color: '#e94560', background: '#fff', borderRadius: 10, padding: '1.5rem', textAlign: 'center' },
}
