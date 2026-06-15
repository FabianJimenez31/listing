import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../../contexts/AuthContext'
import { approveProject, deleteProject, searchProjects, submitProject } from '../../api/projects'
import { formatPrice } from '../../components/property/PropertyCard'
import Spinner from '../../components/ui/Spinner'

const STATUS_TAG = {
  draft: ['Borrador', 'amber'],
  pending: ['Pendiente', 'amber'],
  published: ['Publicado', 'green'],
  paused: ['Pausado', ''],
  deleted: ['Eliminado', ''],
}

export default function AgentProjectsPage() {
  const { user, loading: authLoading, isAdmin } = useAuth()
  const navigate = useNavigate()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    searchProjects({ status: 'all', page_size: 50 })
      .then((r) => setItems(r.data || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (!authLoading) {
      if (!user) { navigate('/login'); return }
      if (!user.permissions?.includes('project:create')) { navigate('/agente'); return }
    }
    if (user) load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, authLoading])

  const act = async (fn, id) => { await fn(id).catch(() => null); load() }
  const remove = async (id) => { if (!confirm('¿Eliminar proyecto?')) return; await deleteProject(id).catch(() => null); load() }

  if (authLoading || loading) return <div className="page-wrap"><Spinner /></div>

  return (
    <div className="page-wrap">
      <Helmet><title>Proyectos | Panel</title></Helmet>
      <div className="admin-head">
        <button className="admin-back" onClick={() => navigate('/agente')}>← Panel</button>
        <h1>Proyectos ({items.length})</h1>
        <Link className="btn btn-blue" to="/agente/proyectos/nuevo">+ Nuevo proyecto</Link>
      </div>

      {items.length === 0 ? (
        <p style={{ color: 'var(--muted)' }}>No hay proyectos. Crea el primero.</p>
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
    </div>
  )
}
