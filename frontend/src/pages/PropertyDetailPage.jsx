import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { getProperty } from '../api/properties'
import LeadForm from '../components/property/LeadForm'
import Spinner from '../components/ui/Spinner'
import { trackEvent } from '../api/admin'

const STATUS_LABEL = { published: 'Publicado', paused: 'Pausado', sold: 'Vendido', rented: 'Rentado' }
const OP_LABEL = { sale: 'Venta', rent: 'Renta', temporary: 'Temporal' }

function formatPrice(amount, currency) {
  if (!amount) return 'Precio a consultar'
  return new Intl.NumberFormat('es-MX', { style: 'currency', currency: currency || 'MXN', maximumFractionDigits: 0 }).format(amount / 100)
}

export default function PropertyDetailPage() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const [property, setProperty] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeImg, setActiveImg] = useState(0)

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
      <div style={styles.gallery}>
        <div style={styles.mainImg}>
          {mainImg ? (
            <img src={mainImg.cdn_url} alt={mainImg.alt_text || property.title} style={styles.mainImgEl} />
          ) : (
            <div style={styles.noImg}>Sin imágenes</div>
          )}
        </div>
        {images.length > 1 && (
          <div style={styles.thumbRow}>
            {images.map((img, i) => (
              <img
                key={img.id}
                src={img.thumb_url || img.cdn_url}
                alt=""
                onClick={() => setActiveImg(i)}
                style={{ ...styles.thumb, border: i === activeImg ? '2px solid #e94560' : '2px solid transparent' }}
              />
            ))}
          </div>
        )}
      </div>

      {/* Detail */}
      <div style={styles.layout}>
        <div style={styles.info}>
          <div style={styles.statusRow}>
            <span style={styles.opBadge}>{OP_LABEL[property.operation_type]}</span>
            {property.status !== 'published' && (
              <span style={styles.statusBadge}>{STATUS_LABEL[property.status] || property.status}</span>
            )}
          </div>
          <h1 style={styles.title}>{property.title}</h1>
          {property.location && <p style={styles.location}>{property.location.name}</p>}
          <p style={styles.price}>{formatPrice(property.price_amount, property.currency)}</p>

          <div style={styles.specs}>
            {property.bedrooms != null && <div style={styles.spec}><strong>{property.bedrooms}</strong><br />Recámaras</div>}
            {property.bathrooms != null && <div style={styles.spec}><strong>{property.bathrooms}</strong><br />Baños</div>}
            {property.total_area_m2 != null && <div style={styles.spec}><strong>{property.total_area_m2}</strong><br />m² totales</div>}
            {property.built_area_m2 != null && <div style={styles.spec}><strong>{property.built_area_m2}</strong><br />m² construidos</div>}
            {property.parking_spots != null && <div style={styles.spec}><strong>{property.parking_spots}</strong><br />Estac.</div>}
          </div>

          {property.description && (
            <div style={styles.desc}>
              <h2 style={styles.descH}>Descripción</h2>
              <p style={styles.descText}>{property.description}</p>
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
          })}} />
        </div>

        <aside style={styles.aside}>
          <LeadForm propertyId={property.id} />
        </aside>
      </div>
    </>
  )
}

const styles = {
  gallery: { marginBottom: '2rem' },
  mainImg: { height: 440, borderRadius: 12, overflow: 'hidden', background: '#eee', marginBottom: 8 },
  mainImgEl: { width: '100%', height: '100%', objectFit: 'cover' },
  noImg: { display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#aaa', fontSize: 18 },
  thumbRow: { display: 'flex', gap: 8, overflowX: 'auto', paddingBottom: 4 },
  thumb: { width: 80, height: 60, objectFit: 'cover', borderRadius: 6, cursor: 'pointer' },
  layout: { display: 'grid', gridTemplateColumns: '1fr 360px', gap: '2rem', alignItems: 'start' },
  info: {},
  aside: {},
  statusRow: { display: 'flex', gap: 8, marginBottom: 8 },
  opBadge: { background: '#e94560', color: '#fff', borderRadius: 4, padding: '3px 10px', fontSize: 13, fontWeight: 600 },
  statusBadge: { background: '#f0a500', color: '#fff', borderRadius: 4, padding: '3px 10px', fontSize: 13, fontWeight: 600 },
  title: { fontSize: 26, color: '#1a1a2e', margin: '0 0 .5rem' },
  location: { color: '#666', fontSize: 15, margin: '0 0 .75rem' },
  price: { color: '#e94560', fontSize: 28, fontWeight: 700, margin: '0 0 1.5rem' },
  specs: { display: 'flex', gap: '1.5rem', margin: '0 0 1.5rem' },
  spec: { textAlign: 'center', fontSize: 14, color: '#555', lineHeight: 1.4 },
  desc: { margin: '0 0 1.5rem' },
  descH: { fontSize: 16, color: '#1a1a2e', marginBottom: '.5rem' },
  descText: { color: '#444', lineHeight: 1.7 },
}
