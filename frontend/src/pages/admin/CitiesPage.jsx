import { useEffect, useRef, useState } from 'react'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../../contexts/AuthContext'
import { clearCityImage, getCities, uploadCityImage } from '../../api/catalog'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import LocationPicker from '../../components/property/LocationPicker'
import Spinner from '../../components/ui/Spinner'

// Seeded/external stock URLs are treated as "no manual image" (the home derives a
// real property cover for these), so the card shows them as Automática.
const PLACEHOLDER_HOSTS = ['picsum.photos', 'unsplash.com']
const isManual = (url) => Boolean(url) && !PLACEHOLDER_HOSTS.some((h) => url.includes(h))

function CityCard({ city, busy, onUpload, onClear }) {
  const fileRef = useRef(null)
  const manual = isManual(city.image_url)
  return (
    <div className="admin-card" style={{ padding: 14 }}>
      <div style={{ position: 'relative', height: 130, borderRadius: 10, overflow: 'hidden', background: '#0d1b33', marginBottom: 10 }}>
        {manual ? (
          <img src={city.image_url} alt={city.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        ) : (
          <div style={{ width: '100%', height: '100%', display: 'grid', placeItems: 'center', color: 'rgba(255,255,255,.65)', fontSize: 13, fontWeight: 600, textAlign: 'center', padding: 8 }}>
            Automática<br /><span style={{ fontSize: 11, opacity: .8 }}>(portada de una propiedad)</span>
          </div>
        )}
        {busy && (
          <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', background: 'rgba(13,27,51,.55)' }}>
            <Spinner />
          </div>
        )}
      </div>
      <div style={{ fontWeight: 800, color: 'var(--ink)', marginBottom: 8 }}>{city.name}</div>
      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        style={{ display: 'none' }}
        onChange={(e) => { const f = e.target.files?.[0]; if (f) onUpload(city.id, f); e.target.value = '' }}
      />
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button type="button" className="btn btn-blue btn-sm" disabled={busy} onClick={() => fileRef.current?.click()}>
          {manual ? 'Cambiar imagen' : 'Subir imagen'}
        </button>
        {manual && (
          <button type="button" className="btn btn-outline btn-sm" disabled={busy} onClick={() => onClear(city.id)}>
            Quitar
          </button>
        )}
      </div>
    </div>
  )
}

export default function CitiesPage() {
  const { user } = useAuth()
  const [cities, setCities] = useState([])
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState(null)
  const [error, setError] = useState(null)
  const [picked, setPicked] = useState('')

  const load = ({ silent = false } = {}) => {
    if (!silent) setLoading(true)
    getCities().then((c) => setCities(c || [])).catch(() => setCities([])).finally(() => setLoading(false))
  }

  useEffect(() => { if (user) load() }, [user])

  // Replace just the touched city in state so the rest of the list doesn't flicker.
  const replaceCity = (updated) => setCities((cs) => cs.map((c) => (c.id === updated.id ? updated : c)))

  const onUpload = async (id, file) => {
    setError(null); setBusyId(id)
    try {
      replaceCity(await uploadCityImage(id, file))
    } catch (err) {
      setError(err.response?.data?.error?.message || 'No se pudo subir la imagen')
    } finally {
      setBusyId(null)
    }
  }

  const onClear = async (id) => {
    setError(null); setBusyId(id)
    try {
      replaceCity(await clearCityImage(id))
    } catch (err) {
      setError(err.response?.data?.error?.message || 'No se pudo quitar la imagen')
    } finally {
      setBusyId(null)
    }
  }

  if (loading) return <Spinner />

  return (
    <>
      <Helmet><title>Ciudades | Proppia</title></Helmet>
      <AdminPageHeader
        title="Ciudades y ubicaciones"
        subtitle="Agrega países, departamentos y ciudades, y define la portada de cada ciudad"
      />

      {error && <p style={{ color: '#b91c1c', marginBottom: 12 }}>{error}</p>}

      <div className="admin-card admin-card-form">
        <h3 className="admin-card-title">Agregar países, departamentos y ciudades</h3>
        <p className="admin-hint" style={{ marginBottom: 14 }}>
          Elige el país (o créalo con «+ Agregar país que falta») y baja por la cascada hasta el nivel que necesites.
          Lo que agregues aquí queda disponible de inmediato en los formularios de propiedades y proyectos.
        </p>
        <div className="form-grid">
          <LocationPicker
            value={picked}
            onChange={(id) => { setPicked(id); load({ silent: true }) }}
            fieldClass="fg"
            inputClass=""
          />
        </div>
      </div>

      <h3 className="admin-card-title" style={{ margin: '22px 0 10px' }}>Portada de las ciudades</h3>

      <p style={{ color: 'var(--muted)', fontSize: 13.5, marginBottom: 16, maxWidth: 720 }}>
        Si no subes una imagen, la ciudad muestra automáticamente la portada de una propiedad publicada en ella.
        Sube una para fijarla manualmente; “Quitar” vuelve al modo automático. Recomendado: fotos horizontales, mín. 800×400.
      </p>

      {cities.length === 0 ? (
        <p style={{ color: 'var(--muted)' }}>No hay ciudades.</p>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 16 }}>
          {cities.map((c) => (
            <CityCard key={c.id} city={c} busy={busyId === c.id} onUpload={onUpload} onClear={onClear} />
          ))}
        </div>
      )}
    </>
  )
}
