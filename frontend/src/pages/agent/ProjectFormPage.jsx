import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../../contexts/AuthContext'
import {
  addProjectImage,
  createProject,
  deleteProjectImage,
  getProject,
  getProjectImages,
  updateProject,
  uploadProjectImage,
} from '../../api/projects'
import { getAgencies } from '../../api/agencies'
import { getLocations, getPropertyTypes } from '../../api/catalog'
import Spinner from '../../components/ui/Spinner'
import { digitsOnly, groupThousands, majorToMinor, minorToMajor } from '../../lib/money'

const EMPTY = {
  title: '', developer_name: '', stage: 'preventa', currency: 'COP',
  agency_id: '', location_id: '', property_type_id: '',
  price_from: '', price_to: '',
  bedrooms_min: '', bedrooms_max: '', bathrooms_min: '', bathrooms_max: '',
  area_min_m2: '', area_max_m2: '', total_units: '', available_units: '',
  address_street: '', contact_phone: '', contact_whatsapp: '', cover_image_url: '', description: '',
}

const num = (v) => (v === '' || v == null ? null : parseInt(v, 10))
const flt = (v) => (v === '' || v == null ? null : parseFloat(v))

export default function ProjectFormPage() {
  const { slug } = useParams()
  const editing = Boolean(slug)
  const { user, loading: authLoading } = useAuth()
  const navigate = useNavigate()
  const fileRef = useRef(null)

  const [form, setForm] = useState(EMPTY)
  const [projectId, setProjectId] = useState(null)
  const [images, setImages] = useState([])
  const [agencies, setAgencies] = useState([])
  const [locations, setLocations] = useState([])
  const [types, setTypes] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [imgUrl, setImgUrl] = useState('')

  useEffect(() => {
    if (!authLoading) {
      if (!user) { navigate('/login'); return }
      if (!user.permissions?.includes('project:create')) { navigate('/agente'); return }
    }
    if (!user) return

    Promise.all([
      getAgencies().catch(() => []),
      getLocations().catch(() => []),
      getPropertyTypes().catch(() => []),
    ]).then(([ag, loc, ty]) => {
      setAgencies(ag || [])
      setLocations(Array.isArray(loc) ? loc : loc.data || [])
      setTypes(ty || [])
    })

    if (editing) {
      getProject(slug)
        .then((p) => {
          setProjectId(p.id)
          setForm({
            ...EMPTY,
            ...Object.fromEntries(Object.keys(EMPTY).map((k) => [k, p[k] ?? ''])),
            price_from: minorToMajor(p.price_from),
            price_to: minorToMajor(p.price_to),
          })
          setImages(p.images || [])
        })
        .catch(() => setError('No se pudo cargar el proyecto'))
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, authLoading, slug])

  const upd = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const buildPayload = () => ({
    title: form.title,
    developer_name: form.developer_name || null,
    stage: form.stage,
    currency: form.currency || 'COP',
    agency_id: form.agency_id || null,
    location_id: form.location_id || null,
    property_type_id: form.property_type_id || null,
    price_from: majorToMinor(form.price_from),
    price_to: majorToMinor(form.price_to),
    bedrooms_min: num(form.bedrooms_min),
    bedrooms_max: num(form.bedrooms_max),
    bathrooms_min: num(form.bathrooms_min),
    bathrooms_max: num(form.bathrooms_max),
    area_min_m2: flt(form.area_min_m2),
    area_max_m2: flt(form.area_max_m2),
    total_units: num(form.total_units),
    available_units: num(form.available_units),
    address_street: form.address_street || null,
    contact_phone: form.contact_phone || null,
    contact_whatsapp: form.contact_whatsapp || null,
    cover_image_url: form.cover_image_url || null,
    description: form.description || null,
  })

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      if (editing) {
        await updateProject(projectId, buildPayload())
      } else {
        const created = await createProject(buildPayload())
        navigate(`/agente/proyectos/editar/${created.slug}`)
        return
      }
      navigate('/agente/proyectos')
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Error al guardar el proyecto')
    } finally {
      setSaving(false)
    }
  }

  const reloadImages = () => getProjectImages(projectId).then(setImages).catch(() => null)

  const onUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file || !projectId) return
    const role = images.length === 0 ? 'main' : 'gallery'
    await uploadProjectImage(projectId, file, role).catch(() => null)
    if (fileRef.current) fileRef.current.value = ''
    reloadImages()
  }

  const addByUrl = async () => {
    if (!imgUrl.trim() || !projectId) return
    const role = images.length === 0 ? 'main' : 'gallery'
    await addProjectImage(projectId, { cdn_url: imgUrl.trim(), role }).catch(() => null)
    setImgUrl('')
    reloadImages()
  }

  const removeImage = async (id) => {
    await deleteProjectImage(projectId, id).catch(() => null)
    reloadImages()
  }

  if (authLoading || loading) return <div className="page-wrap"><Spinner /></div>

  return (
    <div className="page-wrap">
      <Helmet><title>{editing ? 'Editar' : 'Nuevo'} proyecto | Panel</title></Helmet>
      <div className="admin-head">
        <button className="admin-back" onClick={() => navigate('/agente/proyectos')}>← Proyectos</button>
        <h1>{editing ? 'Editar proyecto' : 'Nuevo proyecto'}</h1>
      </div>

      <form className="admin-card" onSubmit={submit}>
        {error && <p style={{ color: '#b91c1c', marginBottom: 10 }}>{error}</p>}
        <div className="form-grid">
          <div className="fg full"><label>Título *</label><input required value={form.title} onChange={upd('title')} /></div>
          <div className="fg"><label>Desarrollador</label><input value={form.developer_name} onChange={upd('developer_name')} /></div>
          <div className="fg"><label>Etapa</label>
            <select value={form.stage} onChange={upd('stage')}>
              <option value="preventa">Preventa</option>
              <option value="construccion">En construcción</option>
              <option value="entrega_inmediata">Entrega inmediata</option>
            </select>
          </div>
          <div className="fg"><label>Inmobiliaria</label>
            <select value={form.agency_id} onChange={upd('agency_id')}>
              <option value="">—</option>
              {agencies.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
          </div>
          <div className="fg"><label>Ubicación</label>
            <select value={form.location_id} onChange={upd('location_id')}>
              <option value="">—</option>
              {locations.map((l) => <option key={l.id} value={l.id}>{l.name} ({l.level})</option>)}
            </select>
          </div>
          <div className="fg"><label>Tipo</label>
            <select value={form.property_type_id} onChange={upd('property_type_id')}>
              <option value="">—</option>
              {types.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </div>
          <div className="fg"><label>Moneda</label>
            <select value={form.currency} onChange={upd('currency')}>
              <option value="COP">COP</option>
              <option value="USD">USD</option>
            </select>
          </div>
          <div className="fg"><label>Precio desde ({form.currency})</label><input inputMode="numeric" placeholder="0" value={groupThousands(form.price_from)} onChange={(e) => setForm((f) => ({ ...f, price_from: digitsOnly(e.target.value) }))} /></div>
          <div className="fg"><label>Precio hasta ({form.currency})</label><input inputMode="numeric" placeholder="0" value={groupThousands(form.price_to)} onChange={(e) => setForm((f) => ({ ...f, price_to: digitsOnly(e.target.value) }))} /></div>
          <div className="fg"><label>Habitaciones mín.</label><input type="number" value={form.bedrooms_min} onChange={upd('bedrooms_min')} /></div>
          <div className="fg"><label>Habitaciones máx.</label><input type="number" value={form.bedrooms_max} onChange={upd('bedrooms_max')} /></div>
          <div className="fg"><label>Baños mín.</label><input type="number" value={form.bathrooms_min} onChange={upd('bathrooms_min')} /></div>
          <div className="fg"><label>Baños máx.</label><input type="number" value={form.bathrooms_max} onChange={upd('bathrooms_max')} /></div>
          <div className="fg"><label>Área mín. (m²)</label><input type="number" value={form.area_min_m2} onChange={upd('area_min_m2')} /></div>
          <div className="fg"><label>Área máx. (m²)</label><input type="number" value={form.area_max_m2} onChange={upd('area_max_m2')} /></div>
          <div className="fg"><label>Unidades totales</label><input type="number" value={form.total_units} onChange={upd('total_units')} /></div>
          <div className="fg"><label>Unidades disponibles</label><input type="number" value={form.available_units} onChange={upd('available_units')} /></div>
          <div className="fg full"><label>Dirección</label><input value={form.address_street} onChange={upd('address_street')} /></div>
          <div className="fg"><label>Teléfono contacto</label><input value={form.contact_phone} onChange={upd('contact_phone')} /></div>
          <div className="fg"><label>WhatsApp contacto</label><input value={form.contact_whatsapp} onChange={upd('contact_whatsapp')} /></div>
          <div className="fg full"><label>Imagen de portada (URL)</label><input value={form.cover_image_url} onChange={upd('cover_image_url')} /></div>
          <div className="fg full"><label>Descripción</label><textarea rows={4} value={form.description} onChange={upd('description')} /></div>
        </div>
        <button className="btn btn-blue" disabled={saving} style={{ marginTop: 14 }}>
          {saving ? 'Guardando…' : editing ? 'Guardar cambios' : 'Crear y continuar'}
        </button>
      </form>

      {editing && (
        <div className="admin-card">
          <h3 style={{ fontWeight: 800, color: 'var(--ink)', marginBottom: 12 }}>Galería del proyecto</h3>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
            <input ref={fileRef} type="file" accept="image/*" onChange={onUpload} />
            <span style={{ color: 'var(--muted)', fontSize: 13 }}>o</span>
            <input
              placeholder="Pega una URL de imagen"
              value={imgUrl}
              onChange={(e) => setImgUrl(e.target.value)}
              style={{ flex: 1, minWidth: 180, padding: '9px 12px', border: '1.5px solid var(--line)', borderRadius: 10 }}
            />
            <button type="button" className="btn btn-outline btn-sm" onClick={addByUrl}>Agregar URL</button>
          </div>
          {images.length === 0 ? (
            <p style={{ color: 'var(--muted)', marginTop: 12 }}>Sin imágenes todavía.</p>
          ) : (
            <div className="thumb-row">
              {images.map((img) => (
                <div className="thumb" key={img.id}>
                  <img src={img.cdn_url} alt={img.alt_text || ''} />
                  <button type="button" className="x" onClick={() => removeImage(img.id)} aria-label="Quitar">✕</button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
