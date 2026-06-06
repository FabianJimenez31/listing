import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../../contexts/AuthContext'
import { getModerationQueue } from '../../api/admin'
import { approveProperty, rejectProperty } from '../../api/properties'
import Spinner from '../../components/ui/Spinner'

export default function ModerationPage() {
  const { user, loading: authLoading, isAdmin } = useAuth()
  const navigate = useNavigate()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [reason, setReason] = useState({})

  const load = () => {
    setLoading(true)
    getModerationQueue({ page_size: 50 })
      .then((r) => setItems(r.data || []))
      .catch(() => null)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (!authLoading) {
      if (!user) { navigate('/login'); return }
      if (!isAdmin()) { navigate('/agente'); return }
    }
    if (user) load()
  }, [user, authLoading])

  const approve = async (id) => {
    await approveProperty(id).catch(() => null)
    load()
  }

  const reject = async (id) => {
    const r = reason[id] || ''
    if (!r.trim()) { alert('Ingresa el motivo de rechazo'); return }
    await rejectProperty(id, r).catch(() => null)
    setReason((prev) => { const n = { ...prev }; delete n[id]; return n })
    load()
  }

  if (authLoading || loading) return <Spinner />

  return (
    <>
      <Helmet><title>Moderación | Listing Admin</title></Helmet>

      <div style={styles.header}>
        <button onClick={() => navigate('/admin')} style={styles.back}>← Admin</button>
        <h1 style={styles.h1}>Cola de moderación ({items.length})</h1>
      </div>

      {items.length === 0 ? (
        <p style={styles.empty}>No hay propiedades pendientes de revisión.</p>
      ) : items.map((p) => (
        <div key={p.id} style={styles.card}>
          <div style={styles.cardHeader}>
            <strong style={styles.title}>{p.title}</strong>
            <span style={styles.op}>{p.operation_type} · {p.property_kind}</span>
            <span style={styles.price}>{p.price_amount ? `${(p.price_amount/100).toLocaleString()} ${p.currency}` : '—'}</span>
          </div>
          {p.description && <p style={styles.desc}>{p.description.slice(0, 200)}…</p>}
          <div style={styles.actions}>
            <button onClick={() => approve(p.id)} style={styles.approveBtn}>Aprobar</button>
            <input
              placeholder="Motivo de rechazo"
              value={reason[p.id] || ''}
              onChange={(e) => setReason((prev) => ({ ...prev, [p.id]: e.target.value }))}
              style={styles.reasonInput}
            />
            <button onClick={() => reject(p.id)} style={styles.rejectBtn}>Rechazar</button>
          </div>
        </div>
      ))}
    </>
  )
}

const styles = {
  header: { display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' },
  back: { background: 'none', border: 'none', color: '#e94560', cursor: 'pointer', fontSize: 14 },
  h1: { fontSize: 22, color: '#1a1a2e', margin: 0 },
  card: { background: '#fff', borderRadius: 10, padding: '1.25rem', marginBottom: '1rem', boxShadow: '0 2px 8px rgba(0,0,0,.07)' },
  cardHeader: { display: 'flex', gap: '1rem', alignItems: 'baseline', marginBottom: 6 },
  title: { fontSize: 16, color: '#1a1a2e', flex: 1 },
  op: { color: '#888', fontSize: 13 },
  price: { color: '#e94560', fontWeight: 600 },
  desc: { color: '#555', fontSize: 14, margin: '0 0 .75rem', lineHeight: 1.5 },
  actions: { display: 'flex', gap: 8, alignItems: 'center' },
  approveBtn: { background: '#2d6a4f', color: '#fff', border: 'none', borderRadius: 6, padding: '7px 18px', cursor: 'pointer', fontWeight: 600 },
  rejectBtn: { background: '#e94560', color: '#fff', border: 'none', borderRadius: 6, padding: '7px 18px', cursor: 'pointer', fontWeight: 600 },
  reasonInput: { flex: 1, padding: '7px 10px', border: '1px solid #ddd', borderRadius: 6, fontSize: 14 },
  empty: { color: '#888', background: '#fff', borderRadius: 10, padding: '2rem', textAlign: 'center' },
}
