import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../../contexts/AuthContext'
import {
  createProject,
  deleteProjectImage,
  getProject,
  getProjectImages,
  setMainProjectImage,
  updateProject,
  uploadProjectImage,
} from '../../api/projects'
import { getAgencies } from '../../api/agencies'
import { getPropertyTypes } from '../../api/catalog'
import LocationPicker from '../../components/property/LocationPicker'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import Spinner from '../../components/ui/Spinner'
import { digitsOnly, groupThousands, majorToMinor, minorToMajor } from '../../lib/money'

const EMPTY = {
  title: '', developer_name: '', stage: 'preventa', currency: 'COP',
  agency_id: '', location_id: '', property_type_id: '',
  price_from: '', price_to: '',
  bedrooms_min: '', bedrooms_max: '', bathrooms_min: '', bathrooms_max: '',
  area_min_m2: '', area_max_m2: '', total_units: '', available_units: '',
  address_street: '', contact_phone: '', contact_whatsapp: '', description: '',
}

const num = (v) => (v === '' || v == null ? null : parseInt(v, 10))
const flt = (v) => (v === '' || v == null ? null : parseFloat(v))
const TourEditor = lazy(() => import('../../components/panel/TourEditor'))

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
  const [types, setTypes] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [uploadProgress, setUploadProgress] = useState(null)

  useEffect(() => {
    if (!authLoading) {
      if (!user) { navigate('/login'); return }
      if (!user.permissions?.includes('project:create')) { navigate('/agente'); return }
    }
    if (!user) return

    Promise.all([
      getAgencies().catch(() => []),
      getPropertyTypes().catch(() => []),
    ]).then(([ag, ty]) => {
      setAgencies(ag || [])
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

  // Bulk upload: the first image of an empty gallery becomes the cover (role=main),
  // the rest go to the gallery. Mirrors the property form.
  const handleUpload = async (e) => {
    const files = Array.from(e.target.files || [])
    if (!files.length || !projectId) return
    setUploadProgress(0)
    const hadNone = images.length === 0
    for (let i = 0; i < files.length; i++) {
      const role = hadNone && i === 0 ? 'main' : 'gallery'
      await uploadProjectImage(projectId, files[i], role).catch(() => null)
      setUploadProgress(Math.round(((i + 1) / files.length) * 100))
    }
    if (fileRef.current) fileRef.current.value = ''
    setUploadProgress(null)
    reloadImages()
  }

  const makeMain = (id) => setMainProjectImage(projectId, id).then(reloadImages).catch(() => null)

  const removeImage = async (id) => {
    await deleteProjectImage(projectId, id).catch(() => null)
    reloadImages()
  }

  if (authLoading || loading) return <Spinner />

  return (
    <>
      <Helmet><title>{`${editing ? 'Editar' : 'Nuevo'} proyecto | Proppia`}</title></Helmet>
      <AdminPageHeader title={editing ? 'Editar proyecto' : 'Nuevo proyecto'} subtitle="Datos del desarrollo inmobiliario" />

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
          <LocationPicker
            value={form.location_id}
            onChange={(id) => setForm((f) => ({ ...f, location_id: id }))}
            fieldClass="fg"
            inputClass=""
          />
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
          <div className="fg full"><label>Descripción</label><textarea rows={4} value={form.description} onChange={upd('description')} /></div>
        </div>
        <button className="btn btn-blue" disabled={saving} style={{ marginTop: 14 }}>
          {saving ? 'Guardando…' : editing ? 'Guardar cambios' : 'Crear y continuar'}
        </button>
      </form>

      {editing && (
        <div className="admin-card">
          <h3 style={{ fontWeight: 800, color: 'var(--ink)', marginBottom: 12 }}>Galería del proyecto ({images.length})</h3>
          <input ref={fileRef} type="file" multiple accept="image/*" onChange={handleUpload} style={{ display: 'none' }} />
          <button type="button" className="btn btn-blue btn-sm" onClick={() => fileRef.current?.click()}>+ Subir fotos</button>
          {uploadProgress !== null && (
            <div className="pf-progress" style={{ maxWidth: 280 }}>
              <div className="bar" style={{ width: `${uploadProgress}%` }} />
              <span className="pct">{uploadProgress}%</span>
            </div>
          )}
          {images.length === 0 ? (
            <p style={{ color: 'var(--muted)', marginTop: 12 }}>Sin imágenes todavía. Sube varias a la vez y elige cuál es la portada.</p>
          ) : (
            <div className="img-manager">
              {images.map((img) => (
                <div className={`img-tile ${img.role === 'main' ? 'main' : ''}`} key={img.id}>
                  <img src={img.thumb_url || img.cdn_url} alt={img.alt_text || ''} />
                  <button type="button" className="x" onClick={() => removeImage(img.id)} aria-label="Quitar">✕</button>
                  {img.role === 'main'
                    ? <span className="mainbadge">PORTADA</span>
                    : <button type="button" className="setmain" onClick={() => makeMain(img.id)}>Hacer portada</button>}
                </div>
              ))}
            </div>
          )}
          <p style={{ color: 'var(--muted)', fontSize: 13, marginTop: 10 }}>
            Sube varias fotos a la vez. La marcada como <b>portada</b> se usa en la tarjeta del listado y como primera del carrusel.
          </p>
        </div>
      )}
      {editing && projectId && (
        <Suspense fallback={<div className="admin-card">Cargando Tour 360…</div>}>
          <TourEditor entity="projects" entityId={projectId} galleryImages={images} />
        </Suspense>
      )}
    </>
  )
}
