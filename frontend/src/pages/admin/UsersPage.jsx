import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../../contexts/AuthContext'
import { getAdminUsers } from '../../api/admin'
import Spinner from '../../components/ui/Spinner'
import Pagination from '../../components/ui/Pagination'

export default function UsersPage() {
  const { user, loading: authLoading, isAdmin } = useAuth()
  const navigate = useNavigate()
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

  useEffect(() => {
    if (!authLoading) {
      if (!user) { navigate('/login'); return }
      if (!isAdmin()) { navigate('/agente'); return }
    }
    if (user) load()
  }, [user, authLoading, page])

  const handlePage = (p) => { setPage(p); load(p) }

  if (authLoading || loading) return <Spinner />

  const users = result?.data || []
  const filtered = search
    ? users.filter((u) => u.email.includes(search) || u.full_name?.toLowerCase().includes(search.toLowerCase()))
    : users

  return (
    <>
      <Helmet><title>Usuarios | Listing Admin</title></Helmet>

      <div style={styles.header}>
        <button onClick={() => navigate('/admin')} style={styles.back}>← Admin</button>
        <h1 style={styles.h1}>Usuarios ({result?.meta?.total ?? 0})</h1>
      </div>

      <input
        style={styles.search}
        placeholder="Buscar por email o nombre…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      <div style={styles.table}>
        <div style={styles.thead}>
          <span style={styles.c3}>Email</span>
          <span style={styles.c2}>Nombre</span>
          <span style={styles.c1}>Estado</span>
          <span style={styles.c2}>Registro</span>
        </div>
        {filtered.length === 0 ? (
          <p style={styles.empty}>Sin resultados</p>
        ) : filtered.map((u) => (
          <div key={u.id} style={styles.row}>
            <span style={{ ...styles.c3, fontFamily: 'monospace', fontSize: 13 }}>{u.email}</span>
            <span style={styles.c2}>{u.full_name || '—'}</span>
            <span style={{ ...styles.c1, color: u.is_active ? '#2d6a4f' : '#888', fontWeight: 600, fontSize: 13 }}>
              {u.is_active ? 'Activo' : 'Inactivo'}
            </span>
            <span style={{ ...styles.c2, color: '#888', fontSize: 13 }}>
              {u.created_at ? new Date(u.created_at).toLocaleDateString('es-CO') : '—'}
            </span>
          </div>
        ))}
      </div>

      <Pagination meta={result?.meta} onPage={handlePage} />
    </>
  )
}

const styles = {
  header: { display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' },
  back: { background: 'none', border: 'none', color: '#e94560', cursor: 'pointer', fontSize: 14 },
  h1: { fontSize: 22, color: '#1a1a2e', margin: 0 },
  search: { display: 'block', width: '100%', maxWidth: 380, padding: '9px 12px', border: '1px solid #ddd', borderRadius: 8, fontSize: 14, marginBottom: '1rem', boxSizing: 'border-box' },
  table: { background: '#fff', borderRadius: 10, overflow: 'hidden', boxShadow: '0 2px 8px rgba(0,0,0,.07)' },
  thead: { display: 'flex', padding: '10px 16px', background: '#f8f8f8', borderBottom: '1px solid #eee', fontWeight: 600, fontSize: 13, color: '#555' },
  row: { display: 'flex', padding: '10px 16px', borderBottom: '1px solid #f5f5f5', fontSize: 14, alignItems: 'center' },
  c3: { flex: 3, paddingRight: 8 },
  c2: { flex: 2, paddingRight: 8 },
  c1: { flex: 1, paddingRight: 8 },
  empty: { padding: '2rem', textAlign: 'center', color: '#888' },
}
