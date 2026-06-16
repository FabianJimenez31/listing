import { useEffect, useState } from 'react'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../../contexts/AuthContext'
import { createPartner, deletePartner, getPartners } from '../../api/partners'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import { IconUsers } from '../../components/admin/adminIcons'
import Spinner from '../../components/ui/Spinner'

const EMPTY = { name: '', kind: 'inmobiliaria', logo_url: '', website: '', priority: 0, is_active: true }

export default function AdminPartnersPage() {
  const { user } = useAuth()
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

  useEffect(() => { if (user) load() }, [user])

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

  if (loading) return <Spinner />

  return (
    <>
      <Helmet><title>Aliados | Listing Admin</title></Helmet>
      <AdminPageHeader
        title="Aliados"
        subtitle="Constructoras e inmobiliarias asociadas"
        count={items.length}
        actions={(
          <button className="btn btn-blue" onClick={() => setShowForm((v) => !v)}>
            {showForm ? 'Cancelar' : '+ Nuevo'}
          </button>
        )}
      />

      {showForm && (
        <form className="admin-card admin-card-form" onSubmit={submit}>
          <h3 className="admin-card-title">Nuevo aliado</h3>
          {error && <p className="admin-error">{error}</p>}
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
        <div className="adm-empty">
          <span className="ico"><IconUsers size={26} /></span>
          <b>Sin aliados</b>
          No hay aliados registrados todavía.
        </div>
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
    </>
  )
}
