import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { searchProjects } from '../api/projects'
import ProjectCard from '../components/property/ProjectCard'
import Pagination from '../components/ui/Pagination'
import Spinner from '../components/ui/Spinner'

const STAGES = [
  ['', 'Todos'],
  ['preventa', 'Preventa'],
  ['construccion', 'En construcción'],
  ['entrega_inmediata', 'Entrega inmediata'],
]

export default function ProjectsPage() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)

  const query = Object.fromEntries(params.entries())
  const key = JSON.stringify(query)
  const activeStage = query.stage || ''

  useEffect(() => {
    setLoading(true)
    searchProjects({ page_size: 12, ...query })
      .then(setResult)
      .catch(() => setResult({ data: [], meta: { total: 0, total_pages: 1, page: 1 } }))
      .finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])

  const setStage = (s) => {
    const p = new URLSearchParams(params)
    if (s) p.set('stage', s)
    else p.delete('stage')
    p.set('page', '1')
    navigate(`/proyectos?${p}`)
  }

  const handlePage = (page) => {
    const p = new URLSearchParams(params)
    p.set('page', page)
    navigate(`/proyectos?${p}`)
  }

  return (
    <div className="page-wrap">
      <Helmet>
        <title>Proyectos | Proppietario</title>
        <meta name="description" content="Proyectos inmobiliarios en preventa y sobre planos en Colombia y Estados Unidos." />
      </Helmet>

      <div className="sec-head" style={{ marginBottom: 18 }}>
        <div>
          <h2 style={{ fontSize: 28 }}>Proyectos</h2>
          <p>Desarrollos en preventa y sobre planos en Colombia y USA</p>
        </div>
      </div>

      <div className="pill-row">
        {STAGES.map(([v, l]) => (
          <button key={v || 'all'} className={`pill ${activeStage === v ? 'active' : ''}`} onClick={() => setStage(v)}>
            {l}
          </button>
        ))}
      </div>

      {loading ? (
        <Spinner />
      ) : result?.data?.length === 0 ? (
        <div style={{ background: 'var(--bg-soft)', borderRadius: 16, padding: '3rem', textAlign: 'center', color: 'var(--muted)', border: '1px solid var(--line)' }}>
          No hay proyectos con estos filtros.
        </div>
      ) : (
        <>
          <div className="grid-list">
            {result.data.map((p) => <ProjectCard key={p.id} project={p} />)}
          </div>
          <Pagination meta={result.meta} onPage={handlePage} />
        </>
      )}
    </div>
  )
}
