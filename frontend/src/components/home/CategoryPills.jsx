import { Link } from 'react-router-dom'

const I = { fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round', strokeLinejoin: 'round' }

const CASA = <svg width="20" height="20" viewBox="0 0 24 24" {...I}><path d="M3 21h18M5 21V8l7-5 7 5v13M9 21v-6h6v6" /></svg>
const APTO = <svg width="20" height="20" viewBox="0 0 24 24" {...I}><path d="M3 21h18M6 21V4h12v17M9 8h.01M13 8h.01M9 12h.01M13 12h.01M9 16h.01M13 16h.01" /></svg>
const PROY = <svg width="20" height="20" viewBox="0 0 24 24" {...I}><path d="M3 21h18M5 21V7l5-3 5 3v14M15 21V11h4v10M8 9h.01M8 13h.01M8 17h.01" /></svg>
const OFIC = <svg width="20" height="20" viewBox="0 0 24 24" {...I}><rect x="3" y="8" width="18" height="13" rx="2" /><path d="M8 8V5a4 4 0 0 1 8 0v3" /></svg>
const USA = <svg width="20" height="20" viewBox="0 0 24 24" {...I}><circle cx="12" cy="12" r="9" /><path d="M2 12h20M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" /></svg>

const cats = [
  { icon: CASA, label: 'Casas', to: '/propiedades?property_kind=house' },
  { icon: APTO, label: 'Apartamentos', to: '/propiedades?property_kind=apartment' },
  { icon: PROY, label: 'Proyectos nuevos', to: '/proyectos' },
  { icon: OFIC, label: 'Oficinas y locales', to: '/propiedades?property_kind=office' },
  { icon: USA, label: 'Mercado USA', to: '/usa' },
]

export default function CategoryPills() {
  return (
    <div className="wrap">
      <div className="cats">
        {cats.map((c) => (
          <Link className="cat" to={c.to} key={c.label}>
            <span className="ci">{c.icon}</span>
            <span>{c.label}</span>
          </Link>
        ))}
      </div>
    </div>
  )
}
