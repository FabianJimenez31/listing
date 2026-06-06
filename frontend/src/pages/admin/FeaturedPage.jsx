import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../../contexts/AuthContext'
import { getFeatured, createFeatured, deleteFeatured } from '../../api/admin'
import { searchProperties } from '../../api/properties'
import Spinner from '../../components/ui/Spinner'

const SCOPES = [
  { value: 'home', label: 'Inicio' },
  { value: 'search', label: 'Resultados' },
  { value: 'locality', label: 'Localidad' },
]

const EMPTY_FORM = { property_id: '', scope: 'home', locality_id: '', priority: 1, expires_at: '' }

export default function FeaturedPage() {
  const { user, loading: authLoading, isAdmin } = useAuth()
  const navigate = useNavigate()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState(EMPTY_FORM)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [propSearch, setPropSearch] = useState('')
  const [propResults, setPropResults] = useState([])
  const [propLoading, setPropLoading] = useState(false)

  const load = () => {
    setLoading(true)
    getFeatured()
      .then((r) => setItems(r.data || []))
      .catch(() => null)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (!authLoading) {
      if (!user) { navigate('/login'); return }
      if (!isAdmin()) { navigate('/agente'); return }
    }
    if (user) load()
  }, [user, authLoading])

  useEffect(() => {
    if (!propSearch.trim()) { setPropResults([]); return }
    const t = setTimeout(() => {
      setPropLoading(true)
      searchProperties({ q: propSearch, page_size: 6 })
        .then((r) => setPropResults(r.data || []))
        .catch(() => null)
        .finally(() => setPropLoading(false))
    }, 350)
    return () => clearTimeout(t)
  }, [propSearch])

  const handleSubmit = (e) => {
    e.preventDefault()
    setError('')
    if (!form.property_id) { setError('Selecciona una propiedad'); return }
    setSaving(true)
    const payload = {
      property_id: form.property_id,
      scope: form.scope,
      priority: Number(form.priority) || 1,
      ...(form.scope === 'locality' && form.locality_id ? { locality_id: form.locality_id } : {}),
      ...(form.expires_at ? { expires_at: form.expires_at } : {}),
    }
    createFeatured(payload)
      .then(() => { setForm(EMPTY_FORM); setPropSearch(''); setPropResults([]); load() })
      .catch((err) => setError(err.response?.data?.error?.message || 'Error al guardar'))
      .finally(() => setSaving(false))
  }

  const handleDelete = (id) => {
    if (!window.confirm('¿Eliminar propiedad destacada?')) return
    deleteFeatured(id).then(load).catch(() => null)
  }

  const selectProp = (p) => {
    setForm((f) => ({ ...f, property_id: p.id }))
    setPropSearch(p.title)
    setPropResults([])
  }

  if (authLoading || loading) return <Spinner />

  return (
    <>
      <Helmet><title>Destacados | Listing Admin</title></Helmet>

      <div style={s.header}>
        <button onClick={() => navigate('/admin')} style={s.back}>← Admin</button>
        <h1 style={s.h1}>Propiedades Destacadas</h1>
      </div>

      <form onSubmit={handleSubmit} style={s.form}>
        <h2 style={s.h2}>Agregar Destacado</h2>

        <label style={s.label}>Propiedad</label>
        <div style={{ position: 'relative' }}>
          <input
            style={s.input}
            placeholder="Buscar propiedad por título…"
            value={propSearch}
            onChange={(e) => { setPropSearch(e.target.value); setForm((f) => ({ ...f, property_id: '' })) }}
          />
          {propLoading && <span style={s.searching}>Buscando…</span>}
          {propResults.length > 0 && (
            <div style={s.dropdown}>
              {propResults.map((p) => (
                <div key={p.id} style={s.dropItem} onClick={() => selectProp(p)}>
                  <strong style={{ fontSize: 13 }}>{p.title}</strong>
                  <span style={{ fontSize: 12, color: '#888', marginLeft: 8 }}>{p.status}</span>
                </div>
              ))}
            </div>
          )}
        </div>
        {form.property_id && <p style={s.selected}>ID: {form.property_id}</p>}

        <label style={s.label}>Ámbito</label>
        <select style={s.input} value={form.scope} onChange={(e) => setForm((f) => ({ ...f, scope: e.target.value }))}>
          {SCOPES.map((sc) => <option key={sc.value} value={sc.value}>{sc.label}</option>)}
        </select>

        {form.scope === 'locality' && (
          <>
            <label style={s.label}>ID de Localidad</label>
            <input
              style={s.input}
              placeholder="UUID de la localidad"
              value={form.locality_id}
              onChange={(e) => setForm((f) => ({ ...f, locality_id: e.target.value }))}
            />
          </>
        )}

        <label style={s.label}>Prioridad (menor = más alto)</label>
        <input
          style={s.input}
          type="number"
          min={1}
          max={100}
          value={form.priority}
          onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}
        />

        <label style={s.label}>Expira (opcional)</label>
        <input
          style={s.input}
          type="datetime-local"
          value={form.expires_at}
          onChange={(e) => setForm((f) => ({ ...f, expires_at: e.target.value }))}
        />

        {error && <p style={s.error}>{error}</p>}

        <button type="submit" style={s.btn} disabled={saving}>
          {saving ? 'Guardando…' : 'Agregar Destacado'}
        </button>
      </form>

      <h2 style={{ ...s.h2, marginTop: '2rem' }}>
        Activos ({items.length})
      </h2>

      {items.length === 0 ? (
        <p style={s.empty}>No hay propiedades destacadas activas.</p>
      ) : (
        <div style={s.table}>
          <div style={s.thead}>
            <span style={s.c4}>Propiedad</span>
            <span style={s.c2}>Ámbito</span>
            <span style={s.c1}>Prioridad</span>
            <span style={s.c2}>Expira</span>
            <span style={s.c1}>Acción</span>
          </div>
          {items.map((item) => (
            <div key={item.id} style={s.row}>
              <span style={{ ...s.c4, fontFamily: 'monospace', fontSize: 12, color: '#555' }}>
                {item.property_id}
              </span>
              <span style={s.c2}>{item.scope}</span>
              <span style={s.c1}>{item.priority}</span>
              <span style={{ ...s.c2, color: '#888', fontSize: 12 }}>
                {item.expires_at ? new Date(item.expires_at).toLocaleDateString('es-MX') : '—'}
              </span>
              <span style={s.c1}>
                <button onClick={() => handleDelete(item.id)} style={s.del}>Eliminar</button>
              </span>
            </div>
          ))}
        </div>
      )}
    </>
  )
}

const s = {
  header: { display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' },
  back: { background: 'none', border: 'none', color: '#e94560', cursor: 'pointer', fontSize: 14 },
  h1: { fontSize: 22, color: '#1a1a2e', margin: 0 },
  h2: { fontSize: 17, color: '#1a1a2e', margin: '0 0 1rem' },
  form: { background: '#fff', borderRadius: 10, padding: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,.07)', marginBottom: '2rem', maxWidth: 560 },
  label: { display: 'block', fontSize: 13, fontWeight: 600, color: '#555', marginBottom: 4, marginTop: 12 },
  input: { width: '100%', padding: '9px 12px', border: '1px solid #ddd', borderRadius: 8, fontSize: 14, boxSizing: 'border-box' },
  searching: { position: 'absolute', right: 10, top: 10, fontSize: 12, color: '#888' },
  dropdown: { position: 'absolute', top: '100%', left: 0, right: 0, background: '#fff', border: '1px solid #ddd', borderRadius: 8, zIndex: 10, boxShadow: '0 4px 12px rgba(0,0,0,.1)', maxHeight: 200, overflowY: 'auto' },
  dropItem: { padding: '10px 14px', cursor: 'pointer', borderBottom: '1px solid #f5f5f5', display: 'flex', alignItems: 'center' },
  selected: { fontSize: 12, color: '#2d6a4f', margin: '4px 0 0', fontFamily: 'monospace' },
  btn: { marginTop: 16, background: '#e94560', color: '#fff', border: 'none', borderRadius: 8, padding: '10px 20px', fontSize: 14, fontWeight: 600, cursor: 'pointer' },
  error: { color: '#c0392b', fontSize: 13, margin: '8px 0 0' },
  table: { background: '#fff', borderRadius: 10, overflow: 'hidden', boxShadow: '0 2px 8px rgba(0,0,0,.07)' },
  thead: { display: 'flex', padding: '10px 16px', background: '#f8f8f8', borderBottom: '1px solid #eee', fontWeight: 600, fontSize: 13, color: '#555' },
  row: { display: 'flex', padding: '10px 16px', borderBottom: '1px solid #f5f5f5', fontSize: 14, alignItems: 'center' },
  c4: { flex: 4, paddingRight: 8 },
  c2: { flex: 2, paddingRight: 8 },
  c1: { flex: 1, paddingRight: 8 },
  empty: { color: '#888', textAlign: 'center', padding: '2rem' },
  del: { background: 'none', border: '1px solid #e94560', color: '#e94560', borderRadius: 6, padding: '4px 10px', fontSize: 12, cursor: 'pointer' },
}
