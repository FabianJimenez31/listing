import { useEffect, useState, lazy, Suspense } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { getProperty } from '../api/properties'
import { addFavorite, removeFavorite } from '../api/favorites'
import { useAuth } from '../contexts/AuthContext'
import LeadForm from '../components/property/LeadForm'
import Spinner from '../components/ui/Spinner'
import { trackEvent } from '../api/admin'

const PropertyMap = lazy(() => import('../components/property/PropertyMap'))

const STATUS_LABEL = { published: 'Publicado', paused: 'Pausado', sold: 'Vendido', rented: 'Arrendado' }
const OP_LABEL = { sale: 'Venta', rent: 'Arriendo', temporary: 'Temporal' }

function formatPrice(amount, currency) {
  if (!amount) return 'Precio a consultar'
  return new Intl.NumberFormat('es-CO', {
    style: 'currency', currency: currency || 'COP', maximumFractionDigits: 0,
  }).format(amount / 100)
}

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
  const [activeImg, setActiveImg] = useState(0)
  const [isFav, setIsFav] = useState(false)
  const [favLoading, setFavLoading] = useState(false)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    setLoading(true)
    getProperty(slug)
      .then(data => {
        setProperty(data)
        trackEvent('view', data.id, null).catch(() => null)
      })
      .catch(() => navigate('/404', { replace: true }))
      .finally(() => setLoading(false))
  }, [slug])

  const pageTitle = property ? `${property.title} | Proppietario` : 'Cargando... | Proppietario'

  if (loading) return (
    <div className="page-wrap">
      <Helmet><title>{pageTitle}</title></Helmet>
      <Spinner />
    </div>
  )
  if (!property) return null

  const images = property.images || []
  const mainImg = images[activeImg] || images[0]
  const pageUrl = window.location.href

  const waPhone = property.contact_whatsapp || property.contact_phone || property.owner?.phone
  const callPhone = property.contact_phone || property.owner?.phone
  const mapLat = property.location?.center_lat
  const mapLng = property.location?.center_lng

  const handleShare = async () => {
    const result = await shareProperty(property.title, pageUrl)
    if (result === 'copied') {
      setCopied(true)
      setTimeout(() => setCopied(false), 2500)
    }
    trackEvent('cta_click', property.id, null).catch(() => null)
  }

  const handleWa = () => trackEvent('cta_click', property.id, null).catch(() => null)
  const handleCall = () => trackEvent('cta_click', property.id, null).catch(() => null)

  return (
    <div className="page-wrap">
      <Helmet>
        <title>{pageTitle}</title>
        <meta name="description" content={property.description?.slice(0, 155) || property.title} />
        <meta property="og:title" content={property.title} />
        <meta property="og:description" content={property.description?.slice(0, 155) || ''} />
        {mainImg && <meta property="og:image" content={mainImg.cdn_url} />}
        <link rel="canonical" href={`${window.location.origin}/propiedades/${property.slug}`} />
      </Helmet>

      {/* Gallery */}
      <div style={s.gallery}>
        <div style={s.mainImgWrap}>
          {mainImg
            ? <img src={mainImg.cdn_url} alt={mainImg.alt_text || property.title} style={s.mainImgEl} />
            : <div style={s.noImg}>Sin imágenes</div>
          }
        </div>
        {images.length > 1 && (
          <div style={s.thumbRow}>
            {images.map((img, i) => (
              <img
                key={img.id}
                src={img.thumb_url || img.cdn_url}
                alt=""
                onClick={() => setActiveImg(i)}
                style={{
                  ...s.thumb,
                  border: i === activeImg ? '2px solid #0251FD' : '2px solid transparent',
                  opacity: i === activeImg ? 1 : 0.7,
                }}
              />
            ))}
          </div>
        )}
      </div>

      {/* Content layout */}
      <div style={s.layout}>
        <div style={s.info}>
          {/* Badges */}
          <div style={s.badgeRow}>
            <span style={s.opBadge}>{OP_LABEL[property.operation_type]}</span>
            {property.status !== 'published' && (
              <span style={s.statusBadge}>{STATUS_LABEL[property.status] || property.status}</span>
            )}
          </div>

          <h1 style={s.title}>{property.title}</h1>
          {property.location && <p style={s.location}>📍 {property.location.name}</p>}

          <p style={s.price}>{formatPrice(property.price_amount, property.currency)}</p>

          {/* Specs */}
          {(property.bedrooms != null || property.bathrooms != null || property.total_area_m2 != null || property.built_area_m2 != null || property.parking_spots != null) && (
            <div style={s.specs}>
              {property.bedrooms != null && <div style={s.spec}><strong style={s.specNum}>{property.bedrooms}</strong><span>Recámaras</span></div>}
              {property.bathrooms != null && <div style={s.spec}><strong style={s.specNum}>{property.bathrooms}</strong><span>Baños</span></div>}
              {property.total_area_m2 != null && <div style={s.spec}><strong style={s.specNum}>{property.total_area_m2}</strong><span>m² totales</span></div>}
              {property.built_area_m2 != null && <div style={s.spec}><strong style={s.specNum}>{property.built_area_m2}</strong><span>m² construidos</span></div>}
              {property.parking_spots != null && <div style={s.spec}><strong style={s.specNum}>{property.parking_spots}</strong><span>Estac.</span></div>}
            </div>
          )}

          {/* Description */}
          {property.description && (
            <div style={s.descSection}>
              <h2 style={s.sectionH}>Descripción</h2>
              <p style={s.descText}>{property.description}</p>
            </div>
          )}

          {/* Map */}
          {(mapLat && mapLng) && (
            <div style={s.mapSection}>
              <h2 style={s.sectionH}>Ubicación</h2>
              <Suspense fallback={<div style={{ height: 280, background: '#F4F6FB', borderRadius: 16 }} />}>
                <PropertyMap lat={mapLat} lng={mapLng} title={property.title} />
              </Suspense>
            </div>
          )}

          <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'RealEstateListing',
            name: property.title,
            description: property.description || '',
            url: `${window.location.origin}/propiedades/${property.slug}`,
            image: mainImg?.cdn_url || '',
            ...(mapLat && mapLng ? { geo: { '@type': 'GeoCoordinates', latitude: mapLat, longitude: mapLng } } : {}),
          })}} />
        </div>

        {/* Aside */}
        <aside style={s.aside}>
          {waPhone && (
            <a
              href={buildWhatsappUrl(waPhone, property.title, pageUrl)}
              target="_blank"
              rel="noopener noreferrer"
              style={s.ctaWa}
              onClick={handleWa}
            >
              💬 Consultar por WhatsApp
            </a>
          )}
          {callPhone && (
            <a href={`tel:${callPhone}`} style={s.ctaCall} onClick={handleCall}>
              📞 Llamar al asesor
            </a>
          )}
          <button style={s.ctaShare} onClick={handleShare}>
            {copied ? '✓ Enlace copiado' : '🔗 Compartir propiedad'}
          </button>
          {user && (
            <button
              style={isFav ? s.favBtnActive : s.favBtn}
              disabled={favLoading}
              onClick={() => {
                setFavLoading(true)
                const action = isFav ? removeFavorite(property.id) : addFavorite(property.id)
                action.then(() => setIsFav(v => !v)).catch(() => null).finally(() => setFavLoading(false))
              }}
            >
              {isFav ? '♥ En favoritos' : '♡ Guardar en favoritos'}
            </button>
          )}
          <LeadForm propertyId={property.id} />
        </aside>
      </div>
    </div>
  )
}

const s = {
  gallery: { marginBottom: '2rem' },
  mainImgWrap: {
    height: 460,
    borderRadius: 20,
    overflow: 'hidden',
    background: '#F4F6FB',
    marginBottom: 10,
  },
  mainImgEl: { width: '100%', height: '100%', objectFit: 'cover' },
  noImg: {
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    height: '100%', color: '#4A5680', fontSize: 18,
  },
  thumbRow: { display: 'flex', gap: 8, overflowX: 'auto', paddingBottom: 4 },
  thumb: { width: 80, height: 60, objectFit: 'cover', borderRadius: 8, cursor: 'pointer', transition: 'all 150ms' },
  layout: { display: 'grid', gridTemplateColumns: '1fr 360px', gap: '2rem', alignItems: 'start' },
  info: {},
  aside: { display: 'flex', flexDirection: 'column', gap: '0.75rem', position: 'sticky', top: 90 },
  badgeRow: { display: 'flex', gap: 8, marginBottom: '0.75rem', flexWrap: 'wrap' },
  opBadge: {
    background: '#DDE8FF', color: '#081D67',
    borderRadius: 999, padding: '4px 14px',
    fontSize: 13, fontWeight: 700,
    fontFamily: "'Montserrat', sans-serif",
  },
  statusBadge: {
    background: '#FFF3CD', color: '#856404',
    borderRadius: 999, padding: '4px 14px',
    fontSize: 13, fontWeight: 700,
  },
  title: {
    fontFamily: "'Montserrat', sans-serif",
    fontWeight: 800,
    fontSize: 28,
    color: '#081D67',
    margin: '0 0 0.5rem',
    lineHeight: 1.2,
  },
  location: { color: '#4A5680', fontSize: 15, margin: '0 0 1rem' },
  price: {
    fontFamily: "'Montserrat', sans-serif",
    fontWeight: 800,
    fontSize: 32,
    color: '#0251FD',
    margin: '0 0 1.5rem',
  },
  specs: {
    display: 'flex',
    gap: '1rem',
    margin: '0 0 1.75rem',
    flexWrap: 'wrap',
    padding: '1.25rem',
    background: '#F4F6FB',
    borderRadius: 16,
    border: '1px solid #DDE8FF',
  },
  spec: { textAlign: 'center', fontSize: 13, color: '#4A5680', lineHeight: 1.4, display: 'flex', flexDirection: 'column', gap: 2 },
  specNum: { fontFamily: "'Montserrat', sans-serif", fontWeight: 700, fontSize: 20, color: '#081D67' },
  descSection: { margin: '0 0 1.75rem' },
  sectionH: {
    fontFamily: "'Montserrat', sans-serif",
    fontWeight: 700,
    fontSize: 17,
    color: '#081D67',
    marginBottom: '0.75rem',
  },
  descText: { color: '#4A5680', lineHeight: 1.75, fontSize: 16 },
  mapSection: { margin: '0 0 1.75rem' },
  ctaWa: {
    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
    background: '#25D366', color: '#fff', textDecoration: 'none',
    borderRadius: 12, padding: '14px 16px', fontWeight: 700, fontSize: 15,
    fontFamily: "'Montserrat', sans-serif",
  },
  ctaCall: {
    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
    background: '#081D67', color: '#fff', textDecoration: 'none',
    borderRadius: 12, padding: '14px 16px', fontWeight: 700, fontSize: 15,
    fontFamily: "'Montserrat', sans-serif",
  },
  ctaShare: {
    background: '#F4F6FB', border: '1px solid #DDE8FF', borderRadius: 12,
    padding: '12px 16px', fontWeight: 600, fontSize: 14, cursor: 'pointer', color: '#4A5680',
    width: '100%',
  },
  favBtn: {
    background: '#fff',
    border: '2px solid #DDE8FF',
    borderRadius: 12,
    padding: '12px 16px',
    fontSize: 14,
    fontWeight: 600,
    cursor: 'pointer',
    color: '#4A5680',
    width: '100%',
    transition: 'all 200ms',
  },
  favBtnActive: {
    background: '#0251FD',
    border: '2px solid #0251FD',
    borderRadius: 12,
    padding: '12px 16px',
    fontSize: 14,
    fontWeight: 600,
    cursor: 'pointer',
    color: '#fff',
    width: '100%',
    transition: 'all 200ms',
  },
}
