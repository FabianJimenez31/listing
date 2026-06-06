import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../../contexts/AuthContext'
import { getBanners, createBanner, deleteBanner } from '../../api/admin'
import Spinner from '../../components/ui/Spinner'

const POSITIONS = ['HOME_HERO', 'HOME_INLINE', 'SEARCH_TOP', 'SEARCH_SIDEBAR', 'DETAIL_BOTTOM']

const EMPTY_BANNER = {
  title: '', position: 'HOME_HERO', image_desktop_url: '',
  image_mobile_url: '', cta_url: '', cta_text: '', priority: 0, is_active: true,
  starts_at: '', ends_at: '',
}

export default function BannersPage() {
  const { user, loading: authLoading, isAdmin } = useAuth()
  const navigate = useNavigate()
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

  useEffect(() => {
    if (!authLoading) {
      if (!user) { navigate('/login'); return }
      if (!isAdmin()) { navigate('/agente'); return }
    }
    if (user) load()
  }, [user, authLoading])

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

  if (authLoading || loading) return <Spinner />

  return (
    <>
      <Helmet><title>Banners | Listing Admin</title></Helmet>

      <div style={styles.header}>
        <button onClick={() => navigate('/admin')} style={styles.back}>← Admin</button>
        <h1 style={styles.h1}>Banners ({banners.length})</h1>
        <button onClick={() => setShowForm(!showForm)} style={styles.newBtn}>
          {showForm ? 'Cancelar' : '+ Nuevo banner'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={submit} style={styles.formCard}>
          <h3 style={styles.formH}>Nuevo banner</h3>
          {error && <p style={styles.error}>{error}</p>}
          <div style={styles.grid2}>
            {[['Título *', 'title'], ['URL imagen desktop *', 'image_desktop_url'], ['URL imagen mobile', 'image_mobile_url'], ['URL destino (CTA)', 'cta_url'], ['Texto CTA', 'cta_text']].map(([label, key]) => (
              <div key={key} style={styles.field}>
                <label style={styles.label}>{label}</label>
                <input required={label.includes('*')} value={form[key]} onChange={upd(key)} style={styles.input} />
              </div>
            ))}
            <div style={styles.field}>
              <label style={styles.label}>Posición</label>
              <select value={form.position} onChange={upd('position')} style={styles.input}>
                {POSITIONS.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div style={styles.field}>
              <label style={styles.label}>Prioridad</label>
              <input type="number" value={form.priority} onChange={upd('priority')} style={styles.input} />
            </div>
            <div style={styles.field}>
              <label style={styles.label}>Inicio</label>
              <input type="datetime-local" value={form.starts_at} onChange={upd('starts_at')} style={styles.input} />
            </div>
            <div style={styles.field}>
              <label style={styles.label}>Fin</label>
              <input type="datetime-local" value={form.ends_at} onChange={upd('ends_at')} style={styles.input} />
            </div>
          </div>
          <button type="submit" disabled={creating} style={styles.saveBtn}>
            {creating ? 'Guardando…' : 'Crear banner'}
          </button>
        </form>
      )}

      {banners.length === 0 ? (
        <p style={styles.empty}>No hay banners creados.</p>
      ) : (
        <div style={styles.table}>
          {banners.map((b) => (
            <div key={b.id} style={styles.row}>
              <div style={styles.rowMain}>
                <strong>{b.title}</strong>
                <span style={styles.posTag}>{b.position}</span>
                <span style={{ fontSize: 12, color: b.is_active ? '#2d6a4f' : '#888' }}>
                  {b.is_active ? 'Activo' : 'Inactivo'}
                </span>
              </div>
              <div style={styles.rowMeta}>
                <span style={{ fontSize: 12, color: '#888' }}>Prioridad: {b.priority}</span>
                {b.starts_at && <span style={{ fontSize: 12, color: '#aaa' }}>desde {new Date(b.starts_at).toLocaleDateString('es-CO')}</span>}
              </div>
              <button onClick={() => remove(b.id)} style={styles.deleteBtn}>Eliminar</button>
            </div>
          ))}
        </div>
      )}
    </>
  )
}

const styles = {
  header: { display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' },
  back: { background: 'none', border: 'none', color: '#e94560', cursor: 'pointer', fontSize: 14 },
  h1: { fontSize: 22, color: '#1a1a2e', margin: 0, flex: 1 },
  newBtn: { background: '#e94560', color: '#fff', border: 'none', borderRadius: 6, padding: '8px 16px', cursor: 'pointer', fontWeight: 600 },
  formCard: { background: '#fff', borderRadius: 10, padding: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,.07)', marginBottom: '1.5rem' },
  formH: { fontSize: 16, color: '#1a1a2e', margin: '0 0 1rem' },
  grid2: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' },
  field: {},
  label: { display: 'block', fontSize: 12, color: '#555', marginBottom: 3 },
  input: { display: 'block', width: '100%', padding: '7px 10px', border: '1px solid #ddd', borderRadius: 5, fontSize: 13, boxSizing: 'border-box' },
  saveBtn: { marginTop: '1rem', background: '#1a1a2e', color: '#fff', border: 'none', borderRadius: 6, padding: '9px 24px', cursor: 'pointer', fontWeight: 600 },
  error: { color: '#e94560', fontSize: 13, marginBottom: 8 },
  table: { background: '#fff', borderRadius: 10, overflow: 'hidden', boxShadow: '0 2px 8px rgba(0,0,0,.07)' },
  row: { display: 'flex', alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid #f0f0f0', gap: '1rem' },
  rowMain: { flex: 1, display: 'flex', gap: '1rem', alignItems: 'center' },
  rowMeta: { display: 'flex', gap: '1rem' },
  posTag: { background: '#f0f0f0', borderRadius: 4, padding: '2px 8px', fontSize: 12 },
  deleteBtn: { background: '#fef2f2', color: '#b91c1c', border: '1px solid #fecaca', borderRadius: 4, padding: '4px 10px', cursor: 'pointer', fontSize: 12 },
  empty: { color: '#888', background: '#fff', borderRadius: 10, padding: '2rem', textAlign: 'center' },
}
