import { useEffect, useState } from 'react'
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { searchProperties } from '../api/properties'
import PropertyCard from '../components/property/PropertyCard'
import PropertyFilters from '../components/property/PropertyFilters'
import Pagination from '../components/ui/Pagination'
import Spinner from '../components/ui/Spinner'

export default function SearchPage({ forced = {}, title, subtitle }) {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const location = useLocation()
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const urlParams = Object.fromEntries(searchParams.entries())
  const params = { ...urlParams, ...forced }
  const key = JSON.stringify(params)

  useEffect(() => {
    setLoading(true)
    setError(null)
    searchProperties({ page_size: 12, ...params })
      .then(setResult)
      .catch((e) => setError(e.message || 'Error al buscar propiedades'))
      .finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])

  const handlePage = (page) => {
    const next = new URLSearchParams(searchParams)
    next.set('page', page)
    navigate(`${location.pathname}?${next}`)
  }

  const total = result?.meta?.total ?? 0
  const heading = title || (urlParams.q ? `Resultados para "${urlParams.q}"` : 'Propiedades')

  return (
    <div className="page-wrap">
      <Helmet>
        <title>{`${heading} | Proppietario`}</title>
        <meta name="description" content={`${total} propiedades encontradas en Proppietario.`} />
      </Helmet>

      <div className="sec-head" style={{ marginBottom: 24 }}>
        <div>
          <h2 style={{ fontSize: 28 }}>{heading}</h2>
          <p>{subtitle || (result ? `${total} resultado${total !== 1 ? 's' : ''}` : 'Cargando…')}</p>
        </div>
      </div>

      <div className="search-layout">
        <aside>
          <PropertyFilters basePath={location.pathname} />
        </aside>
        <div>
          {loading ? (
            <Spinner />
          ) : error ? (
            <p style={{ color: '#D7263D' }}>{error}</p>
          ) : result?.data?.length === 0 ? (
            <div style={{ background: 'var(--bg-soft)', borderRadius: 16, padding: '3rem', textAlign: 'center', color: 'var(--muted)', border: '1px solid var(--line)' }}>
              No se encontraron propiedades con los filtros seleccionados.
            </div>
          ) : (
            <>
              <div className="prop-grid">
                {result.data.map((p) => <PropertyCard key={p.id} property={p} />)}
              </div>
              <Pagination meta={result.meta} onPage={handlePage} />
            </>
          )}
        </div>
      </div>
    </div>
  )
}
