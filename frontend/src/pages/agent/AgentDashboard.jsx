import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../../contexts/AuthContext'
import { searchProperties, submitProperty, pauseProperty, reactivateProperty } from '../../api/properties'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import { IconHome } from '../../components/admin/adminIcons'
import Spinner from '../../components/ui/Spinner'
import Pagination from '../../components/ui/Pagination'

const STATUS = {
  draft: ['Borrador', 'amber'],
  pending: ['Pendiente', 'amber'],
  published: ['Publicado', 'green'],
  paused: ['Pausado', ''],
  rejected: ['Rechazado', 'amber'],
  sold: ['Vendido', ''],
  rented: ['Arrendado', ''],
  deleted: ['Eliminado', ''],
}

export default function AgentDashboard() {
  const { user } = useAuth()
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [query, setQuery] = useState('')        // what's typed in the box
  const [search, setSearch] = useState('')       // committed search term

  const loadProperties = () => {
    setLoading(true)
    const params = { owner_id: user?.id, page, page_size: 10, include_own: true }
    const term = search.trim()
    if (term) {
      // A pure number is treated as a Record ID (NID); anything else as text.
      if (/^\d+$/.test(term)) params.nid = Number(term)
      else params.q = term
    }
    searchProperties(params)
      .then(setResult)
      .catch(() => null)
      .finally(() => setLoading(false))
  }

  useEffect(() => { if (user) loadProperties() }, [user, page, search])

  const action = async (fn, id) => { await fn(id); loadProperties() }

  const onSearch = (e) => { e.preventDefault(); setPage(1); setSearch(query) }
  const clearSearch = () => { setQuery(''); setPage(1); setSearch('') }

  if (loading) return <Spinner />

  const props = result?.data || []

  return (
    <>
      <Helmet><title>Mis propiedades | Proppietario</title></Helmet>

      <AdminPageHeader
        title="Mis propiedades"
        subtitle="Gestiona tus publicaciones"
        count={result?.meta?.total ?? props.length}
        actions={<Link to="/agente/nueva" className="btn btn-blue">+ Nueva propiedad</Link>}
      />

      <form onSubmit={onSearch} className="adm-search" style={{ display: 'flex', gap: 8, margin: '0 0 16px', flexWrap: 'wrap' }}>
        <input
          className="adm-input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Buscar por ID (ej. 1000000001) o título…"
          inputMode="search"
          style={{ flex: '1 1 260px', minWidth: 0 }}
        />
        <button type="submit" className="btn btn-blue btn-sm">Buscar</button>
        {search && <button type="button" className="btn btn-outline btn-sm" onClick={clearSearch}>Limpiar</button>}
      </form>

      {props.length === 0 ? (
        <div className="adm-empty">
          <span className="ico"><IconHome size={26} /></span>
          {search ? (
            <>
              <b>Sin resultados para «{search}»</b>
              <button type="button" className="btn btn-outline btn-sm" onClick={clearSearch}>Ver todas</button>
            </>
          ) : (
            <>
              <b>Aún no tienes propiedades</b>
              <Link to="/agente/nueva" style={{ color: 'var(--blue)', fontWeight: 700 }}>Publicar mi primera propiedad</Link>
            </>
          )}
        </div>
      ) : (
        <>
          <div className="adm-table">
            <div className="adm-thead">
              <span className="col4">Título</span>
              <span className="col2">Estado</span>
              <span className="col2">Precio</span>
              <span className="col4">Acciones</span>
            </div>
            {props.map((p) => {
              const [label, cls] = STATUS[p.status] || [p.status, '']
              return (
                <div key={p.id} className="adm-row">
                  <span className="col4 name">
                    {p.title}
                    <small style={{ display: 'block', color: 'var(--muted)', fontWeight: 500, fontSize: 12 }}>ID {p.nid}</small>
                  </span>
                  <span className="col2"><span className={`tag ${cls}`}>{label}</span></span>
                  <span className="col2" style={{ color: 'var(--muted)', fontSize: 13 }}>
                    {p.price_amount ? `${(p.price_amount / 100).toLocaleString()} ${p.currency}` : '—'}
                  </span>
                  <span className="col4" style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    <Link to={`/agente/editar/${p.id}`} className="btn btn-outline btn-sm">Editar</Link>
                    {p.status === 'draft' && <button className="btn btn-outline btn-sm" onClick={() => action(submitProperty, p.id)}>Enviar</button>}
                    {p.status === 'published' && <button className="btn btn-outline btn-sm" onClick={() => action(pauseProperty, p.id)}>Pausar</button>}
                    {p.status === 'paused' && <button className="btn btn-blue btn-sm" onClick={() => action(reactivateProperty, p.id)}>Reactivar</button>}
                    <Link to={`/agente/leads?property_id=${p.id}`} className="btn btn-outline btn-sm">Leads</Link>
                  </span>
                </div>
              )
            })}
          </div>
          <Pagination meta={result?.meta} onPage={setPage} />
        </>
      )}
    </>
  )
}
