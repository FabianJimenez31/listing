import { useEffect, useState } from 'react'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../../contexts/AuthContext'
import { getAdminUsers } from '../../api/admin'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import Spinner from '../../components/ui/Spinner'
import Pagination from '../../components/ui/Pagination'

export default function UsersPage() {
  const { user } = useAuth()
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')

  const load = (p = page) => {
    setLoading(true)
    getAdminUsers({ page: p, page_size: 20 })
      .then(setResult)
      .catch(() => null)
      .finally(() => setLoading(false))
  }

  useEffect(() => { if (user) load() }, [user, page])

  const handlePage = (p) => { setPage(p); load(p) }

  if (loading) return <Spinner />

  const users = result?.data || []
  const filtered = search
    ? users.filter((u) => u.email.includes(search) || u.full_name?.toLowerCase().includes(search.toLowerCase()))
    : users

  return (
    <>
      <Helmet><title>Usuarios | Listing Admin</title></Helmet>

      <AdminPageHeader
        title="Usuarios"
        subtitle="Cuentas registradas en la plataforma"
        count={result?.meta?.total ?? 0}
      />

      <input
        className="adm-input adm-search"
        placeholder="Buscar por email o nombre…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      <div className="adm-table">
        <div className="adm-thead">
          <span className="col3">Email</span>
          <span className="col2">Nombre</span>
          <span className="col1">Estado</span>
          <span className="col2">Registro</span>
        </div>
        {filtered.length === 0 ? (
          <div className="adm-row"><span style={{ color: 'var(--muted)' }}>Sin resultados</span></div>
        ) : filtered.map((u) => (
          <div key={u.id} className="adm-row">
            <span className="col3 mono">{u.email}</span>
            <span className="col2">{u.full_name || '—'}</span>
            <span className="col1">
              <span className={`tag ${u.is_active ? 'green' : ''}`}>{u.is_active ? 'Activo' : 'Inactivo'}</span>
            </span>
            <span className="col2" style={{ color: 'var(--muted)', fontSize: 13 }}>
              {u.created_at ? new Date(u.created_at).toLocaleDateString('es-CO') : '—'}
            </span>
          </div>
        ))}
      </div>

      <Pagination meta={result?.meta} onPage={handlePage} />
    </>
  )
}
