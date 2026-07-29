import { useEffect, useState } from 'react'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../../contexts/AuthContext'
import { getModerationQueue } from '../../api/admin'
import { approveProperty, rejectProperty } from '../../api/properties'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import { IconInbox } from '../../components/admin/adminIcons'
import Spinner from '../../components/ui/Spinner'

export default function ModerationPage() {
  const { user } = useAuth()
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

  useEffect(() => { if (user) load() }, [user])

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

  if (loading) return <Spinner />

  return (
    <>
      <Helmet><title>Por aprobar | Listing Admin</title></Helmet>

      <AdminPageHeader
        title="Por aprobar"
        subtitle="Propiedades que esperan tu visto bueno"
        count={items.length}
      />

      {items.length === 0 ? (
        <div className="adm-empty">
          <span className="ico"><IconInbox size={26} /></span>
          <b>Todo al día</b>
          No hay propiedades pendientes de revisión.
        </div>
      ) : items.map((p) => (
        <div key={p.id} className="admin-card" style={{ marginBottom: 14 }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'baseline', flexWrap: 'wrap', marginBottom: 8 }}>
            <strong style={{ fontSize: 16, color: 'var(--ink)', flex: 1, minWidth: 180 }}>{p.title}</strong>
            <span className="tag">{p.operation_type} · {p.property_kind}</span>
            <span style={{ color: 'var(--blue)', fontWeight: 700 }}>
              {p.price_amount ? `${(p.price_amount / 100).toLocaleString()} ${p.currency}` : '—'}
            </span>
          </div>
          {p.description && (
            <p style={{ color: 'var(--muted)', fontSize: 14, margin: '0 0 14px', lineHeight: 1.5 }}>
              {p.description.slice(0, 200)}…
            </p>
          )}
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
            <button onClick={() => approve(p.id)} className="btn btn-green btn-sm">Aprobar</button>
            <input
              className="adm-input"
              style={{ flex: 1, minWidth: 200 }}
              placeholder="Motivo de rechazo"
              value={reason[p.id] || ''}
              onChange={(e) => setReason((prev) => ({ ...prev, [p.id]: e.target.value }))}
            />
            <button onClick={() => reject(p.id)} className="btn btn-outline btn-sm btn-danger">Rechazar</button>
          </div>
        </div>
      ))}
    </>
  )
}
