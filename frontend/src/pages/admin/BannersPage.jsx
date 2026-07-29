import { useEffect, useState } from 'react'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../../contexts/AuthContext'
import { getBanners, createBanner, deleteBanner } from '../../api/admin'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import { IconImage } from '../../components/admin/adminIcons'
import Spinner from '../../components/ui/Spinner'

const POSITIONS = ['HOME_HERO', 'HOME_INLINE', 'SEARCH_TOP', 'SEARCH_SIDEBAR', 'DETAIL_BOTTOM']

const EMPTY_BANNER = {
  title: '', position: 'HOME_HERO', image_desktop_url: '',
  image_mobile_url: '', cta_url: '', cta_text: '', priority: 0, is_active: true,
  starts_at: '', ends_at: '',
}

export default function BannersPage() {
  const { user } = useAuth()
  const [banners, setBanners] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState(EMPTY_BANNER)
  const [creating, setCreating] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [error, setError] = useState(null)

  const load = () => {
    setLoading(true)
    getBanners().then((r) => setBanners(r.data || r)).catch(() => null).finally(() => setLoading(false))
  }

  useEffect(() => { if (user) load() }, [user])

  const upd = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    setCreating(true)
    try {
      const payload = { ...form, priority: parseInt(form.priority, 10) || 0 }
      if (!payload.starts_at) delete payload.starts_at
      if (!payload.ends_at) delete payload.ends_at
      await createBanner(payload)
      setForm(EMPTY_BANNER)
      setShowForm(false)
      load()
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Error al crear banner')
    } finally {
      setCreating(false)
    }
  }

  const remove = async (id) => {
    if (!confirm('¿Eliminar este banner?')) return
    await deleteBanner(id).catch(() => null)
    load()
  }

  if (loading) return <Spinner />

  return (
    <>
      <Helmet><title>Banners | Listing Admin</title></Helmet>

      <AdminPageHeader
        title="Banners"
        subtitle="Piezas publicitarias del portal"
        count={banners.length}
        actions={(
          <button onClick={() => setShowForm(!showForm)} className="btn btn-blue">
            {showForm ? 'Cancelar' : '+ Nuevo banner'}
          </button>
        )}
      />

      {showForm && (
        <form onSubmit={submit} className="admin-card admin-card-form">
          <h3 className="admin-card-title">Nuevo banner</h3>
          {error && <p className="admin-error">{error}</p>}
          <div className="form-grid">
            {[['Título *', 'title'], ['URL imagen desktop *', 'image_desktop_url'], ['URL imagen mobile', 'image_mobile_url'], ['URL destino (CTA)', 'cta_url'], ['Texto CTA', 'cta_text']].map(([label, key]) => (
              <div key={key} className="fg">
                <label>{label}</label>
                <input required={label.includes('*')} value={form[key]} onChange={upd(key)} />
              </div>
            ))}
            <div className="fg">
              <label>Posición</label>
              <select value={form.position} onChange={upd('position')}>
                {POSITIONS.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div className="fg">
              <label>Prioridad</label>
              <input type="number" value={form.priority} onChange={upd('priority')} />
            </div>
            <div className="fg">
              <label>Inicio</label>
              <input type="datetime-local" value={form.starts_at} onChange={upd('starts_at')} />
            </div>
            <div className="fg">
              <label>Fin</label>
              <input type="datetime-local" value={form.ends_at} onChange={upd('ends_at')} />
            </div>
          </div>
          <button type="submit" disabled={creating} className="btn btn-blue" style={{ marginTop: 16 }}>
            {creating ? 'Guardando…' : 'Crear banner'}
          </button>
        </form>
      )}

      {banners.length === 0 ? (
        <div className="adm-empty">
          <span className="ico"><IconImage size={26} /></span>
          <b>Sin banners</b>
          No hay banners creados todavía.
        </div>
      ) : (
        <div className="adm-table">
          {banners.map((b) => (
            <div key={b.id} className="adm-row">
              <div className="grow">
                <div className="name">{b.title}</div>
                <div className="sub">
                  Prioridad {b.priority}
                  {b.starts_at && ` · desde ${new Date(b.starts_at).toLocaleDateString('es-CO')}`}
                </div>
              </div>
              <span className="tag">{b.position}</span>
              <span className={`tag ${b.is_active ? 'green' : ''}`}>{b.is_active ? 'Activo' : 'Inactivo'}</span>
              <button onClick={() => remove(b.id)} className="btn btn-outline btn-sm btn-danger">Eliminar</button>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
