import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { getProject } from '../api/projects'
import Spinner from '../components/ui/Spinner'
import { formatPrice } from '../components/property/PropertyCard'
import ImageCarousel from '../components/ui/ImageCarousel'
import { IconPin } from '../components/ui/icons'

const STAGE = { preventa: 'Preventa', construccion: 'En construcción', entrega_inmediata: 'Entrega inmediata' }

const range = (a, b) => (a == null ? '—' : b && b !== a ? `${a}–${b}` : `${a}`)

export default function ProjectDetailPage() {
  const { slug } = useParams()
  const [project, setProject] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    setLoading(true)
    setError(false)
    getProject(slug).then(setProject).catch(() => setError(true)).finally(() => setLoading(false))
  }, [slug])

  if (loading) return <div className="page-wrap"><Spinner /></div>
  if (error || !project) {
    return (
      <div className="page-wrap">
        <p>Proyecto no encontrado.</p>
        <Link to="/proyectos" className="seelink">← Volver a proyectos</Link>
      </div>
    )
  }

  const images = project.images?.length
    ? project.images
    : project.cover_image_url
      ? [{ id: 'cover', cdn_url: project.cover_image_url }]
      : []
  const from = formatPrice(project.price_from, project.currency)
  const to = formatPrice(project.price_to, project.currency)
  const phone = project.contact_phone || project.agency?.phone
  const wa = (project.contact_whatsapp || project.agency?.whatsapp || '').replace(/[^0-9]/g, '')

  const specs = [
    ['Etapa', STAGE[project.stage] || 'Proyecto'],
    ['Habitaciones', range(project.bedrooms_min, project.bedrooms_max)],
    ['Baños', range(project.bathrooms_min, project.bathrooms_max)],
    ['Área (m²)', range(project.area_min_m2, project.area_max_m2)],
    ['Unidades', project.total_units ?? '—'],
  ]

  return (
    <div className="page-wrap">
      <Helmet><title>{project.title} | Proppietario</title></Helmet>
      <div className="crumbs">
        <Link to="/proyectos">Proyectos</Link>{project.location?.name ? ` · ${project.location.name}` : ''}
      </div>

      <div className="pdp-hero">
        <div className="badges">
          {project.currency === 'USD' && <span className="badge usa">USA</span>}
          <span className="badge proyecto">{STAGE[project.stage] || 'Proyecto'}</span>
        </div>
        <ImageCarousel images={images} alt={project.title} />
      </div>

      <div className="detail-cols">
        <div>
          <span className="badge proyecto" style={{ display: 'inline-block' }}>{STAGE[project.stage] || 'Proyecto'}</span>
          <h1 style={{ fontSize: 30, fontWeight: 800, color: 'var(--ink)', margin: '12px 0 6px' }}>{project.title}</h1>
          {project.location?.name && <div className="loc" style={{ fontSize: 15 }}><IconPin /> {project.location.name}</div>}
          <div className="spec-grid">
            {specs.map(([k, v]) => <div className="sp" key={k}><div className="k">{k}</div><div className="v">{v}</div></div>)}
          </div>
          {project.description && (
            <>
              <h3 style={{ fontWeight: 800, color: 'var(--ink)', margin: '10px 0' }}>Descripción</h3>
              <div className="prose"><p>{project.description}</p></div>
            </>
          )}
        </div>
        <aside>
          <div style={{ position: 'sticky', top: 90, background: '#fff', border: '1px solid var(--line)', borderRadius: 16, padding: 22, boxShadow: 'var(--shadow-sm)' }}>
            <div style={{ fontSize: 13, color: 'var(--muted)' }}>Precios desde</div>
            <div style={{ fontSize: 26, fontWeight: 800, color: 'var(--ink)' }}>{from || 'Consultar'}</div>
            {to && <div style={{ fontSize: 13, color: 'var(--muted)' }}>hasta {to}</div>}
            {project.developer_name && (
              <div style={{ marginTop: 14, fontSize: 14, color: 'var(--muted)' }}>
                Desarrolla<br /><b style={{ color: 'var(--ink)' }}>{project.developer_name}</b>
              </div>
            )}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 18 }}>
              {wa && <a className="btn btn-blue" style={{ justifyContent: 'center' }} href={`https://wa.me/${wa}`} target="_blank" rel="noreferrer">WhatsApp</a>}
              {phone && <a className="btn btn-outline" style={{ justifyContent: 'center' }} href={`tel:${phone}`}>Llamar</a>}
              {project.agency && <Link className="btn btn-outline" style={{ justifyContent: 'center' }} to={`/inmobiliarias/${project.agency.slug}`}>Ver inmobiliaria</Link>}
            </div>
          </div>
        </aside>
      </div>
    </div>
  )
}
