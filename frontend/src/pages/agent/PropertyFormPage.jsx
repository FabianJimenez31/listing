import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import {
  approveProperty,
  createProperty,
  getProperty,
  pauseProperty,
  reactivateProperty,
  rejectProperty,
  setShowOnHome,
  submitProperty,
  updateProperty,
  uploadImage,
} from '../../api/properties'
import { useAuth } from '../../contexts/AuthContext'
import Spinner from '../../components/ui/Spinner'
import { digitsOnly, groupThousands, majorToMinor, minorToMajor } from '../../lib/money'

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
  price_amount: '', currency: 'COP', bedrooms: '', bathrooms: '',
  total_area_m2: '', built_area_m2: '', parking_spots: '',
  address_street: '', contact_phone: '', contact_whatsapp: '',
  show_on_home: false,
}

// Defined at module scope (NOT inside the page component) so its identity is
// stable across renders — otherwise React remounts the input on every keystroke
// and the field loses focus.
function Field({ label, k, form, upd, type = 'text', as = 'input', options = null }) {
  return (
    <div style={s.field}>
      <label style={s.label}>{label}</label>
      {as === 'textarea' ? (
        <textarea value={form[k]} onChange={upd(k)} style={{ ...s.input, height: 90, resize: 'vertical' }} />
      ) : options ? (
        <select value={form[k]} onChange={upd(k)} style={s.input}>
          {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      ) : (
        <input type={type} value={form[k]} onChange={upd(k)} style={s.input} />
      )}
    </div>
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
  const fileRef = useRef()

  const loadProperty = () => {
    setLoading(true)
    getProperty(id).then(data => {
      setForm({
        title: data.title || '', description: data.description || '',
        operation_type: data.operation_type || 'sale', property_kind: data.property_kind || 'house',
        price_amount: minorToMajor(data.price_amount), currency: data.currency || 'COP',
        bedrooms: data.bedrooms ?? '', bathrooms: data.bathrooms ?? '',
        total_area_m2: data.total_area_m2 ?? '', built_area_m2: data.built_area_m2 ?? '',
        parking_spots: data.parking_spots ?? '', address_street: data.address_street || '',
        contact_phone: data.contact_phone || '', contact_whatsapp: data.contact_whatsapp || '',
        show_on_home: data.show_on_home ?? false,
      })
      setStatus(data.status)
      setRejectionReason(data.rejection_reason)
    }).catch(() => navigate('/agente'))
      .finally(() => setLoading(false))
  }

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

  const handleImageUpload = async (e) => {
    const files = Array.from(e.target.files || [])
    if (!files.length || !id) return
    setUploadProgress(0)
    for (let i = 0; i < files.length; i++) {
      await uploadImage(id, files[i], i === 0 ? 'main' : 'gallery').catch(() => null)
      setUploadProgress(Math.round(((i + 1) / files.length) * 100))
    }
    setUploadProgress(null)
    alert('Imágenes subidas correctamente')
  }

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    const payload = { ...form }
    const minorPrice = majorToMinor(form.price_amount)
    if (minorPrice == null) { setError('Ingresa el precio'); setSaving(false); return }
    payload.price_amount = minorPrice
    if (payload.bedrooms !== '') payload.bedrooms = parseInt(payload.bedrooms, 10)
    if (payload.bathrooms !== '') payload.bathrooms = parseInt(payload.bathrooms, 10)
    if (payload.total_area_m2 !== '') payload.total_area_m2 = parseFloat(payload.total_area_m2)
    if (payload.built_area_m2 !== '') payload.built_area_m2 = parseFloat(payload.built_area_m2)
    if (payload.parking_spots !== '') payload.parking_spots = parseInt(payload.parking_spots, 10)
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

  if (loading || authLoading) return <div className="page-wrap"><Spinner /></div>

  return (
    <div className="page-wrap">
      <Helmet><title>{isEdit ? 'Editar propiedad' : 'Nueva propiedad'} | Proppietario</title></Helmet>

      <div style={s.header}>
        <button onClick={() => navigate('/agente')} style={s.back}>← Volver</button>
        <h1 style={s.h1}>{isEdit ? 'Editar propiedad' : 'Nueva propiedad'}</h1>
      </div>

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

      <div style={s.layout}>
        <form onSubmit={submit} style={s.form}>
          <Field label="Título *" k="title" form={form} upd={upd} />
          <Field label="Descripción" k="description" as="textarea" form={form} upd={upd} />
          <div style={s.row2}>
            <Field label="Operación" k="operation_type" form={form} upd={upd} options={[['sale', 'Venta'], ['rent', 'Renta'], ['temporary', 'Temporal']]} />
            <Field label="Tipo" k="property_kind" form={form} upd={upd} options={[['house', 'Casa'], ['apartment', 'Apartamento'], ['lot', 'Terreno'], ['office', 'Oficina']]} />
          </div>
          <div style={s.row2}>
            <div style={s.field}>
              <label style={s.label}>Precio ({form.currency}) *</label>
              <div style={{ position: 'relative' }}>
                <span style={s.moneyPrefix}>{form.currency === 'USD' ? 'US$' : form.currency === 'EUR' ? '€' : '$'}</span>
                <input
                  type="text"
                  inputMode="numeric"
                  placeholder="0"
                  value={groupThousands(form.price_amount)}
                  onChange={(e) => setForm((f) => ({ ...f, price_amount: digitsOnly(e.target.value) }))}
                  style={{ ...s.input, paddingLeft: 36 }}
                />
              </div>
            </div>
            <Field label="Moneda" k="currency" form={form} upd={upd} options={[['COP', 'COP'], ['USD', 'USD'], ['EUR', 'EUR']]} />
          </div>
          <div style={s.row3}>
            <Field label="Recámaras" k="bedrooms" type="number" form={form} upd={upd} />
            <Field label="Baños" k="bathrooms" type="number" form={form} upd={upd} />
            <Field label="Estacionamientos" k="parking_spots" type="number" form={form} upd={upd} />
          </div>
          <div style={s.row2}>
            <Field label="Área total m²" k="total_area_m2" type="number" form={form} upd={upd} />
            <Field label="Área construida m²" k="built_area_m2" type="number" form={form} upd={upd} />
          </div>
          <Field label="Dirección" k="address_street" form={form} upd={upd} />
          <Field label="Teléfono de contacto" k="contact_phone" form={form} upd={upd} />
          <Field label="WhatsApp de contacto" k="contact_whatsapp" form={form} upd={upd} />

          <label style={s.homeToggle}>
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
            <span>
              <b>Mostrar en portada</b>
              <small style={s.homeHint}>Aparece en “Propiedades destacadas” del inicio (solo si está publicada). Se guarda al instante.</small>
            </span>
          </label>

          <button type="submit" disabled={saving || !editable} style={{ ...s.btn, ...(editable ? {} : s.btnDisabled) }}>
            {saving ? 'Guardando…' : !editable ? 'No editable en este estado' : isEdit ? 'Guardar cambios' : 'Crear propiedad'}
          </button>
        </form>

        {isEdit && (
          <aside style={s.aside}>
            <h3 style={s.asideH}>Imágenes</h3>
            <input type="file" ref={fileRef} multiple accept="image/*" onChange={handleImageUpload} style={{ display: 'none' }} />
            <button onClick={() => fileRef.current?.click()} style={s.uploadBtn}>
              Subir imágenes
            </button>
            {uploadProgress !== null && (
              <div style={s.progress}>
                <div style={{ ...s.progressBar, width: `${uploadProgress}%` }} />
                <span style={s.progressLabel}>{uploadProgress}%</span>
              </div>
            )}
          </aside>
        )}
      </div>
    </div>
  )
}

const s = {
  header: { display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.75rem' },
  back: { background: 'none', border: 'none', color: '#0251FD', cursor: 'pointer', fontSize: 14, fontWeight: 600 },
  h1: { fontFamily: "'Montserrat', sans-serif", fontWeight: 800, fontSize: 22, color: '#081D67', margin: 0 },
  error: { background: '#fef2f2', color: '#D7263D', borderRadius: 10, padding: '10px 14px', fontSize: 14, marginBottom: 16 },
  layout: { display: 'grid', gridTemplateColumns: '1fr 280px', gap: '2rem', alignItems: 'start' },
  form: { background: '#fff', borderRadius: 16, padding: '1.75rem', border: '1px solid #DDE8FF', boxShadow: '0 8px 24px rgba(8,29,103,0.06)' },
  field: { marginBottom: '1rem' },
  label: { display: 'block', fontSize: 12, fontWeight: 700, color: '#4A5680', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.04em' },
  input: { display: 'block', width: '100%', padding: '9px 12px', border: '1px solid #DDE8FF', borderRadius: 8, fontSize: 14, boxSizing: 'border-box', color: '#081D67', outline: 'none' },
  moneyPrefix: { position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: '#8A94A3', fontSize: 14, pointerEvents: 'none' },
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
  btnDisabled: { background: '#DDE8FF', color: '#8A94A3', cursor: 'not-allowed' },
  homeToggle: { display: 'flex', gap: 10, alignItems: 'flex-start', background: '#F4F6FB', border: '1px solid #DDE8FF', borderRadius: 10, padding: '12px 14px', margin: '4px 0 4px', cursor: 'pointer' },
  homeHint: { display: 'block', color: '#4A5680', fontSize: 12.5, marginTop: 2, fontWeight: 400 },
  row2: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' },
  row3: { display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' },
  btn: {
    width: '100%', background: '#0251FD', color: '#fff',
    border: 'none', borderRadius: 12, padding: '12px',
    fontSize: 15, fontWeight: 700, cursor: 'pointer', marginTop: 8,
    fontFamily: "'Montserrat', sans-serif",
  },
  aside: { background: '#fff', borderRadius: 16, padding: '1.5rem', border: '1px solid #DDE8FF', boxShadow: '0 8px 24px rgba(8,29,103,0.06)' },
  asideH: { fontFamily: "'Montserrat', sans-serif", fontWeight: 700, fontSize: 15, color: '#081D67', margin: '0 0 1rem' },
  uploadBtn: { width: '100%', background: '#F4F6FB', color: '#4A5680', border: '1px solid #DDE8FF', borderRadius: 10, padding: '9px', cursor: 'pointer', fontWeight: 600 },
  progress: { marginTop: 10, background: '#DDE8FF', borderRadius: 8, height: 18, position: 'relative', overflow: 'hidden' },
  progressBar: { height: '100%', background: '#0251FD', transition: 'width .3s' },
  progressLabel: { position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700, color: '#081D67' },
}
