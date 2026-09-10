import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import {
  approveProperty,
  createProperty,
  deleteImage,
  getProperty,
  pauseProperty,
  reactivateProperty,
  rejectProperty,
  setMainImage,
  setShowOnHome,
  submitProperty,
  updateProperty,
  uploadImage,
} from '../../api/properties'
import LocationPicker from '../../components/property/LocationPicker'
import { useAuth } from '../../contexts/AuthContext'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import Spinner from '../../components/ui/Spinner'
import { digitsOnly, groupThousands, majorToMinor, minorToMajor } from '../../lib/money'
import { prioritizeMainImage } from '../../lib/imageOrder'

const STATUS_LABEL = {
  draft: 'Borrador', pending: 'En revisión', published: 'Publicada', paused: 'Pausada',
  rejected: 'Rechazada', sold: 'Vendida', rented: 'Rentada', deleted: 'Eliminada',
}
const STATUS_CHIP = {
  draft: { color: '#4A5680', background: '#F4F6FB' },
  pending: { color: '#b45309', background: '#FEF3C7' },
  published: { color: '#15803d', background: '#DCFCE7' },
  paused: { color: '#0251FD', background: '#EEF4FF' },
  rejected: { color: '#D7263D', background: '#FEE2E2' },
}
const EDITABLE = ['draft', 'paused', 'rejected']

const EMPTY = {
  title: '', description: '', operation_type: 'sale', property_kind: 'house',
  price_amount: '', currency: 'COP', admin_fee_amount: '', bedrooms: '', bathrooms: '',
  total_area_m2: '', built_area_m2: '', parking_spots: '',
  stratum: '', floor_number: '', total_floors: '', age_years: '',
  view_type: '', security_type: '',
  address_street: '', contact_phone: '', contact_whatsapp: '',
  location_id: '',
  has_storage: false,
  has_elevator: false,
  has_study: false,
  has_balcony: false,
  show_on_home: false,
}

// Estrato options (1–6, Colombian socioeconomic stratum) for the select.
const STRATUM_OPTS = [['', '—'], ['1', '1'], ['2', '2'], ['3', '3'], ['4', '4'], ['5', '5'], ['6', '6']]
const VIEW_OPTS = [['', '—'], ['internal', 'Interna'], ['external', 'Externa']]
const SECURITY_OPTS = [['', '—'], ['none', 'Sin vigilancia'], ['private', 'Privada (portería)'], ['automated', 'Automatizada']]
const TourEditor = lazy(() => import('../../components/panel/TourEditor'))

// Defined at module scope (NOT inside the page component) so their identity is
// stable across renders — otherwise React remounts the input on every keystroke
// and the field loses focus.
function Field({ label, k, form, upd, type = 'text', as = 'input', options = null, required = false, full = false }) {
  // Counts and areas can never be negative; step="any" keeps decimals (m²) valid.
  const numberProps = type === 'number' ? { min: 0, step: 'any' } : {}
  return (
    <div className={`pf-field${full ? ' col-full' : ''}`}>
      <label>{label}</label>
      {as === 'textarea' ? (
        <textarea className="pf-input" value={form[k]} onChange={upd(k)} required={required} />
      ) : options ? (
        <select className="pf-input" value={form[k]} onChange={upd(k)} required={required}>
          {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      ) : (
        <input className="pf-input" type={type} value={form[k]} onChange={upd(k)} required={required} {...numberProps} />
      )}
    </div>
  )
}

// A titled group of fields, separated by a hairline (replaces the old flat list).
function Section({ title, hint, children }) {
  return (
    <section className="pform-section">
      <div className="pform-sec-head"><b>{title}</b>{hint && <small>{hint}</small>}</div>
      {children}
    </section>
  )
}

// Selectable amenity chip. Pure (props only) so it never remounts unexpectedly.
function Chip({ active, onToggle, title, desc }) {
  return (
    <label className={`pf-chip${active ? ' on' : ''}`}>
      <input type="checkbox" checked={active} onChange={(e) => onToggle(e.target.checked)} />
      <span className="box">{active ? '✓' : ''}</span>
      <span className="txt"><b>{title}</b><small>{desc}</small></span>
    </label>
  )
}

export default function PropertyFormPage() {
  const { id } = useParams()
  const isEdit = !!id
  const { user, loading: authLoading, hasPermission } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState(EMPTY)
  const [status, setStatus] = useState(null)
  const [rejectionReason, setRejectionReason] = useState(null)
  const [loading, setLoading] = useState(isEdit)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [uploadProgress, setUploadProgress] = useState(null)
  const [images, setImages] = useState([])
  const fileRef = useRef()

  // `location_id` (el nodo más profundo elegido) es lo único que se persiste;
  // LocationPicker resuelve la cascada País → Departamento → Ciudad → Localidad → Barrio.
  const setLocation = (id) => setForm((f) => ({ ...f, location_id: id }))

  const loadProperty = () => {
    setLoading(true)
    getProperty(id).then(data => {
      setForm({
        title: data.title || '', description: data.description || '',
        operation_type: data.operation_type || 'sale', property_kind: data.property_kind || 'house',
        price_amount: minorToMajor(data.price_amount), currency: data.currency || 'COP',
        admin_fee_amount: minorToMajor(data.admin_fee_amount),
        bedrooms: data.bedrooms ?? '', bathrooms: data.bathrooms ?? '',
        total_area_m2: data.total_area_m2 ?? '', built_area_m2: data.built_area_m2 ?? '',
        parking_spots: data.parking_spots ?? '', address_street: data.address_street || '',
        stratum: data.stratum ?? '', floor_number: data.floor_number ?? '',
        total_floors: data.total_floors ?? '', age_years: data.age_years ?? '',
        view_type: data.view_type || '', security_type: data.security_type || '',
        contact_phone: data.contact_phone || '', contact_whatsapp: data.contact_whatsapp || '',
        location_id: data.location?.id || '',
        has_storage: data.has_storage ?? false,
        has_elevator: data.has_elevator ?? false,
        has_study: data.has_study ?? false,
        has_balcony: data.has_balcony ?? false,
        show_on_home: data.show_on_home ?? false,
      })
      setStatus(data.status)
      setRejectionReason(data.rejection_reason)
      setImages(prioritizeMainImage(data.images || []))
    }).catch(() => navigate('/agente'))
      .finally(() => setLoading(false))
  }

  const reloadImages = () =>
    getProperty(id).then((d) => setImages(prioritizeMainImage(d.images || []))).catch(() => null)

  useEffect(() => {
    if (!authLoading && !user) { navigate('/login'); return }
    if (isEdit && user) loadProperty()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, authLoading, id])

  const upd = k => e => setForm(f => ({ ...f, [k]: e.target.value }))

  const runLifecycle = async (fn, ...args) => {
    setError(null)
    try {
      await fn(id, ...args)
      loadProperty()
    } catch (err) {
      setError(err.response?.data?.error?.message || 'No se pudo cambiar el estado')
    }
  }

  const doReject = () => {
    const reason = window.prompt('Motivo del rechazo:')
    if (reason && reason.trim()) runLifecycle(rejectProperty, reason.trim())
  }

  const editable = !isEdit || EDITABLE.includes(status)
  // Para casa/lote/finca el área principal es la del lote; para apto es el área total.
  const areaLabel = ['house', 'lot', 'farm'].includes(form.property_kind) ? 'Área de lote m²' : 'Área total m²'

  const handleImageUpload = async (e) => {
    const files = Array.from(e.target.files || [])
    if (!files.length || !id) return
    setUploadProgress(0)
    const hadNone = images.length === 0
    for (let i = 0; i < files.length; i++) {
      // first ever image becomes the cover; the rest are gallery
      const role = hadNone && i === 0 ? 'main' : 'gallery'
      await uploadImage(id, files[i], role).catch(() => null)
      setUploadProgress(Math.round(((i + 1) / files.length) * 100))
    }
    if (fileRef.current) fileRef.current.value = ''
    setUploadProgress(null)
    reloadImages()
  }

  const removeImg = (imageId) => deleteImage(id, imageId).then(reloadImages).catch(() => null)
  const makeMain = (imageId) => setMainImage(id, imageId).then(reloadImages).catch(() => null)

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    const payload = { ...form }
    const minorPrice = majorToMinor(form.price_amount)
    if (minorPrice == null) { setError('Ingresa el precio'); setSaving(false); return }
    payload.price_amount = minorPrice
    // Counts/areas are never negative — clamp defensively in case the field is bypassed.
    if (payload.bedrooms !== '') payload.bedrooms = Math.max(0, parseInt(payload.bedrooms, 10) || 0)
    if (payload.bathrooms !== '') payload.bathrooms = Math.max(0, parseInt(payload.bathrooms, 10) || 0)
    if (payload.total_area_m2 !== '') payload.total_area_m2 = Math.max(0, parseFloat(payload.total_area_m2) || 0)
    if (payload.built_area_m2 !== '') payload.built_area_m2 = Math.max(0, parseFloat(payload.built_area_m2) || 0)
    if (payload.parking_spots !== '') payload.parking_spots = Math.max(0, parseInt(payload.parking_spots, 10) || 0)
    // Descriptive integer fields (estrato, piso, antigüedad…)
    if (payload.stratum !== '') payload.stratum = Math.max(0, parseInt(payload.stratum, 10) || 0)
    if (payload.floor_number !== '') payload.floor_number = Math.max(0, parseInt(payload.floor_number, 10) || 0)
    if (payload.total_floors !== '') payload.total_floors = Math.max(0, parseInt(payload.total_floors, 10) || 0)
    if (payload.age_years !== '') payload.age_years = Math.max(0, parseInt(payload.age_years, 10) || 0)
    // Administración is stored in minor units, like the price.
    if (form.admin_fee_amount !== '') payload.admin_fee_amount = majorToMinor(form.admin_fee_amount)
    // Drop empty optional fields so the API doesn't reject "" for int/None columns
    Object.keys(payload).forEach((k) => { if (payload[k] === '') delete payload[k] })
    try {
      const saved = isEdit ? await updateProperty(id, payload) : await createProperty(payload)
      navigate(`/agente/editar/${saved.id}`)
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Error al guardar')
    } finally {
      setSaving(false)
    }
  }

  if (loading || authLoading) return <Spinner />

  return (
    <>
      <Helmet><title>{`${isEdit ? 'Editar propiedad' : 'Nueva propiedad'} | Proppia`}</title></Helmet>

      <AdminPageHeader title={isEdit ? 'Editar propiedad' : 'Nueva propiedad'} subtitle="Completa los datos de la publicación" />

      {isEdit && status && (
        <div style={s.statusPanel}>
          <div style={s.statusInfo}>
            <span style={s.statusLabel}>Estado</span>
            <span style={{ ...s.statusChip, ...(STATUS_CHIP[status] || STATUS_CHIP.draft) }}>
              {STATUS_LABEL[status] || status}
            </span>
            {status === 'rejected' && rejectionReason && (
              <span style={s.rejReason}>Motivo: {rejectionReason}</span>
            )}
          </div>
          <div style={s.statusActions}>
            {status === 'draft' && <button style={s.lcBtn} onClick={() => runLifecycle(submitProperty)}>Enviar a revisión</button>}
            {status === 'rejected' && <button style={s.lcBtn} onClick={() => runLifecycle(submitProperty)}>Reenviar a revisión</button>}
            {status === 'published' && <button style={s.lcBtn} onClick={() => runLifecycle(pauseProperty)}>Pausar para editar</button>}
            {status === 'paused' && <button style={s.lcBtnPrimary} onClick={() => runLifecycle(reactivateProperty)}>Reactivar (publicar)</button>}
            {status === 'pending' && hasPermission('property:moderate') && (
              <>
                <button style={s.lcBtnPrimary} onClick={() => runLifecycle(approveProperty)}>Aprobar y publicar</button>
                <button style={s.lcBtnDanger} onClick={doReject}>Rechazar</button>
              </>
            )}
            {status === 'pending' && !hasPermission('property:moderate') && (
              <span style={s.muted}>En revisión por un administrador.</span>
            )}
          </div>
        </div>
      )}

      {isEdit && !editable && (
        <p style={s.notice}>
          Esta propiedad está <b>{STATUS_LABEL[status] || status}</b> y no se puede editar directamente.{' '}
          {status === 'published' && 'Pulsa “Pausar para editar”, guarda los cambios y luego “Reactivar”.'}
          {status === 'pending' && (hasPermission('property:moderate')
            ? 'Apruébala o recházala para continuar.'
            : 'Debe aprobarla o rechazarla un administrador.')}
        </p>
      )}

      {error && <p style={s.error}>{error}</p>}

      <div className="pform-layout">
        <form onSubmit={submit} className="pform">
          <fieldset disabled={!editable} className={`pform-fieldset${editable ? '' : ' off'}`}>

            <Section title="Información básica">
              <div className="pform-grid">
                <Field full label="Título *" k="title" form={form} upd={upd} required />
                <Field full label="Descripción" k="description" as="textarea" form={form} upd={upd} />
                <Field label="Operación" k="operation_type" form={form} upd={upd} options={[['sale', 'Venta'], ['rent', 'Renta'], ['temporary', 'Temporal']]} />
                <Field label="Tipo" k="property_kind" form={form} upd={upd} options={[['house', 'Casa'], ['apartment', 'Apartamento'], ['studio', 'Aparta estudio'], ['lot', 'Terreno'], ['office', 'Oficina']]} />
              </div>
            </Section>

            <Section title="Precio">
              <div className="pform-grid">
                <div className="pf-field">
                  <label>Precio ({form.currency}) *</label>
                  <div className="pf-money">
                    <span>{form.currency === 'USD' ? 'US$' : form.currency === 'EUR' ? '€' : '$'}</span>
                    <input
                      className="pf-input"
                      type="text"
                      inputMode="numeric"
                      placeholder="0"
                      required
                      value={groupThousands(form.price_amount)}
                      onChange={(e) => setForm((f) => ({ ...f, price_amount: digitsOnly(e.target.value) }))}
                    />
                  </div>
                </div>
                <Field label="Moneda" k="currency" form={form} upd={upd} options={[['COP', 'COP'], ['USD', 'USD'], ['EUR', 'EUR']]} />
                <div className="pf-field">
                  <label>Administración ({form.currency}) / mes</label>
                  <div className="pf-money">
                    <span>{form.currency === 'USD' ? 'US$' : form.currency === 'EUR' ? '€' : '$'}</span>
                    <input
                      className="pf-input"
                      type="text"
                      inputMode="numeric"
                      placeholder="0"
                      value={groupThousands(form.admin_fee_amount)}
                      onChange={(e) => setForm((f) => ({ ...f, admin_fee_amount: digitsOnly(e.target.value) }))}
                    />
                  </div>
                </div>
              </div>
            </Section>

            <Section title="Características">
              <div className="pform-grid cols-3">
                <Field label="Habitaciones" k="bedrooms" type="number" form={form} upd={upd} />
                <Field label="Baños" k="bathrooms" type="number" form={form} upd={upd} />
                <Field label="Estacionamientos" k="parking_spots" type="number" form={form} upd={upd} />
                <Field label={areaLabel} k="total_area_m2" type="number" form={form} upd={upd} />
                <Field label="Área construida m²" k="built_area_m2" type="number" form={form} upd={upd} />
                <Field label="Estrato" k="stratum" form={form} upd={upd} options={STRATUM_OPTS} />
                <Field label="No. de piso" k="floor_number" type="number" form={form} upd={upd} />
                <Field label="Pisos del edificio" k="total_floors" type="number" form={form} upd={upd} />
                <Field label="Antigüedad (años)" k="age_years" type="number" form={form} upd={upd} />
                <Field label="Vista" k="view_type" form={form} upd={upd} options={VIEW_OPTS} />
                <Field label="Vigilancia" k="security_type" form={form} upd={upd} options={SECURITY_OPTS} />
              </div>
            </Section>

            <Section title="Comodidades" hint="Marca lo que aplique al inmueble.">
              <div className="pf-chips">
                <Chip active={form.has_storage} onToggle={(v) => setForm((f) => ({ ...f, has_storage: v }))}
                  title="Depósito / Bodega" desc="Cuenta con depósito o bodega" />
                <Chip active={form.has_elevator} onToggle={(v) => setForm((f) => ({ ...f, has_elevator: v }))}
                  title="Ascensor" desc="El edificio tiene ascensor" />
                <Chip active={form.has_study} onToggle={(v) => setForm((f) => ({ ...f, has_study: v }))}
                  title="Zona de estudio" desc="El apartamento tiene zona de estudio" />
                <Chip active={form.has_balcony} onToggle={(v) => setForm((f) => ({ ...f, has_balcony: v }))}
                  title="Balcón / Terraza" desc="Cuenta con balcón o terraza" />
              </div>
            </Section>

            <Section title="Ubicación">
              <div className="pform-grid cols-3">
                <LocationPicker value={form.location_id} onChange={setLocation} />
              </div>
              <div className="pform-grid" style={{ marginTop: 16 }}>
                <Field full label="Dirección" k="address_street" form={form} upd={upd} />
              </div>
            </Section>

            <Section title="Contacto">
              <div className="pform-grid">
                <Field label="Teléfono de contacto" k="contact_phone" form={form} upd={upd} />
                <Field label="WhatsApp de contacto" k="contact_whatsapp" form={form} upd={upd} />
              </div>
            </Section>
          </fieldset>

          <label className="pf-toggle">
            <span className="txt">
              <b>Mostrar en portada</b>
              <small>Aparece en “Propiedades destacadas” del inicio (solo si está publicada). Se guarda al instante.</small>
            </span>
            <span className="pf-switch">
              <input
                type="checkbox"
                checked={form.show_on_home}
                onChange={(e) => {
                  const checked = e.target.checked
                  setForm((f) => ({ ...f, show_on_home: checked }))
                  // Persist immediately for existing properties (works in any status);
                  // for new ones it travels in the create payload.
                  if (isEdit) {
                    setError(null)
                    setShowOnHome(id, checked).catch(() => {
                      setForm((f) => ({ ...f, show_on_home: !checked }))
                      setError('No se pudo cambiar la visibilidad en portada')
                    })
                  }
                }}
              />
              <span className="track" />
            </span>
          </label>

          <button type="submit" disabled={saving || !editable} className="pf-submit">
            {saving ? 'Guardando…' : !editable ? 'No editable en este estado' : isEdit ? 'Guardar cambios' : 'Crear propiedad'}
          </button>
        </form>

        {isEdit && (
          <aside className="pform-aside">
            <h3>Fotos ({images.length})</h3>
            <input type="file" ref={fileRef} multiple accept="image/*" onChange={handleImageUpload} style={{ display: 'none' }} />
            <button type="button" onClick={() => fileRef.current?.click()} className="pform-upload">
              + Subir fotos
            </button>
            {uploadProgress !== null && (
              <div className="pf-progress">
                <div className="bar" style={{ width: `${uploadProgress}%` }} />
                <span className="pct">{uploadProgress}%</span>
              </div>
            )}
            {images.length > 0 && (
              <div className="img-manager">
                {images.map((img) => (
                  <div key={img.id} className={`img-tile ${img.role === 'main' ? 'main' : ''}`}>
                    <img src={img.thumb_url || img.cdn_url} alt={img.alt_text || ''} />
                    <button type="button" className="x" onClick={() => removeImg(img.id)} aria-label="Quitar">✕</button>
                    {img.role === 'main'
                      ? <span className="mainbadge">PORTADA</span>
                      : <button type="button" className="setmain" onClick={() => makeMain(img.id)}>Hacer portada</button>}
                  </div>
                ))}
              </div>
            )}
            <p className="hint">
              Sube varias fotos a la vez. La marcada como <b>portada</b> se usa en la tarjeta y como primera del carrusel.
            </p>
          </aside>
        )}
      </div>
      {isEdit && (
        <Suspense fallback={<div className="admin-card">Cargando Tour 360…</div>}>
          <TourEditor entity="properties" entityId={id} galleryImages={images} />
        </Suspense>
      )}
    </>
  )
}

// Inline styles kept only for the status bar / lifecycle controls (the form body
// itself is now styled via the .pform* classes in admin.css).
const s = {
  error: { background: '#fef2f2', color: '#D7263D', borderRadius: 10, padding: '10px 14px', fontSize: 14, marginBottom: 16 },
  statusPanel: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap', background: '#fff', border: '1px solid #DDE8FF', borderRadius: 14, padding: '14px 18px', marginBottom: 16, boxShadow: '0 8px 24px rgba(8,29,103,0.06)' },
  statusInfo: { display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' },
  statusLabel: { fontSize: 11, fontWeight: 700, color: '#8A94A3', textTransform: 'uppercase', letterSpacing: '0.05em' },
  statusChip: { borderRadius: 999, padding: '4px 12px', fontSize: 13, fontWeight: 700 },
  rejReason: { fontSize: 13, color: '#D7263D' },
  statusActions: { display: 'flex', gap: 8, flexWrap: 'wrap' },
  lcBtn: { background: '#F4F6FB', color: '#0251FD', border: '1px solid #DDE8FF', borderRadius: 10, padding: '8px 16px', fontSize: 13, fontWeight: 700, cursor: 'pointer' },
  lcBtnPrimary: { background: '#0251FD', color: '#fff', border: 'none', borderRadius: 10, padding: '8px 16px', fontSize: 13, fontWeight: 700, cursor: 'pointer' },
  lcBtnDanger: { background: '#fef2f2', color: '#b91c1c', border: '1px solid #fecaca', borderRadius: 10, padding: '8px 16px', fontSize: 13, fontWeight: 700, cursor: 'pointer' },
  muted: { fontSize: 13, color: '#6B7686' },
  notice: { background: '#FEF3C7', color: '#92400e', borderRadius: 10, padding: '10px 14px', fontSize: 13.5, marginBottom: 16 },
}
