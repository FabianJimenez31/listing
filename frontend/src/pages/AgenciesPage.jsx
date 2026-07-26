import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { getAgencies } from '../api/agencies'
import Spinner from '../components/ui/Spinner'

export default function AgenciesPage() {
  const [items, setItems] = useState(null)

  useEffect(() => {
    getAgencies().then(setItems).catch(() => setItems([]))
  }, [])

  return (
    <div className="page-wrap">
      <Helmet>
        <title>Inmobiliarias | Proppia</title>
        <meta name="description" content="Inmobiliarias y agencias aliadas de Proppia en Colombia y Estados Unidos." />
      </Helmet>

      <div className="sec-head" style={{ marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: 28 }}>Inmobiliarias</h2>
          <p>Nuestras agencias e inmobiliarias aliadas</p>
        </div>
      </div>

      {items === null ? (
        <Spinner />
      ) : items.length === 0 ? (
        <p style={{ color: 'var(--muted)' }}>Aún no hay inmobiliarias registradas.</p>
      ) : (
        <div className="agency-grid">
          {items.map((a) => (
            <Link key={a.id} className="agency-card" to={`/inmobiliarias/${a.slug}`}>
              <span className="lg">{a.initials || a.name.slice(0, 2).toUpperCase()}</span>
              <div>
                <div className="nm">{a.name}</div>
                <div className="meta">
                  {a.property_count} propiedad{a.property_count !== 1 ? 'es' : ''}
                  {a.is_verified ? ' · Verificada' : ''}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
