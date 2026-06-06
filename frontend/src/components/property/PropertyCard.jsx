import { Link } from 'react-router-dom'

const OPERATION_LABEL = { sale: 'Venta', rent: 'Renta', temporary: 'Temporal' }
const KIND_LABEL = { house: 'Casa', apartment: 'Apartamento', lot: 'Terreno', office: 'Oficina' }

function formatPrice(amount, currency = 'MXN') {
  if (!amount) return 'Precio a consultar'
  return new Intl.NumberFormat('es-MX', { style: 'currency', currency, maximumFractionDigits: 0 }).format(amount / 100)
}

export default function PropertyCard({ property }) {
  const mainImage = property.images?.find((i) => i.role === 'main') || property.images?.[0]

  return (
    <Link to={`/propiedades/${property.slug}`} style={{ textDecoration: 'none', color: 'inherit' }}>
      <div style={styles.card}>
        <div style={styles.imgWrapper}>
          {mainImage ? (
            <img src={mainImage.cdn_url} alt={mainImage.alt_text || property.title} style={styles.img} loading="lazy" />
          ) : (
            <div style={styles.noImg}>Sin foto</div>
          )}
          <span style={styles.opBadge}>{OPERATION_LABEL[property.operation_type] || property.operation_type}</span>
        </div>
        <div style={styles.body}>
          <p style={styles.kind}>{KIND_LABEL[property.property_kind] || property.property_kind}</p>
          <h3 style={styles.title}>{property.title}</h3>
          {property.location && (
            <p style={styles.location}>{property.location.name}</p>
          )}
          <p style={styles.price}>{formatPrice(property.price_amount, property.currency)}</p>
          <div style={styles.stats}>
            {property.bedrooms != null && <span>{property.bedrooms} rec.</span>}
            {property.bathrooms != null && <span>{property.bathrooms} baños</span>}
            {property.total_area_m2 != null && <span>{property.total_area_m2} m²</span>}
          </div>
        </div>
      </div>
    </Link>
  )
}

const styles = {
  card: { background: '#fff', borderRadius: 10, overflow: 'hidden', boxShadow: '0 2px 8px rgba(0,0,0,.07)', transition: 'transform .2s', cursor: 'pointer' },
  imgWrapper: { position: 'relative', height: 200 },
  img: { width: '100%', height: '100%', objectFit: 'cover' },
  noImg: { width: '100%', height: '100%', background: '#eee', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#aaa' },
  opBadge: { position: 'absolute', top: 10, left: 10, background: '#e94560', color: '#fff', borderRadius: 4, padding: '2px 8px', fontSize: 12, fontWeight: 600 },
  body: { padding: '1rem' },
  kind: { color: '#888', fontSize: 12, margin: '0 0 4px' },
  title: { fontSize: 16, fontWeight: 600, margin: '0 0 4px', color: '#1a1a2e' },
  location: { color: '#666', fontSize: 13, margin: '0 0 8px' },
  price: { color: '#e94560', fontWeight: 700, fontSize: 18, margin: '0 0 8px' },
  stats: { display: 'flex', gap: 12, fontSize: 13, color: '#555' },
}
