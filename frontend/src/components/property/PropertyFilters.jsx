import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { digitsOnly, groupThousands, minorToMajor, normalizePriceRange } from '../../lib/money'
import LocationFilter from './LocationFilter'

// Build the form state from the current URL so the controls always reflect the
// active query (deep links, back/forward, category pills) — not just first mount.
const fromParams = (params, defaultCurrency) => ({
  q: params.get('q') || '',
  location: params.get('location') || '',
  operation_type: params.get('operation_type') || '',
  property_kind: params.get('property_kind') || '',
  // shown to the user in pesos/dollars; the URL/API keeps minor units
  min_price: minorToMajor(params.get('min_price')),
  max_price: minorToMajor(params.get('max_price')),
  currency: params.get('currency') || (['us', 'usa', 'estados-unidos'].includes(params.get('country')) ? 'USD' : defaultCurrency),
  min_bedrooms: params.get('min_bedrooms') || '',
})

export default function PropertyFilters({ basePath = '/propiedades', defaultCurrency = 'COP' }) {
  const [params] = useSearchParams()
  const navigate = useNavigate()

  const [filters, setFilters] = useState(() => fromParams(params, defaultCurrency))
  // Cache for the location hierarchy, hoisted so it survives URL-driven re-syncs.
  const [locations, setLocations] = useState([])

  // Keep the form in sync with the URL — fixes stale selects (and the resulting
  // "wrong results" when an applied filter still carried a previous value).
  const search = params.toString()
  useEffect(() => {
    setFilters(fromParams(params, defaultCurrency))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, defaultCurrency])

  const apply = (e) => {
    e.preventDefault()
    const p = new URLSearchParams()
    // preserve a country/market preset already in the URL (e.g. Mercado USA)
    if (params.get('country')) p.set('country', params.get('country'))
    Object.entries(filters).forEach(([k, v]) => {
      if (!v) return
      if (!['min_price', 'max_price', 'currency'].includes(k)) {
        p.set(k, v)
      }
    })
    const range = normalizePriceRange(filters.min_price, filters.max_price)
    if (range.min_price != null) p.set('min_price', String(range.min_price))
    if (range.max_price != null) p.set('max_price', String(range.max_price))
    if (range.min_price != null || range.max_price != null) p.set('currency', filters.currency)
    p.set('page', '1')
    navigate(`${basePath}?${p.toString()}`)
  }

  const reset = () => {
    setFilters({ q: '', location: '', operation_type: '', property_kind: '', min_price: '', max_price: '', currency: params.get('country') === 'us' ? 'USD' : defaultCurrency, min_bedrooms: '' })
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

  const priceField = (label, key) => (
    <div className="fld">
      <label>{label} ({filters.currency})</label>
      <input
        type="text"
        inputMode="numeric"
        autoComplete="off"
        placeholder={filters.currency === 'COP' ? 'Ej: 350.000.000' : 'Ej: 250.000'}
        value={groupThousands(filters[key])}
        onChange={(e) => setFilters({ ...filters, [key]: digitsOnly(e.target.value) })}
      />
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
      {field('Moneda del precio', 'currency', 'text', [['COP', 'Pesos colombianos (COP)'], ['USD', 'Dólares (USD)']])}
      {priceField('Precio mín.', 'min_price')}
      {priceField('Precio máx.', 'max_price')}
      {field('Habitaciones mín.', 'min_bedrooms', 'number')}
      <button type="submit" className="btn btn-blue" style={{ width: '100%', justifyContent: 'center', marginBottom: 8 }}>Aplicar filtros</button>
      <button type="button" onClick={reset} className="btn btn-outline" style={{ width: '100%', justifyContent: 'center' }}>Limpiar</button>
    </form>
  )
}
