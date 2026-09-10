import { Link } from 'react-router-dom'
import { IconArea, IconBed, IconPin } from '../ui/icons'
import { formatPrice } from '../../lib/priceDisplay'

const STAGE = {
  preventa: 'Preventa',
  construccion: 'En construcción',
  entrega_inmediata: 'Entrega inmediata',
}

function range(min, max, suffix = '') {
  if (min == null) return null
  if (max != null && max !== min) return `${min}–${max}${suffix}`
  return `${min}${suffix}`
}

export default function ProjectCard({ project }) {
  const isUSA = project.currency === 'USD'
  const from = formatPrice(project.price_from, project.currency)
  const city = project.location?.name
  const beds = range(project.bedrooms_min, project.bedrooms_max)
  const area = range(project.area_min_m2, project.area_max_m2)

  return (
    <Link to={`/proyectos/${project.slug}`} className="listing" aria-label={project.title}>
      <div className="photo">
        <div className="badges">
          {isUSA && <span className="badge usa">USA</span>}
          <span className="badge proyecto">{STAGE[project.stage] || 'Proyecto'}</span>
        </div>
        {project.cover_image_url ? (
          <img
            src={project.cover_image_url}
            alt={project.title}
            loading="lazy"
            onError={(e) => { e.currentTarget.src = `https://picsum.photos/seed/${project.slug}/800/600` }}
          />
        ) : (
          <div className="noimg" aria-hidden="true">P</div>
        )}
      </div>
      <div className="body">
        <div className="price">{from ? <>Desde {from}</> : 'Consultar precio'}</div>
        <div className="title">{project.title}</div>
        {city && <div className="loc"><IconPin /> {city}</div>}
        <div className="specs">
          {beds && <span><IconBed /> {beds} hab</span>}
          {area && <span><IconArea /> {area} m²</span>}
        </div>
        {project.developer_name && (
          <div className="agency">
            <span className="av">{project.developer_name.slice(0, 2).toUpperCase()}</span>
            <span className="an">{project.developer_name}</span>
          </div>
        )}
      </div>
    </Link>
  )
}
