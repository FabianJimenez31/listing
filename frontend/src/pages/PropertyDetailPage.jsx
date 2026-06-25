import { lazy, Suspense, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { getProperty } from '../api/properties'
import { addFavorite, removeFavorite } from '../api/favorites'
import { trackEvent } from '../api/admin'
import { useAuth } from '../contexts/AuthContext'
import LeadForm from '../components/property/LeadForm'
import { formatPrice } from '../components/property/PropertyCard'
import ImageCarousel from '../components/ui/ImageCarousel'
import Spinner from '../components/ui/Spinner'
import {
  IconArea, IconBath, IconBed, IconCar, IconCheck, IconHeart, IconPhone, IconPin, IconShare, IconWhatsapp,
} from '../components/ui/icons'

const PropertyMap = lazy(() => import('../components/property/PropertyMap'))

const OP = { sale: ['Venta', 'venta'], rent: ['Arriendo', 'arriendo'], temporary: ['Temporal', 'arriendo'] }
const KIND_LABEL = {
  house: 'Casa', apartment: 'Apartamento', lot: 'Lote', office: 'Oficina',
  commercial: 'Local comercial', farm: 'Finca', warehouse: 'Bodega', other: 'Otro',
}
const CONDITION_LABEL = { new: 'Nuevo', used: 'Usado', remodeled: 'Remodelado', under_construction: 'En construcción' }
const STATUS_LABEL = { paused: 'Pausado', sold: 'Vendido', rented: 'Arrendado' }
const VIEW_LABEL = { internal: 'Interna', external: 'Externa' }
const SECURITY_LABEL = { none: 'Sin vigilancia', private: 'Privada', automated: 'Automatizada' }

// "5 años", "1 año", "Menos de 1 año" (0).
const formatAge = (years) => (years === 0 ? 'Menos de 1 año' : `${years} año${years === 1 ? '' : 's'}`)

function buildWhatsappUrl(phone, title, url) {
  const clean = phone.replace(/\D/g, '')
  const text = encodeURIComponent(`Hola, me interesa la propiedad: ${title}\n${url}`)
  return `https://wa.me/${clean}?text=${text}`
}

async function shareProperty(title, url) {
  if (navigator.share) {
    try { await navigator.share({ title, url }); return } catch (_) { /* cancelled */ }
  }
  await navigator.clipboard.writeText(url)
  return 'copied'
}

export default function PropertyDetailPage() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [property, setProperty] = useState(null)
  const [loading, setLoading] = useState(true)
  const [isFav, setIsFav] = useState(false)
  const [favLoading, setFavLoading] = useState(false)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    setLoading(true)
    getProperty(slug)
      .then((data) => {
        setProperty(data)
        trackEvent('view', data.id, null).catch(() => null)
      })
      .catch(() => navigate('/404', { replace: true }))
      .finally(() => setLoading(false))
  }, [slug])

  if (loading) return <div className="page-wrap"><Spinner /></div>
  if (!property) return null

  const images = property.images || []
  const main = images[0]

  const pageUrl = window.location.href
  const [opLabel, opClass] = OP[property.operation_type] || ['Venta', 'venta']
  const isUSA = property.currency === 'USD'
  const perMonth = property.operation_type === 'rent' || property.operation_type === 'temporary'
  const price = formatPrice(property.price_amount, property.currency) || 'Precio a consultar'

  const waPhone = property.contact_whatsapp || property.contact_phone || property.owner?.phone
  const callPhone = property.contact_phone || property.owner?.phone
  const mapLat = property.location?.center_lat
  const mapLng = property.location?.center_lng

  const agency = property.agency
  const contactName = agency?.name || property.owner?.full_name || 'Proppietario'
  const contactRole = agency ? 'Inmobiliaria' : 'Asesor'
  const initials = (agency?.initials || contactName).slice(0, 2).toUpperCase()

  const areaLabel = ['house', 'lot', 'farm'].includes(property.property_kind) ? 'Área de lote' : 'Área total'
  const facts = [
    ['Operación', opLabel],
    ['Tipo', KIND_LABEL[property.property_kind] || property.property_kind],
    // Áreas
    property.total_area_m2 != null && [areaLabel, `${property.total_area_m2} m²`],
    property.built_area_m2 != null && ['Área construida', `${property.built_area_m2} m²`],
    // Distribución y atributos
    property.bedrooms != null && ['Habitaciones', property.bedrooms],
    property.bathrooms != null && ['Baños', property.bathrooms],
    property.parking_spots != null && ['Parqueaderos', property.parking_spots],
    property.stratum != null && ['Estrato', property.stratum],
    property.floor_number != null && ['Piso', property.total_floors ? `${property.floor_number} de ${property.total_floors}` : property.floor_number],
    property.age_years != null && ['Antigüedad', formatAge(property.age_years)],
    property.condition && ['Estado', CONDITION_LABEL[property.condition] || property.condition],
    property.view_type && ['Vista', VIEW_LABEL[property.view_type] || property.view_type],
    property.admin_fee_amount != null && ['Administración', `${formatPrice(property.admin_fee_amount, property.currency)} / mes`],
    property.security_type && property.security_type !== 'none' && ['Vigilancia', SECURITY_LABEL[property.security_type] || property.security_type],
    property.has_balcony && ['Balcón / Terraza', 'Sí'],
    property.has_elevator && ['Ascensor', 'Sí'],
    property.has_storage && ['Depósito / Bodega', 'Sí'],
    property.has_study && ['Zona de estudio', 'Sí'],
    ['Código', property.nid],
  ].filter(Boolean)

  const trackCta = () => trackEvent('cta_click', property.id, null).catch(() => null)
  const handleShare = async () => {
    const result = await shareProperty(property.title, pageUrl)
    if (result === 'copied') { setCopied(true); setTimeout(() => setCopied(false), 2500) }
    trackCta()
  }
  const toggleFav = () => {
    setFavLoading(true)
    const action = isFav ? removeFavorite(property.id) : addFavorite(property.id)
    action.then(() => setIsFav((v) => !v)).catch(() => null).finally(() => setFavLoading(false))
  }

  return (
    <div className="page-wrap">
      <Helmet>
        <title>{`${property.title} | Proppietario`}</title>
        <meta name="description" content={property.description?.slice(0, 155) || property.title} />
        <meta property="og:title" content={property.title} />
        {main && <meta property="og:image" content={main.cdn_url} />}
        <link rel="canonical" href={`${window.location.origin}/propiedades/${property.nid}`} />
      </Helmet>

      <div className="pdp-crumbs">
        <Link to="/">Inicio</Link> · <Link to={`/propiedades?operation_type=${property.operation_type}`}>{opLabel}</Link>
        {(property.location?.path?.length ? property.location.path : (property.location ? [property.location] : []))
          .map((c) => <span key={c.id}> · {c.name}</span>)}
      </div>

      {/* Gallery carousel */}
      <div className="pdp-hero">
        <div className="badges">
          {isUSA && <span className="badge usa">USA</span>}
          <span className={`badge ${opClass}`}>{opLabel}</span>
          {STATUS_LABEL[property.status] && <span className="badge proyecto">{STATUS_LABEL[property.status]}</span>}
        </div>
        <div className="pdp-gtools">
          {user && (
            <button className={`pdp-gtool fav ${isFav ? 'on' : ''}`} disabled={favLoading} onClick={toggleFav} aria-label="Guardar en favoritos">
              <IconHeart />
            </button>
          )}
          <button className="pdp-gtool" onClick={handleShare} aria-label="Compartir">
            <IconShare />
          </button>
        </div>
        <ImageCarousel images={images} alt={property.title} />
      </div>

      <div className="detail-cols">
        {/* Main column */}
        <div>
          <div className="pdp-head">
            <h1>{property.title}</h1>
            {property.location?.name && <div className="pdp-loc"><IconPin /> {property.location.name}</div>}
            <div className="pdp-price">{price}{perMonth && <small> / mes</small>}</div>
          </div>

          <div className="pdp-specs">
            {property.total_area_m2 != null && (
              <div className="pdp-spec"><span className="ic"><IconArea /></span><span className="v">{property.total_area_m2} m²</span><span className="k">{areaLabel}</span></div>
            )}
            {property.bedrooms != null && (
              <div className="pdp-spec"><span className="ic"><IconBed /></span><span className="v">{property.bedrooms}</span><span className="k">Habitaciones</span></div>
            )}
            {property.bathrooms != null && (
              <div className="pdp-spec"><span className="ic"><IconBath /></span><span className="v">{property.bathrooms}</span><span className="k">Baños</span></div>
            )}
            {property.parking_spots != null && (
              <div className="pdp-spec"><span className="ic"><IconCar /></span><span className="v">{property.parking_spots}</span><span className="k">Parqueaderos</span></div>
            )}
            {property.age_years != null && (
              <div className="pdp-spec"><span className="ic"><IconCheck /></span><span className="v">{formatAge(property.age_years)}</span><span className="k">Antigüedad</span></div>
            )}
            {property.condition && (
              <div className="pdp-spec"><span className="ic"><IconCheck /></span><span className="v">{CONDITION_LABEL[property.condition] || property.condition}</span><span className="k">Estado</span></div>
            )}
          </div>

          {property.description && (
            <section className="pdp-section">
              <h2>Descripción</h2>
              <div className="prose"><p>{property.description}</p></div>
            </section>
          )}

          <section className="pdp-section">
            <h2>Detalles</h2>
            <div className="pdp-facts">
              {facts.map(([k, v]) => (
                <div className="pdp-fact" key={k}><span className="k">{k}</span><span className="v">{v}</span></div>
              ))}
            </div>
          </section>

          {mapLat && mapLng && (
            <section className="pdp-section">
              <h2>Ubicación</h2>
              <div className="pdp-map">
                <Suspense fallback={<div style={{ height: 280, background: 'var(--bg-soft)' }} />}>
                  <PropertyMap lat={mapLat} lng={mapLng} title={property.title} />
                </Suspense>
              </div>
            </section>
          )}

          <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'RealEstateListing',
            name: property.title,
            description: property.description || '',
            url: `${window.location.origin}/propiedades/${property.nid}`,
            image: main?.cdn_url || '',
            ...(mapLat && mapLng ? { geo: { '@type': 'GeoCoordinates', latitude: mapLat, longitude: mapLng } } : {}),
          }) }} />
        </div>

        {/* Sticky contact aside */}
        <aside className="pdp-aside">
          <div className="pdp-contact">
            <div className="op">{opLabel}{isUSA ? ' · USA' : ''}</div>
            <div className="price">{price}{perMonth && <small> / mes</small>}</div>

            <div className="pdp-agent">
              <span className="av">{initials}</span>
              <div>
                <div className="nm">{contactName}</div>
                <div className="ro">{contactRole}</div>
              </div>
            </div>

            <div className="pdp-actions">
              {waPhone && (
                <a className="btn btn-wa" href={buildWhatsappUrl(waPhone, property.title, pageUrl)} target="_blank" rel="noopener noreferrer" onClick={trackCta}>
                  <IconWhatsapp /> Consultar por WhatsApp
                </a>
              )}
              {callPhone && (
                <a className="btn btn-outline" href={`tel:${callPhone}`} onClick={trackCta}>
                  <IconPhone /> Llamar al asesor
                </a>
              )}
              <button className="btn btn-outline" onClick={handleShare}>
                <IconShare /> {copied ? 'Enlace copiado ✓' : 'Compartir'}
              </button>
              {agency && (
                <Link className="btn btn-outline" to={`/inmobiliarias/${agency.slug}`}>Ver inmobiliaria</Link>
              )}
            </div>
          </div>

          <div className="pdp-contact">
            <LeadForm propertyId={property.id} />
          </div>
        </aside>
      </div>
    </div>
  )
}
