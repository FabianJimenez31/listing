import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../../contexts/AuthContext'
import { approveProject, deleteProject, searchProjects, submitProject } from '../../api/projects'
import { formatPrice } from '../../components/property/PropertyCard'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import { IconBuilding } from '../../components/admin/adminIcons'
import Spinner from '../../components/ui/Spinner'

const STATUS_TAG = {
  draft: ['Borrador', 'amber'],
  pending: ['Pendiente', 'amber'],
  published: ['Publicado', 'green'],
  paused: ['Pausado', ''],
  deleted: ['Eliminado', ''],
}

export default function AgentProjectsPage() {
  const { user, isAdmin } = useAuth()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    searchProjects({ status: 'all', page_size: 50 })
      .then((r) => setItems(r.data || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => { if (user) load() }, [user])

  const act = async (fn, id) => { await fn(id).catch(() => null); load() }
  const remove = async (id) => { if (!confirm('¿Eliminar proyecto?')) return; await deleteProject(id).catch(() => null); load() }

  if (loading) return <Spinner />

  return (
    <>
      <Helmet><title>Proyectos | Proppietario</title></Helmet>

      <AdminPageHeader
        title="Proyectos"
        subtitle="Desarrollos y proyectos inmobiliarios"
        count={items.length}
        actions={<Link className="btn btn-blue" to="/agente/proyectos/nuevo">+ Nuevo proyecto</Link>}
      />

      {items.length === 0 ? (
        <div className="adm-empty">
          <span className="ico"><IconBuilding size={26} /></span>
          <b>Sin proyectos</b>
          Crea el primero con "+ Nuevo proyecto".
        </div>
      ) : (
        <div className="adm-table">
          {items.map((p) => {
            const [label, cls] = STATUS_TAG[p.status] || [p.status, '']
            return (
              <div className="adm-row" key={p.id}>
                <div className="grow">
                  <div className="name">{p.title}</div>
                  <div className="sub">{p.stage} · {p.location?.name || 'Sin ubicación'} · {formatPrice(p.price_from, p.currency) || 'Sin precio'}</div>
                </div>
                <span className={`tag ${cls}`}>{label}</span>
                <Link className="btn btn-outline btn-sm" to={`/agente/proyectos/editar/${p.slug}`}>Editar</Link>
                {p.status === 'draft' && <button className="btn btn-outline btn-sm" onClick={() => act(submitProject, p.id)}>Enviar</button>}
                {isAdmin() && p.status === 'pending' && <button className="btn btn-blue btn-sm" onClick={() => act(approveProject, p.id)}>Aprobar</button>}
                {isAdmin() && p.status === 'draft' && <button className="btn btn-blue btn-sm" onClick={() => act(approveProject, p.id)}>Publicar</button>}
                <button className="btn btn-outline btn-sm btn-danger" onClick={() => remove(p.id)}>Eliminar</button>
              </div>
            )
          })}
        </div>
      )}
    </>
  )
}
