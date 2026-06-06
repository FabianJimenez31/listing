import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

export default function PropertyFilters() {
  const [params] = useSearchParams()
  const navigate = useNavigate()

  const [filters, setFilters] = useState({
    q: params.get('q') || '',
    operation_type: params.get('operation_type') || '',
    property_kind: params.get('property_kind') || '',
    min_price: params.get('min_price') || '',
    max_price: params.get('max_price') || '',
    min_bedrooms: params.get('min_bedrooms') || '',
  })

  const apply = (e) => {
    e.preventDefault()
    const p = new URLSearchParams()
    Object.entries(filters).forEach(([k, v]) => { if (v) p.set(k, v) })
    p.set('page', '1')
    navigate(`/propiedades?${p.toString()}`)
  }

  const reset = () => {
    setFilters({ q: '', operation_type: '', property_kind: '', min_price: '', max_price: '', min_bedrooms: '' })
    navigate('/propiedades')
  }

  const field = (label, key, type = 'text', options = null) => (
    <div style={styles.field}>
      <label style={styles.label}>{label}</label>
      {options ? (
        <select value={filters[key]} onChange={(e) => setFilters({ ...filters, [key]: e.target.value })} style={styles.input}>
          <option value="">Todos</option>
          {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      ) : (
        <input type={type} value={filters[key]} onChange={(e) => setFilters({ ...filters, [key]: e.target.value })} style={styles.input} />
      )}
    </div>
  )

  return (
    <form onSubmit={apply} style={styles.form}>
      <h3 style={styles.heading}>Filtros</h3>
      {field('Buscar', 'q')}
      {field('Operación', 'operation_type', 'text', [['sale', 'Venta'], ['rent', 'Renta'], ['temporary', 'Temporal']])}
      {field('Tipo', 'property_kind', 'text', [['house', 'Casa'], ['apartment', 'Apartamento'], ['lot', 'Terreno'], ['office', 'Oficina']])}
      {field('Precio mín. (centavos)', 'min_price', 'number')}
      {field('Precio máx. (centavos)', 'max_price', 'number')}
      {field('Recámaras mín.', 'min_bedrooms', 'number')}
      <button type="submit" style={styles.btnApply}>Aplicar</button>
      <button type="button" onClick={reset} style={styles.btnReset}>Limpiar</button>
    </form>
  )
}

const styles = {
  form: { background: '#fff', borderRadius: 10, padding: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,.07)', minWidth: 220 },
  heading: { margin: '0 0 1rem', fontSize: 16, color: '#1a1a2e' },
  field: { marginBottom: '1rem' },
  label: { display: 'block', fontSize: 13, color: '#555', marginBottom: 4 },
  input: { width: '100%', padding: '6px 10px', border: '1px solid #ddd', borderRadius: 6, fontSize: 14, boxSizing: 'border-box' },
  btnApply: { width: '100%', background: '#e94560', color: '#fff', border: 'none', borderRadius: 6, padding: '8px', cursor: 'pointer', fontWeight: 600, marginBottom: 8 },
  btnReset: { width: '100%', background: '#eee', color: '#333', border: 'none', borderRadius: 6, padding: '8px', cursor: 'pointer' },
}
