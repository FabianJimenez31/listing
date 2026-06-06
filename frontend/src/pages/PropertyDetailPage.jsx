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
      .then((data) => {
        setProperty(data)
        trackEvent('view', data.id, null).catch(() => null)
      })
      .catch(() => navigate('/404', { replace: true }))
      .finally(() => setLoading(false))
  }, [slug])

  if (loading) return <Spinner />
  if (!property) return null

  const images = property.images || []
  const mainImg = images[activeImg] || images[0]
  const pageUrl = window.location.href

  // Contact: prefer explicit contact fields, fall back to owner's phone
  const waPhone = property.contact_whatsapp || property.contact_phone || property.owner?.phone
  const callPhone = property.contact_phone || property.owner?.phone

  // Map coordinates: from location centroid
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
    <>
      <Helmet>
        <title>{property.title} | Listing</title>
        <meta name="description" content={property.description?.slice(0, 155) || property.title} />
        <meta property="og:title" content={property.title} />
        <meta property="og:description" content={property.description?.slice(0, 155) || ''} />
        {mainImg && <meta property="og:image" content={mainImg.cdn_url} />}
        <link rel="canonical" href={`${window.location.origin}/propiedades/${property.slug}`} />
      </Helmet>

      {/* Gallery */}
      <div style={s.gallery}>
        <div style={s.mainImg}>
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
                style={{ ...s.thumb, border: i === activeImg ? '2px solid #e94560' : '2px solid transparent' }}
              />
            ))}
          </div>
        )}
      </div>

      {/* Content */}
      <div style={s.layout}>
        <div style={s.info}>
          <div style={s.statusRow}>
            <span style={s.opBadge}>{OP_LABEL[property.operation_type]}</span>
            {property.status !== 'published' && (
              <span style={s.statusBadge}>{STATUS_LABEL[property.status] || property.status}</span>
            )}
          </div>

          <h1 style={s.title}>{property.title}</h1>
          {property.location && <p style={s.location}>{property.location.name}</p>}
          <p style={s.price}>{formatPrice(property.price_amount, property.currency)}</p>

          <div style={s.specs}>
            {property.bedrooms != null && <div style={s.spec}><strong>{property.bedrooms}</strong><br />Recámaras</div>}
            {property.bathrooms != null && <div style={s.spec}><strong>{property.bathrooms}</strong><br />Baños</div>}
            {property.total_area_m2 != null && <div style={s.spec}><strong>{property.total_area_m2}</strong><br />m² totales</div>}
            {property.built_area_m2 != null && <div style={s.spec}><strong>{property.built_area_m2}</strong><br />m² construidos</div>}
            {property.parking_spots != null && <div style={s.spec}><strong>{property.parking_spots}</strong><br />Estac.</div>}
          </div>

          {property.description && (
            <div style={s.desc}>
              <h2 style={s.descH}>Descripción</h2>
              <p style={s.descText}>{property.description}</p>
            </div>
          )}

          {/* Map */}
          {(mapLat && mapLng) && (
            <div style={s.mapSection}>
              <h2 style={s.descH}>Ubicación</h2>
              <Suspense fallback={<div style={{ height: 280, background: '#f5f5f5', borderRadius: 12 }} />}>
                <PropertyMap lat={mapLat} lng={mapLng} title={property.title} />
              </Suspense>
            </div>
          )}

          {/* JSON-LD */}
          <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'RealEstateListing',
            name: property.title,
            description: property.description || '',
            url: `${window.location.origin}/propiedades/${property.slug}`,
            image: mainImg?.cdn_url || '',
            ...(mapLat && mapLng ? {
              geo: { '@type': 'GeoCoordinates', latitude: mapLat, longitude: mapLng },
            } : {}),
          })}} />
        </div>

        <aside style={s.aside}>
          {/* Primary CTAs */}
          {waPhone && (
            <a
              href={buildWhatsappUrl(waPhone, property.title, pageUrl)}
              target="_blank"
              rel="noopener noreferrer"
              style={s.ctaWa}
              onClick={handleWa}
            >
              <span style={s.ctaIcon}>💬</span> WhatsApp
            </a>
          )}
          {callPhone && (
            <a href={`tel:${callPhone}`} style={s.ctaCall} onClick={handleCall}>
              <span style={s.ctaIcon}>📞</span> Llamar
            </a>
          )}

          {/* Share */}
          <button style={s.ctaShare} onClick={handleShare}>
            {copied ? '✓ Enlace copiado' : '🔗 Compartir'}
          </button>

          {/* Favorite */}
          {user && (
            <button
              style={{ ...s.favBtn, background: isFav ? '#e94560' : '#fff', color: isFav ? '#fff' : '#e94560' }}
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
    </>
  )
}

const s = {
  gallery: { marginBottom: '2rem' },
  mainImg: { height: 440, borderRadius: 12, overflow: 'hidden', background: '#eee', marginBottom: 8 },
  mainImgEl: { width: '100%', height: '100%', objectFit: 'cover' },
  noImg: { display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#aaa', fontSize: 18 },
  thumbRow: { display: 'flex', gap: 8, overflowX: 'auto', paddingBottom: 4 },
  thumb: { width: 80, height: 60, objectFit: 'cover', borderRadius: 6, cursor: 'pointer' },
  layout: { display: 'grid', gridTemplateColumns: '1fr 360px', gap: '2rem', alignItems: 'start' },
  info: {},
  aside: { display: 'flex', flexDirection: 'column', gap: '0.75rem' },
  statusRow: { display: 'flex', gap: 8, marginBottom: 8 },
  opBadge: { background: '#e94560', color: '#fff', borderRadius: 4, padding: '3px 10px', fontSize: 13, fontWeight: 600 },
  statusBadge: { background: '#f0a500', color: '#fff', borderRadius: 4, padding: '3px 10px', fontSize: 13, fontWeight: 600 },
  title: { fontSize: 26, color: '#1a1a2e', margin: '0 0 .5rem' },
  location: { color: '#666', fontSize: 15, margin: '0 0 .75rem' },
  price: { color: '#e94560', fontSize: 28, fontWeight: 700, margin: '0 0 1.5rem' },
  specs: { display: 'flex', gap: '1.5rem', margin: '0 0 1.5rem', flexWrap: 'wrap' },
  spec: { textAlign: 'center', fontSize: 14, color: '#555', lineHeight: 1.4 },
  desc: { margin: '0 0 1.5rem' },
  descH: { fontSize: 16, color: '#1a1a2e', marginBottom: '.5rem' },
  descText: { color: '#444', lineHeight: 1.7 },
  mapSection: { margin: '0 0 1.5rem' },
  ctaWa: {
    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
    background: '#25D366', color: '#fff', textDecoration: 'none',
    borderRadius: 8, padding: '12px 16px', fontWeight: 700, fontSize: 15,
  },
  ctaCall: {
    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
    background: '#1a1a2e', color: '#fff', textDecoration: 'none',
    borderRadius: 8, padding: '12px 16px', fontWeight: 700, fontSize: 15,
  },
  ctaShare: {
    background: '#f5f5f5', border: '1px solid #ddd', borderRadius: 8,
    padding: '10px 16px', fontWeight: 600, fontSize: 14, cursor: 'pointer', color: '#444',
  },
  favBtn: {
    border: '2px solid #e94560', borderRadius: 8, padding: '10px 16px',
    fontSize: 14, fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s',
  },
  ctaIcon: { fontSize: 18 },
}
