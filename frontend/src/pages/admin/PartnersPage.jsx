import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../../contexts/AuthContext'
import { createPartner, deletePartner, getPartners } from '../../api/partners'
import Spinner from '../../components/ui/Spinner'

const EMPTY = { name: '', kind: 'inmobiliaria', logo_url: '', website: '', priority: 0, is_active: true }

export default function AdminPartnersPage() {
  const { user, loading: authLoading, isAdmin } = useAuth()
  const navigate = useNavigate()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState(EMPTY)
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const load = () => {
    setLoading(true)
    getPartners().then(setItems).catch(() => setItems([])).finally(() => setLoading(false))
  }

  useEffect(() => {
    if (!authLoading) {
      if (!user) { navigate('/login'); return }
      if (!isAdmin()) { navigate('/agente'); return }
    }
    if (user) load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, authLoading])

  const upd = (k) => (e) =>
    setForm((f) => ({ ...f, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      await createPartner({ ...form, priority: parseInt(form.priority, 10) || 0 })
      setForm(EMPTY); setShowForm(false); load()
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Error al crear aliado')
    } finally {
      setSaving(false)
    }
  }

  const remove = async (id) => {
    if (!confirm('¿Eliminar este aliado?')) return
    await deletePartner(id).catch(() => null)
    load()
  }

  if (authLoading || loading) return <div className="page-wrap"><Spinner /></div>

  return (
    <div className="page-wrap">
      <Helmet><title>Aliados | Admin</title></Helmet>
      <div className="admin-head">
        <button className="admin-back" onClick={() => navigate('/admin')}>← Admin</button>
        <h1>Aliados ({items.length})</h1>
        <button className="btn btn-blue" onClick={() => setShowForm((v) => !v)}>{showForm ? 'Cancelar' : '+ Nuevo'}</button>
      </div>

      {showForm && (
        <form className="admin-card" onSubmit={submit}>
          <h3 style={{ fontWeight: 800, color: 'var(--ink)', marginBottom: 14 }}>Nuevo aliado</h3>
          {error && <p style={{ color: '#b91c1c', marginBottom: 10 }}>{error}</p>}
          <div className="form-grid">
            <div className="fg"><label>Nombre *</label><input required value={form.name} onChange={upd('name')} /></div>
            <div className="fg"><label>Tipo</label>
              <select value={form.kind} onChange={upd('kind')}>
                <option value="inmobiliaria">Inmobiliaria</option>
                <option value="constructora">Constructora</option>
              </select>
            </div>
            <div className="fg"><label>Logo URL</label><input value={form.logo_url} onChange={upd('logo_url')} /></div>
            <div className="fg"><label>Website</label><input value={form.website} onChange={upd('website')} /></div>
            <div className="fg"><label>Prioridad</label><input type="number" value={form.priority} onChange={upd('priority')} /></div>
            <div className="fg check"><input type="checkbox" id="pact" checked={form.is_active} onChange={upd('is_active')} /><label htmlFor="pact" style={{ margin: 0 }}>Activo</label></div>
          </div>
          <button className="btn btn-blue" disabled={saving} style={{ marginTop: 14 }}>{saving ? 'Guardando…' : 'Crear aliado'}</button>
        </form>
      )}

      {items.length === 0 ? (
        <p style={{ color: 'var(--muted)' }}>No hay aliados.</p>
      ) : (
        <div className="adm-table">
          {items.map((p) => (
            <div className="adm-row" key={p.id}>
              <div className="grow">
                <div className="name">{p.name}</div>
                <div className="sub">{p.kind} · prioridad {p.priority}{p.is_active ? '' : ' · inactivo'}</div>
              </div>
              <button className="btn btn-outline btn-sm btn-danger" onClick={() => remove(p.id)}>Eliminar</button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
