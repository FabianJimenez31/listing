import { useEffect, useState } from 'react'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../../contexts/AuthContext'
import { getFeatured, createFeatured, deleteFeatured } from '../../api/admin'
import { searchProperties } from '../../api/properties'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import { IconStar } from '../../components/admin/adminIcons'
import Spinner from '../../components/ui/Spinner'

const SCOPES = [
  { value: 'home', label: 'Inicio' },
  { value: 'search', label: 'Resultados' },
  { value: 'locality', label: 'Localidad' },
]

const EMPTY_FORM = { property_id: '', scope: 'home', locality_id: '', priority: 1, expires_at: '' }

export default function FeaturedPage() {
  const { user } = useAuth()
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
      .then((r) => setItems(Array.isArray(r) ? r : (r.data || [])))
      .catch(() => null)
      .finally(() => setLoading(false))
  }

  useEffect(() => { if (user) load() }, [user])

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

  if (loading) return <Spinner />

  return (
    <>
      <Helmet><title>Destacados | Listing Admin</title></Helmet>

      <AdminPageHeader title="Destacados" subtitle="Propiedades resaltadas en el portal" />

      <form onSubmit={handleSubmit} className="admin-card admin-card-form">
        <h3 className="admin-card-title">Agregar destacado</h3>

        <div className="form-grid">
          <div className="fg full adm-combo">
            <label>Propiedad</label>
            <input
              placeholder="Buscar propiedad por título…"
              value={propSearch}
              onChange={(e) => { setPropSearch(e.target.value); setForm((f) => ({ ...f, property_id: '' })) }}
            />
            {propLoading && <span style={{ fontSize: 12, color: 'var(--muted)' }}>Buscando…</span>}
            {form.property_id && <p className="mono" style={{ marginTop: 4, color: 'var(--green)' }}>ID: {form.property_id}</p>}
            {propResults.length > 0 && (
              <div className="adm-dropdown">
                {propResults.map((p) => (
                  <button type="button" key={p.id} onClick={() => selectProp(p)}>
                    <strong>{p.title}</strong>
                    <span style={{ color: 'var(--muted)' }}>{p.status}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="fg">
            <label>Ámbito</label>
            <select value={form.scope} onChange={(e) => setForm((f) => ({ ...f, scope: e.target.value }))}>
              {SCOPES.map((sc) => <option key={sc.value} value={sc.value}>{sc.label}</option>)}
            </select>
          </div>

          {form.scope === 'locality' && (
            <div className="fg">
              <label>ID de Localidad</label>
              <input
                placeholder="UUID de la localidad"
                value={form.locality_id}
                onChange={(e) => setForm((f) => ({ ...f, locality_id: e.target.value }))}
              />
            </div>
          )}

          <div className="fg">
            <label>Prioridad (menor = más alto)</label>
            <input type="number" min={1} max={100} value={form.priority} onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))} />
          </div>

          <div className="fg">
            <label>Expira (opcional)</label>
            <input type="datetime-local" value={form.expires_at} onChange={(e) => setForm((f) => ({ ...f, expires_at: e.target.value }))} />
          </div>
        </div>

        {error && <p className="admin-error" style={{ marginTop: 12 }}>{error}</p>}

        <button type="submit" className="btn btn-blue" style={{ marginTop: 16 }} disabled={saving}>
          {saving ? 'Guardando…' : 'Agregar destacado'}
        </button>
      </form>

      <p className="admin-section-title">Activos ({items.length})</p>

      {items.length === 0 ? (
        <div className="adm-empty">
          <span className="ico"><IconStar size={26} /></span>
          <b>Sin destacados</b>
          No hay propiedades destacadas activas.
        </div>
      ) : (
        <div className="adm-table">
          <div className="adm-thead">
            <span className="col4">Propiedad</span>
            <span className="col2">Ámbito</span>
            <span className="col1">Prioridad</span>
            <span className="col2">Expira</span>
            <span className="col1">Acción</span>
          </div>
          {items.map((item) => (
            <div key={item.id} className="adm-row">
              <span className="col4 mono">{item.property_id}</span>
              <span className="col2"><span className="tag">{item.scope}</span></span>
              <span className="col1">{item.priority}</span>
              <span className="col2" style={{ color: 'var(--muted)', fontSize: 13 }}>
                {item.expires_at ? new Date(item.expires_at).toLocaleDateString('es-CO') : '—'}
              </span>
              <span className="col1">
                <button onClick={() => handleDelete(item.id)} className="btn btn-outline btn-sm btn-danger">Eliminar</button>
              </span>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
