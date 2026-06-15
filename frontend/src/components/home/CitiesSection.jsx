import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getFeaturedCities } from '../../api/catalog'
import { IconArrow } from '../ui/icons'

export default function CitiesSection() {
  const [cities, setCities] = useState([])

  useEffect(() => {
    getFeaturedCities(6).then((data) => setCities(data || [])).catch(() => setCities([]))
  }, [])

  if (cities.length === 0) return null

  return (
    <section className="section cities">
      <div className="wrap">
        <div className="sec-head">
          <div>
            <h2>Explora por ciudad</h2>
            <p>Encuentra oportunidades en los mercados más dinámicos</p>
          </div>
          <Link className="seelink" to="/propiedades">Ver todas las ciudades <IconArrow /></Link>
        </div>
        <div className="grid-cities">
          {cities.map((c, i) => {
            const wide = i === 0 || (cities.length >= 6 && i === cities.length - 1)
            return (
              <Link className={`city ${wide ? 'wide' : ''}`} to={`/propiedades?country=${c.slug}`} key={c.id}>
                {c.image_url && (
                  <img
                    src={c.image_url}
                    alt={c.name}
                    onError={(e) => { e.currentTarget.src = `https://picsum.photos/seed/${c.slug}/800/400` }}
                  />
                )}
                <div className="cc">
                  <div className="n">{c.name}</div>
                  <div className="c">{c.property_count} {c.property_count === 1 ? 'propiedad' : 'propiedades'}</div>
                </div>
              </Link>
            )
          })}
        </div>
      </div>
    </section>
  )
}
