import { Link } from 'react-router-dom'
import PropertyCard from '../property/PropertyCard'
import { IconArrow } from '../ui/icons'

export default function FeaturedListings({ items = [], loading }) {
  return (
    <section className="section">
      <div className="wrap">
        <div className="sec-head">
          <div>
            <h2>Propiedades destacadas</h2>
            <p>Selección curada con el mejor potencial de valorización</p>
          </div>
          <Link className="seelink" to="/propiedades">Ver todas <IconArrow /></Link>
        </div>

        <div className="grid-list">
          {loading
            ? Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="skeleton" style={{ height: 380 }} />
              ))
            : items.map((p) => <PropertyCard key={p.id} property={p} showShare />)}
        </div>
        {!loading && items.length === 0 && (
          <p style={{ color: 'var(--muted)' }}>Aún no hay propiedades destacadas.</p>
        )}
      </div>
    </section>
  )
}
