import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../../contexts/AuthContext'
import { searchProperties, deleteProperty, submitProperty, pauseProperty, reactivateProperty } from '../../api/properties'
import Spinner from '../../components/ui/Spinner'
import Pagination from '../../components/ui/Pagination'

const STATUS_COLOR = {
  draft: '#4A5680',
  pending: '#b45309',
  published: '#15803d',
  paused: '#0251FD',
  rejected: '#D7263D',
  sold: '#081D67',
  rented: '#081D67',
  deleted: '#DDE8FF',
}

const STATUS_BG = {
  draft: '#F4F6FB',
  pending: '#FEF3C7',
  published: '#DCFCE7',
  paused: '#EEF4FF',
  rejected: '#FEE2E2',
  sold: '#E8EDF5',
  rented: '#E8EDF5',
  deleted: '#F4F6FB',
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

  if (authLoading || loading) return <div className="page-wrap"><Spinner /></div>

  const props = result?.data || []

  return (
    <div className="page-wrap">
      <Helmet><title>Mi panel | Proppietario</title></Helmet>

      <div style={s.header}>
        <h1 style={s.h1}>Mis propiedades</h1>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <Link to="/agente/proyectos" style={{ ...s.newBtn, background: '#F4F6FB', color: '#0251FD' }}>Proyectos</Link>
          <Link to="/agente/nueva" style={s.newBtn}>+ Nueva propiedad</Link>
        </div>
      </div>

      {props.length === 0 ? (
        <div style={s.empty}>
          <p style={{ marginBottom: '1rem', color: '#4A5680' }}>No tienes propiedades aún.</p>
          <Link to="/agente/nueva" style={s.link}>Publicar mi primera propiedad</Link>
        </div>
      ) : (
        <>
          <div style={s.table}>
            <div style={s.tableHeader}>
              <span style={s.col4}>Título</span>
              <span style={s.col2}>Estado</span>
              <span style={s.col2}>Precio</span>
              <span style={s.col4}>Acciones</span>
            </div>
            {props.map(p => (
              <div key={p.id} style={s.row}>
                <span style={{ ...s.col4, fontWeight: 500, color: '#081D67' }}>{p.title}</span>
                <span style={s.col2}>
                  <span style={{
                    ...s.statusChip,
                    color: STATUS_COLOR[p.status] || '#4A5680',
                    background: STATUS_BG[p.status] || '#F4F6FB',
                  }}>
                    {p.status}
                  </span>
                </span>
                <span style={{ ...s.col2, color: '#4A5680', fontSize: 13 }}>
                  {p.price_amount ? `${(p.price_amount / 100).toLocaleString()} ${p.currency}` : '—'}
                </span>
                <span style={{ ...s.col4, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  <Link to={`/agente/editar/${p.id}`} style={s.actBtn}>Editar</Link>
                  {p.status === 'draft' && <button style={s.actBtn} onClick={() => action(submitProperty, p.id)}>Enviar</button>}
                  {p.status === 'published' && <button style={s.actBtn} onClick={() => action(pauseProperty, p.id)}>Pausar</button>}
                  {p.status === 'paused' && <button style={s.actBtnPrimary} onClick={() => action(reactivateProperty, p.id)}>Reactivar</button>}
                  <Link to={`/agente/leads?property_id=${p.id}`} style={s.actBtn}>Leads</Link>
                </span>
              </div>
            ))}
          </div>
          <Pagination meta={result?.meta} onPage={setPage} />
        </>
      )}
    </div>
  )
}

const s = {
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.75rem', flexWrap: 'wrap', gap: '1rem' },
  h1: { fontFamily: "'Montserrat', sans-serif", fontWeight: 800, fontSize: 24, color: '#081D67', margin: 0 },
  newBtn: {
    background: '#0251FD', color: '#fff', borderRadius: 12,
    padding: '10px 20px', textDecoration: 'none', fontWeight: 700,
    fontFamily: "'Montserrat', sans-serif", fontSize: 14,
  },
  table: { background: '#fff', borderRadius: 16, overflow: 'hidden', border: '1px solid #DDE8FF', boxShadow: '0 8px 24px rgba(8,29,103,0.06)' },
  tableHeader: {
    display: 'flex', padding: '12px 16px',
    background: '#F4F6FB', borderBottom: '1px solid #DDE8FF',
    fontWeight: 700, fontSize: 12, color: '#4A5680',
    textTransform: 'uppercase', letterSpacing: '0.05em',
    fontFamily: "'Montserrat', sans-serif",
  },
  row: { display: 'flex', padding: '14px 16px', borderBottom: '1px solid #F4F6FB', alignItems: 'center', fontSize: 14 },
  col4: { flex: 4, paddingRight: 8 },
  col2: { flex: 2, paddingRight: 8 },
  statusChip: { borderRadius: 999, padding: '3px 10px', fontSize: 12, fontWeight: 700 },
  actBtn: {
    background: '#F4F6FB', color: '#4A5680',
    border: '1px solid #DDE8FF', borderRadius: 8,
    padding: '5px 12px', fontSize: 12, cursor: 'pointer',
    textDecoration: 'none', fontWeight: 600,
  },
  actBtnPrimary: {
    background: '#0251FD', color: '#fff',
    border: 'none', borderRadius: 8,
    padding: '5px 12px', fontSize: 12, cursor: 'pointer',
    fontWeight: 700,
  },
  empty: {
    background: '#F4F6FB', borderRadius: 16, padding: '3rem',
    textAlign: 'center', border: '1px solid #DDE8FF',
  },
  link: { color: '#0251FD', fontWeight: 700, textDecoration: 'none' },
}
