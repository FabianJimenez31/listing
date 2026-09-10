import { useState } from 'react'
import { Link } from 'react-router-dom'
import { trackEvent } from '../../api/admin'
import { formatPrice } from '../../lib/priceDisplay'
import { shareContent } from '../../lib/shareContent'
import { IconArea, IconBath, IconBed, IconHeart, IconPhotos, IconPin, IconShare } from '../ui/icons'

const OPERATION = {
  sale: ['Venta', 'venta'],
  rent: ['Arriendo', 'arriendo'],
  temporary: ['Temporal', 'arriendo'],
}

export default function PropertyCard({ property, showShare = false }) {
  const [copied, setCopied] = useState(false)
  const mainImage =
    property.main_image || property.images?.find((i) => i.role === 'main') || property.images?.[0]
  const [opLabel, opClass] = OPERATION[property.operation_type] || ['Venta', 'venta']
  const isUSA = property.currency === 'USD'
  const perMonth = property.operation_type === 'rent' || property.operation_type === 'temporary'
  const price = formatPrice(property.price_amount, property.currency)
  const city = property.location?.name
  const agency = property.agency
  const photoCount = property.images?.length
  const href = `/propiedades/${property.nid}`

  const handleShare = async () => {
    const result = await shareContent({
      title: property.title,
      url: `${window.location.origin}${href}`,
    })
    if (result === 'copied') {
      setCopied(true)
      setTimeout(() => setCopied(false), 2500)
    }
    if (result !== 'cancelled') trackEvent('share', property.id).catch(() => null)
  }

  const content = (
    <>
      <div className="photo">
        <div className="badges">
          {isUSA && <span className="badge usa">USA</span>}
          <span className={`badge ${opClass}`}>{opLabel}</span>
        </div>
        {!showShare && <span className="fav" aria-hidden="true"><IconHeart /></span>}
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
          {property.total_area_m2 != null && <span><IconArea /> {property.total_area_m2} m²</span>}
          {property.bedrooms != null && <span><IconBed /> {property.bedrooms} hab</span>}
          {property.bathrooms != null && <span><IconBath /> {property.bathrooms} baños</span>}
        </div>
        {agency && (
          <div className="agency">
            <span className="av">{agency.initials || agency.name?.slice(0, 2).toUpperCase()}</span>
            <span className="an">{agency.name}</span>
          </div>
        )}
      </div>
    </>
  )

  if (!showShare) {
    return <Link to={href} className="listing" aria-label={property.title}>{content}</Link>
  }

  return (
    <article className="listing listing-shareable">
      <Link to={href} className="listing-hit" aria-label={`Ver ${property.title}`} />
      {content}
      <button
        type="button"
        className="card-share"
        onClick={handleShare}
        aria-label={copied ? 'Enlace copiado' : `Compartir ${property.title}`}
        title={copied ? 'Enlace copiado' : 'Compartir propiedad'}
      >
        <IconShare />
      </button>
      {copied && <span className="card-share-status" role="status">Enlace copiado</span>}
    </article>
  )
}
