import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { IconSearch } from '../ui/icons'
import SearchAutocomplete from './SearchAutocomplete'

const TABS = [
  { key: 'sale', label: 'Venta' },
  { key: 'rent', label: 'Arriendo' },
  { key: 'projects', label: 'Proyectos' },
  { key: 'usa', label: 'Mercado USA' },
]

const KINDS = [
  ['', 'Casa, Apartamento…'],
  ['apartment', 'Apartamento'],
  ['house', 'Casa'],
  ['office', 'Oficina'],
  ['commercial', 'Local comercial'],
  ['lot', 'Lote'],
]

const HERO_IMG = 'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1920&q=80'

const QUICK = [
  ['Apartamentos en Bogotá', '/propiedades?location=bogota&property_kind=apartment'],
  ['Casas en Medellín', '/propiedades?location=medellin&property_kind=house'],
  ['Proyectos en Cali', '/proyectos?location=cali'],
  ['Condos en Miami', '/usa?location=miami'],
  ['Oficinas Bogotá', '/propiedades?location=bogota&property_kind=office'],
]

export default function HeroSection() {
  const navigate = useNavigate()
  const [tab, setTab] = useState('sale')
  const [kind, setKind] = useState('')
  const [q, setQ] = useState('')

  const runSearch = () => {
    const params = new URLSearchParams()
    if (q.trim()) params.set('q', q.trim())
    if (kind) params.set('property_kind', kind)
    if (tab === 'sale' || tab === 'rent') {
      params.set('operation_type', tab)
      navigate(`/propiedades?${params}`)
    } else if (tab === 'projects') {
      navigate(`/proyectos?${params}`)
    } else {
      navigate(`/usa?${params}`)
    }
  }

  const submit = (e) => {
    e.preventDefault()
    runSearch()
  }

  return (
    <section className="hero">
      <div className="hero-bg">
        <img
          src={HERO_IMG}
          alt="Edificio residencial moderno"
          onError={(e) => { e.currentTarget.src = 'https://picsum.photos/seed/hero/1600/700' }}
        />
      </div>
      <div className="hero-inner">
        <div className="wrap">
          <h1>Tu patrimonio en <span style={{ color: '#9fc0ff' }}>un solo lugar</span></h1>
          <p className="sub">Venta, arriendo, proyectos en Colombia y Estados Unidos.</p>

          <form className="searchcard" onSubmit={submit}>
            <div className="tabs">
              {TABS.map((t) => (
                <button
                  type="button"
                  key={t.key}
                  className={`tab ${tab === t.key ? 'active' : ''}`}
                  onClick={() => setTab(t.key)}
                >
                  {t.label}
                </button>
              ))}
            </div>
            <div className="searchrow">
              <div className="selectwrap">
                <select value={kind} onChange={(e) => setKind(e.target.value)} aria-label="Tipo de propiedad">
                  {KINDS.map(([value, label]) => (
                    <option key={label} value={value}>{label}</option>
                  ))}
                </select>
              </div>
              <SearchAutocomplete
                value={q}
                onChange={setQ}
                tab={tab}
                kind={kind}
                onSearch={runSearch}
              />
              <button className="searchbtn" type="submit" aria-label="Buscar">
                <IconSearch size={20} />
              </button>
            </div>
            <div className="searchfoot">
              <button type="button" className="chip-link" onClick={() => navigate('/propiedades')}>Búsqueda avanzada</button>
              <button type="button" className="chip-link" onClick={() => navigate('/proyectos')}>Ver proyectos</button>
              <button type="button" className="chip-link" onClick={() => navigate('/usa')}>Mercado USA</button>
            </div>
          </form>

          <div className="hero-quick">
            {QUICK.map(([label, to]) => (
              <Link key={label} to={to}>{label}</Link>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
