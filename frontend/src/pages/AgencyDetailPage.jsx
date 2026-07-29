import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { getAgency } from '../api/agencies'
import { searchProperties } from '../api/properties'
import PropertyCard from '../components/property/PropertyCard'
import Spinner from '../components/ui/Spinner'

export default function AgencyDetailPage() {
  const { slug } = useParams()
  const [agency, setAgency] = useState(null)
  const [properties, setProperties] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    setLoading(true)
    setError(false)
    getAgency(slug)
      .then((a) => {
        setAgency(a)
        return searchProperties({ agency_id: a.id, page_size: 24 })
      })
      .then((res) => setProperties(res?.data || []))
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [slug])

  if (loading) return <div className="page-wrap"><Spinner /></div>
  if (error || !agency) {
    return (
      <div className="page-wrap">
        <p>Inmobiliaria no encontrada.</p>
        <Link to="/inmobiliarias" className="seelink">← Volver a inmobiliarias</Link>
      </div>
    )
  }

  return (
    <div className="page-wrap">
      <Helmet><title>{`${agency.name} | Proppia`}</title></Helmet>
      <div className="crumbs"><Link to="/inmobiliarias">Inmobiliarias</Link> · {agency.name}</div>

      <div className="agency-card" style={{ marginBottom: 28 }}>
        <span className="lg" style={{ width: 64, height: 64, fontSize: 22 }}>
          {agency.initials || agency.name.slice(0, 2).toUpperCase()}
        </span>
        <div>
          <div className="nm" style={{ fontSize: 22 }}>{agency.name}{agency.is_verified ? ' ✓' : ''}</div>
          <div className="meta">{agency.property_count} propiedades publicadas</div>
          {agency.description && <div className="meta" style={{ marginTop: 6 }}>{agency.description}</div>}
          <div style={{ display: 'flex', gap: 10, marginTop: 12 }}>
            {agency.whatsapp && (
              <a className="btn btn-blue" href={`https://wa.me/${agency.whatsapp.replace(/[^0-9]/g, '')}`} target="_blank" rel="noreferrer">WhatsApp</a>
            )}
            {agency.phone && <a className="btn btn-outline" href={`tel:${agency.phone}`}>Llamar</a>}
          </div>
        </div>
      </div>

      <h3 style={{ fontSize: 20, fontWeight: 800, color: 'var(--ink)', marginBottom: 16 }}>Propiedades de {agency.name}</h3>
      {properties.length === 0 ? (
        <p style={{ color: 'var(--muted)' }}>Esta inmobiliaria aún no tiene propiedades publicadas.</p>
      ) : (
        <div className="prop-grid">
          {properties.map((p) => <PropertyCard key={p.id} property={p} />)}
        </div>
      )}
    </div>
  )
}
