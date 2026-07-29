import { useEffect, useState } from 'react'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../../contexts/AuthContext'
import { createAgency, deleteAgency, getAgencies, updateAgency } from '../../api/agencies'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import { IconOffice } from '../../components/admin/adminIcons'
import Spinner from '../../components/ui/Spinner'

const EMPTY = {
  name: '', initials: '', logo_url: '', description: '',
  phone: '', email: '', whatsapp: '', website: '', is_verified: false, is_active: true,
}

export default function AdminAgenciesPage() {
  const { user } = useAuth()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState(EMPTY)
  const [editId, setEditId] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const load = () => {
    setLoading(true)
    getAgencies().then(setItems).catch(() => setItems([])).finally(() => setLoading(false))
  }

  useEffect(() => { if (user) load() }, [user])

  const upd = (k) => (e) =>
    setForm((f) => ({ ...f, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }))
  const startNew = () => { setForm(EMPTY); setEditId(null); setShowForm(true) }
  const startEdit = (a) => { setForm({ ...EMPTY, ...a }); setEditId(a.id); setShowForm(true); window.scrollTo({ top: 0 }) }

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      if (editId) await updateAgency(editId, form)
      else await createAgency(form)
      setShowForm(false); setForm(EMPTY); setEditId(null); load()
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Error al guardar')
    } finally {
      setSaving(false)
    }
  }

  const remove = async (id) => {
    if (!confirm('¿Eliminar esta inmobiliaria?')) return
    await deleteAgency(id).catch(() => null)
    load()
  }

  if (loading) return <Spinner />

  return (
    <>
      <Helmet><title>Inmobiliarias | Listing Admin</title></Helmet>
      <AdminPageHeader
        title="Inmobiliarias"
        subtitle="Agencias e inmobiliarias del portal"
        count={items.length}
        actions={(
          <button className="btn btn-blue" onClick={showForm ? () => setShowForm(false) : startNew}>
            {showForm ? 'Cancelar' : '+ Nueva'}
          </button>
        )}
      />

      {showForm && (
        <form className="admin-card admin-card-form" onSubmit={submit}>
          <h3 className="admin-card-title">{editId ? 'Editar' : 'Nueva'} inmobiliaria</h3>
          {error && <p className="admin-error">{error}</p>}
          <div className="form-grid">
            <div className="fg"><label>Nombre *</label><input required value={form.name} onChange={upd('name')} /></div>
            <div className="fg"><label>Iniciales</label><input maxLength={8} value={form.initials} onChange={upd('initials')} /></div>
            <div className="fg full"><label>Logo URL</label><input value={form.logo_url} onChange={upd('logo_url')} /></div>
            <div className="fg full"><label>Descripción</label><textarea rows={2} value={form.description} onChange={upd('description')} /></div>
            <div className="fg"><label>Teléfono</label><input value={form.phone} onChange={upd('phone')} /></div>
            <div className="fg"><label>WhatsApp</label><input value={form.whatsapp} onChange={upd('whatsapp')} /></div>
            <div className="fg"><label>Email</label><input value={form.email} onChange={upd('email')} /></div>
            <div className="fg"><label>Website</label><input value={form.website} onChange={upd('website')} /></div>
            <div className="fg check"><input type="checkbox" id="ver" checked={form.is_verified} onChange={upd('is_verified')} /><label htmlFor="ver" style={{ margin: 0 }}>Verificada</label></div>
            <div className="fg check"><input type="checkbox" id="act" checked={form.is_active} onChange={upd('is_active')} /><label htmlFor="act" style={{ margin: 0 }}>Activa</label></div>
          </div>
          <button className="btn btn-blue" disabled={saving} style={{ marginTop: 14 }}>
            {saving ? 'Guardando…' : editId ? 'Guardar cambios' : 'Crear inmobiliaria'}
          </button>
        </form>
      )}

      {items.length === 0 ? (
        <div className="adm-empty">
          <span className="ico"><IconOffice size={26} /></span>
          <b>Sin inmobiliarias</b>
          No hay inmobiliarias registradas todavía.
        </div>
      ) : (
        <div className="adm-table">
          {items.map((a) => (
            <div className="adm-row" key={a.id}>
              <span className="tag">{a.initials || a.name.slice(0, 2).toUpperCase()}</span>
              <div className="grow">
                <div className="name">{a.name}{a.is_verified ? ' ✓' : ''}</div>
                <div className="sub">{a.property_count} propiedades{a.is_active ? '' : ' · inactiva'}</div>
              </div>
              <button className="btn btn-outline btn-sm" onClick={() => startEdit(a)}>Editar</button>
              <button className="btn btn-outline btn-sm btn-danger" onClick={() => remove(a.id)}>Eliminar</button>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
