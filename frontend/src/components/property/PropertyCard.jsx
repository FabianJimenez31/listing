import { Link } from 'react-router-dom'
import { IconArea, IconBath, IconBed, IconHeart, IconPhotos, IconPin } from '../ui/icons'

const OPERATION = {
  sale: ['Venta', 'venta'],
  rent: ['Arriendo', 'arriendo'],
  temporary: ['Temporal', 'arriendo'],
}

export function formatPrice(amount, currency = 'COP') {
  if (amount == null) return null
  const locale = currency === 'USD' ? 'en-US' : 'es-CO'
  const formatted = new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(amount / 100)
  // USD already prefixes "$"; keep COP as plain "$" too (Intl gives "US$"/"$")
  return formatted
}

export default function PropertyCard({ property }) {
  const mainImage =
    property.main_image || property.images?.find((i) => i.role === 'main') || property.images?.[0]
  const [opLabel, opClass] = OPERATION[property.operation_type] || ['Venta', 'venta']
  const isUSA = property.currency === 'USD'
  const perMonth = property.operation_type === 'rent' || property.operation_type === 'temporary'
  const price = formatPrice(property.price_amount, property.currency)
  const city = property.location?.name
  const agency = property.agency
  const photoCount = property.images?.length

  return (
    <Link to={`/propiedades/${property.slug}`} className="listing" aria-label={property.title}>
      <div className="photo">
        <div className="badges">
          {isUSA && <span className="badge usa">USA</span>}
          <span className={`badge ${opClass}`}>{opLabel}</span>
        </div>
        <span className="fav" aria-hidden="true"><IconHeart /></span>
        {photoCount ? (
          <span className="count"><IconPhotos /> {photoCount}</span>
        ) : null}
        {mainImage ? (
          <img src={mainImage.cdn_url} alt={mainImage.alt_text || property.title} loading="lazy" />
        ) : (
          <div className="noimg" aria-hidden="true">P</div>
        )}
      </div>
      <div className="body">
        <div className="price">
          {price}
          {perMonth && <small> / mes</small>}
        </div>
        <div className="title">{property.title}</div>
        {city && <div className="loc"><IconPin /> {city}</div>}
        <div className="specs">
          {property.bedrooms != null && <span><IconBed /> {property.bedrooms} hab</span>}
          {property.bathrooms != null && <span><IconBath /> {property.bathrooms} baños</span>}
          {property.total_area_m2 != null && <span><IconArea /> {property.total_area_m2} m²</span>}
        </div>
        {agency && (
          <div className="agency">
            <span className="av">{agency.initials || agency.name?.slice(0, 2).toUpperCase()}</span>
            <span className="an">{agency.name}</span>
          </div>
        )}
      </div>
    </Link>
  )
}
