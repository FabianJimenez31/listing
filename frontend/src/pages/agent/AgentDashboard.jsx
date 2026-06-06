import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../../contexts/AuthContext'
import { searchProperties, deleteProperty, submitProperty, pauseProperty, reactivateProperty } from '../../api/properties'
import Spinner from '../../components/ui/Spinner'
import Pagination from '../../components/ui/Pagination'

const STATUS_COLOR = {
  draft: '#888',
  pending: '#f0a500',
  published: '#2d6a4f',
  paused: '#e94560',
  rejected: '#b91c1c',
  sold: '#1a1a2e',
  rented: '#1a1a2e',
  deleted: '#ccc',
}

export default function AgentDashboard() {
  const { user, loading: authLoading } = useAuth()
  const navigate = useNavigate()
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)

  const loadProperties = () => {
    setLoading(true)
    searchProperties({ owner_id: user?.id, page, page_size: 10, include_own: true })
      .then(setResult)
      .catch(() => null)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (!authLoading && !user) { navigate('/login'); return }
    if (user) loadProperties()
  }, [user, authLoading, page])

  const action = async (fn, id) => {
    await fn(id)
    loadProperties()
  }

  if (authLoading || loading) return <Spinner />

  const props = result?.data || []

  return (
    <>
      <Helmet><title>Mi panel | Listing</title></Helmet>

      <div style={styles.header}>
        <h1 style={styles.h1}>Mis propiedades</h1>
        <Link to="/agente/nueva" style={styles.newBtn}>+ Nueva propiedad</Link>
      </div>

      {props.length === 0 ? (
        <div style={styles.empty}>
          <p>No tienes propiedades aún.</p>
          <Link to="/agente/nueva" style={styles.link}>Publicar mi primera propiedad</Link>
        </div>
      ) : (
        <>
          <div style={styles.table}>
            <div style={styles.tableHeader}>
              <span style={styles.col4}>Título</span>
              <span style={styles.col2}>Estado</span>
              <span style={styles.col2}>Precio</span>
              <span style={styles.col4}>Acciones</span>
            </div>
            {props.map((p) => (
              <div key={p.id} style={styles.row}>
                <span style={{ ...styles.col4, fontWeight: 500 }}>{p.title}</span>
                <span style={{ ...styles.col2, color: STATUS_COLOR[p.status] || '#333', fontWeight: 600, fontSize: 13 }}>{p.status}</span>
                <span style={styles.col2}>{p.price_amount ? `${(p.price_amount/100).toLocaleString()} ${p.currency}` : '—'}</span>
                <span style={{ ...styles.col4, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  <Link to={`/agente/editar/${p.id}`} style={styles.actBtn}>Editar</Link>
                  {p.status === 'draft' && <button style={styles.actBtn} onClick={() => action(submitProperty, p.id)}>Enviar</button>}
                  {p.status === 'published' && <button style={styles.actBtn} onClick={() => action(pauseProperty, p.id)}>Pausar</button>}
                  {p.status === 'paused' && <button style={styles.actBtn} onClick={() => action(reactivateProperty, p.id)}>Reactivar</button>}
                  <Link to={`/agente/leads?property_id=${p.id}`} style={styles.actBtn}>Leads</Link>
                </span>
              </div>
            ))}
          </div>
          <Pagination meta={result?.meta} onPage={setPage} />
        </>
      )}
    </>
  )
}

const styles = {
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' },
  h1: { fontSize: 22, color: '#1a1a2e', margin: 0 },
  newBtn: { background: '#e94560', color: '#fff', borderRadius: 8, padding: '8px 20px', textDecoration: 'none', fontWeight: 600 },
  table: { background: '#fff', borderRadius: 10, overflow: 'hidden', boxShadow: '0 2px 8px rgba(0,0,0,.07)' },
  tableHeader: { display: 'flex', padding: '12px 16px', background: '#f8f8f8', borderBottom: '1px solid #eee', fontWeight: 600, fontSize: 13, color: '#555' },
  row: { display: 'flex', padding: '12px 16px', borderBottom: '1px solid #f0f0f0', alignItems: 'center', fontSize: 14 },
  col4: { flex: 4, paddingRight: 8 },
  col2: { flex: 2, paddingRight: 8 },
  actBtn: { background: '#f0f0f0', color: '#333', border: 'none', borderRadius: 4, padding: '4px 10px', fontSize: 12, cursor: 'pointer', textDecoration: 'none' },
  empty: { background: '#fff', borderRadius: 10, padding: '3rem', textAlign: 'center', color: '#888' },
  link: { color: '#e94560' },
}
