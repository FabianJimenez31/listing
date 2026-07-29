import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { majorToMinor, minorToMajor } from '../../lib/money'
import LocationFilter from './LocationFilter'

// Build the form state from the current URL so the controls always reflect the
// active query (deep links, back/forward, category pills) — not just first mount.
const fromParams = (params) => ({
  q: params.get('q') || '',
  location: params.get('location') || '',
  operation_type: params.get('operation_type') || '',
  property_kind: params.get('property_kind') || '',
  // shown to the user in pesos/dollars; the URL/API keeps minor units
  min_price: minorToMajor(params.get('min_price')),
  max_price: minorToMajor(params.get('max_price')),
  min_bedrooms: params.get('min_bedrooms') || '',
})

export default function PropertyFilters({ basePath = '/propiedades' }) {
  const [params] = useSearchParams()
  const navigate = useNavigate()

  const [filters, setFilters] = useState(() => fromParams(params))
  // Cache for the location hierarchy, hoisted so it survives URL-driven re-syncs.
  const [locations, setLocations] = useState([])

  // Keep the form in sync with the URL — fixes stale selects (and the resulting
  // "wrong results" when an applied filter still carried a previous value).
  const search = params.toString()
  useEffect(() => {
    setFilters(fromParams(params))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search])

  const apply = (e) => {
    e.preventDefault()
    const p = new URLSearchParams()
    // preserve a country/market preset already in the URL (e.g. Mercado USA)
    if (params.get('country')) p.set('country', params.get('country'))
    Object.entries(filters).forEach(([k, v]) => {
      if (!v) return
      if (k === 'min_price' || k === 'max_price') {
        const minor = majorToMinor(v)
        if (minor != null) p.set(k, String(minor))
      } else {
        p.set(k, v)
      }
    })
    p.set('page', '1')
    navigate(`${basePath}?${p.toString()}`)
  }

  const reset = () => {
    setFilters({ q: '', location: '', operation_type: '', property_kind: '', min_price: '', max_price: '', min_bedrooms: '' })
    const p = new URLSearchParams()
    if (params.get('country')) p.set('country', params.get('country'))
    navigate(p.toString() ? `${basePath}?${p}` : basePath)
  }

  const field = (label, key, type = 'text', options = null) => (
    <div className="fld">
      <label>{label}</label>
      {options ? (
        <select value={filters[key]} onChange={(e) => setFilters({ ...filters, [key]: e.target.value })}>
          <option value="">Todos</option>
          {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      ) : (
        <input type={type} value={filters[key]} onChange={(e) => setFilters({ ...filters, [key]: e.target.value })} />
      )}
    </div>
  )

  return (
    <form onSubmit={apply} className="filters-card">
      <h3>Filtros</h3>
      {field('Buscar', 'q')}
      <LocationFilter
        value={filters.location}
        onChange={(slug) => setFilters((f) => ({ ...f, location: slug }))}
        all={locations}
        setAll={setLocations}
      />
      {field('Operación', 'operation_type', 'text', [['sale', 'Venta'], ['rent', 'Arriendo'], ['temporary', 'Temporal']])}
      {field('Tipo', 'property_kind', 'text', [['house', 'Casa'], ['apartment', 'Apartamento'], ['studio', 'Apartaestudio'], ['lot', 'Lote'], ['office', 'Oficina'], ['commercial', 'Local comercial']])}
      {field('Precio mín.', 'min_price', 'number')}
      {field('Precio máx.', 'max_price', 'number')}
      {field('Habitaciones mín.', 'min_bedrooms', 'number')}
      <button type="submit" className="btn btn-blue" style={{ width: '100%', justifyContent: 'center', marginBottom: 8 }}>Aplicar filtros</button>
      <button type="button" onClick={reset} className="btn btn-outline" style={{ width: '100%', justifyContent: 'center' }}>Limpiar</button>
    </form>
  )
}
