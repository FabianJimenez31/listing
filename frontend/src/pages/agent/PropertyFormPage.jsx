import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { createProperty, getProperty, updateProperty, uploadImage } from '../../api/properties'
import { useAuth } from '../../contexts/AuthContext'
import Spinner from '../../components/ui/Spinner'

const EMPTY = {
  title: '', description: '', operation_type: 'sale', property_kind: 'house',
  price_amount: '', currency: 'COP', bedrooms: '', bathrooms: '',
  total_area_m2: '', built_area_m2: '', parking_spots: '',
  address_street: '', contact_phone: '', contact_whatsapp: '',
}

export default function PropertyFormPage() {
  const { id } = useParams()
  const isEdit = !!id
  const { user, loading: authLoading } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState(EMPTY)
  const [loading, setLoading] = useState(isEdit)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [uploadProgress, setUploadProgress] = useState(null)
  const fileRef = useRef()

  useEffect(() => {
    if (!authLoading && !user) { navigate('/login'); return }
    if (isEdit && user) {
      getProperty(id).then((data) => {
        setForm({
          title: data.title || '', description: data.description || '',
          operation_type: data.operation_type || 'sale', property_kind: data.property_kind || 'house',
          price_amount: data.price_amount || '', currency: data.currency || 'COP',
          bedrooms: data.bedrooms ?? '', bathrooms: data.bathrooms ?? '',
          total_area_m2: data.total_area_m2 ?? '', built_area_m2: data.built_area_m2 ?? '',
          parking_spots: data.parking_spots ?? '', address_street: data.address_street || '',
          contact_phone: data.contact_phone || '', contact_whatsapp: data.contact_whatsapp || '',
        })
      }).catch(() => navigate('/agente'))
        .finally(() => setLoading(false))
    }
  }, [user, authLoading, id])

  const upd = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

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
    if (payload.price_amount) payload.price_amount = parseInt(payload.price_amount, 10)
    if (payload.bedrooms !== '') payload.bedrooms = parseInt(payload.bedrooms, 10)
    if (payload.bathrooms !== '') payload.bathrooms = parseInt(payload.bathrooms, 10)
    if (payload.total_area_m2 !== '') payload.total_area_m2 = parseFloat(payload.total_area_m2)
    if (payload.built_area_m2 !== '') payload.built_area_m2 = parseFloat(payload.built_area_m2)
    if (payload.parking_spots !== '') payload.parking_spots = parseInt(payload.parking_spots, 10)
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

  const F = ({ label, k, type = 'text', as = 'input', options = null }) => (
    <div style={styles.field}>
      <label style={styles.label}>{label}</label>
      {as === 'textarea' ? (
        <textarea value={form[k]} onChange={upd(k)} style={{ ...styles.input, height: 90, resize: 'vertical' }} />
      ) : options ? (
        <select value={form[k]} onChange={upd(k)} style={styles.input}>
          {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      ) : (
        <input type={type} value={form[k]} onChange={upd(k)} style={styles.input} />
      )}
    </div>
  )

  return (
    <>
      <Helmet><title>{isEdit ? 'Editar propiedad' : 'Nueva propiedad'} | Listing</title></Helmet>

      <div style={styles.header}>
        <button onClick={() => navigate('/agente')} style={styles.back}>← Volver</button>
        <h1 style={styles.h1}>{isEdit ? 'Editar propiedad' : 'Nueva propiedad'}</h1>
      </div>

      {error && <p style={styles.error}>{error}</p>}

      <div style={styles.layout}>
        <form onSubmit={submit} style={styles.form}>
          <F label="Título *" k="title" />
          <F label="Descripción" k="description" as="textarea" />
          <div style={styles.row2}>
            <F label="Operación" k="operation_type" options={[['sale','Venta'],['rent','Renta'],['temporary','Temporal']]} />
            <F label="Tipo" k="property_kind" options={[['house','Casa'],['apartment','Apartamento'],['lot','Terreno'],['office','Oficina']]} />
          </div>
          <div style={styles.row2}>
            <F label="Precio (centavos) *" k="price_amount" type="number" />
            <F label="Moneda" k="currency" options={[['COP','COP'],['USD','USD'],['EUR','EUR']]} />
          </div>
          <div style={styles.row3}>
            <F label="Recámaras" k="bedrooms" type="number" />
            <F label="Baños" k="bathrooms" type="number" />
            <F label="Estacionamientos" k="parking_spots" type="number" />
          </div>
          <div style={styles.row2}>
            <F label="Área total m²" k="total_area_m2" type="number" />
            <F label="Área construida m²" k="built_area_m2" type="number" />
          </div>
          <F label="Dirección" k="address_street" />
          <F label="Teléfono de contacto" k="contact_phone" />
          <F label="WhatsApp de contacto" k="contact_whatsapp" />

          <button type="submit" disabled={saving} style={styles.btn}>
            {saving ? 'Guardando…' : isEdit ? 'Guardar cambios' : 'Crear propiedad'}
          </button>
        </form>

        {isEdit && (
          <aside style={styles.aside}>
            <h3 style={styles.asideH}>Imágenes</h3>
            <input type="file" ref={fileRef} multiple accept="image/*" onChange={handleImageUpload} style={{ display: 'none' }} />
            <button onClick={() => fileRef.current?.click()} style={styles.uploadBtn}>
              Subir imágenes
            </button>
            {uploadProgress !== null && (
              <div style={styles.progress}>
                <div style={{ ...styles.progressBar, width: `${uploadProgress}%` }} />
                <span style={styles.progressLabel}>{uploadProgress}%</span>
              </div>
            )}
          </aside>
        )}
      </div>
    </>
  )
}

const styles = {
  header: { display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' },
  back: { background: 'none', border: 'none', color: '#e94560', cursor: 'pointer', fontSize: 14 },
  h1: { fontSize: 22, color: '#1a1a2e', margin: 0 },
  error: { background: '#fef2f2', color: '#b91c1c', borderRadius: 6, padding: '10px 12px', fontSize: 14, marginBottom: 12 },
  layout: { display: 'grid', gridTemplateColumns: '1fr 280px', gap: '2rem', alignItems: 'start' },
  form: { background: '#fff', borderRadius: 10, padding: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,.07)' },
  field: { marginBottom: '1rem' },
  label: { display: 'block', fontSize: 13, color: '#555', marginBottom: 4 },
  input: { display: 'block', width: '100%', padding: '8px 10px', border: '1px solid #ddd', borderRadius: 6, fontSize: 14, boxSizing: 'border-box' },
  row2: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' },
  row3: { display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' },
  btn: { width: '100%', background: '#e94560', color: '#fff', border: 'none', borderRadius: 6, padding: '10px', fontSize: 15, fontWeight: 600, cursor: 'pointer', marginTop: 8 },
  aside: { background: '#fff', borderRadius: 10, padding: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,.07)' },
  asideH: { fontSize: 15, color: '#1a1a2e', margin: '0 0 1rem' },
  uploadBtn: { width: '100%', background: '#f0f0f0', color: '#333', border: '1px solid #ddd', borderRadius: 6, padding: '8px', cursor: 'pointer' },
  progress: { marginTop: 10, background: '#eee', borderRadius: 4, height: 18, position: 'relative', overflow: 'hidden' },
  progressBar: { height: '100%', background: '#e94560', transition: 'width .3s' },
  progressLabel: { position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 600 },
}
