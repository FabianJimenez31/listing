import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../../contexts/AuthContext'
import { getLeads, updateLead } from '../../api/leads'
import Spinner from '../../components/ui/Spinner'

const STATUS_OPTIONS = ['new', 'contacted', 'visit_scheduled', 'closed_won', 'closed_lost']
const STATUS_COLOR = { new: '#e94560', contacted: '#f0a500', visit_scheduled: '#2980b9', closed_won: '#2d6a4f', closed_lost: '#888' }
const CHANNEL_LABEL = { form: 'Formulario', whatsapp: 'WhatsApp', call: 'Llamada', visit: 'Visita' }

export default function LeadsPage() {
  const { user, loading: authLoading } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const propertyId = searchParams.get('property_id')
  const [leads, setLeads] = useState([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    getLeads(propertyId ? { property_id: propertyId } : {})
      .then((r) => setLeads(r.data || []))
      .catch(() => null)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (!authLoading && !user) { navigate('/login'); return }
    if (user) load()
  }, [user, authLoading])

  const changeStatus = async (leadId, status) => {
    await updateLead(leadId, { status }).catch(() => null)
    load()
  }

  if (authLoading || loading) return <Spinner />

  return (
    <>
      <Helmet><title>Leads | Listing</title></Helmet>
      <div style={styles.header}>
        <button onClick={() => navigate('/agente')} style={styles.back}>← Volver</button>
        <h1 style={styles.h1}>Leads {propertyId ? `— Propiedad ${propertyId.slice(0, 8)}…` : 'totales'}</h1>
      </div>

      {leads.length === 0 ? (
        <p style={styles.empty}>No hay leads registrados.</p>
      ) : (
        <div style={styles.table}>
          {leads.map((lead) => (
            <div key={lead.id} style={styles.row}>
              <div style={styles.leadInfo}>
                <strong>{lead.name}</strong>
                <span style={{ color: '#666', marginLeft: 8, fontSize: 13 }}>{lead.email || lead.phone}</span>
                <span style={{ ...styles.channelBadge, background: '#f0f0f0' }}>{CHANNEL_LABEL[lead.channel] || lead.channel}</span>
              </div>
              <span style={{ color: STATUS_COLOR[lead.status], fontWeight: 600, fontSize: 13 }}>{lead.status}</span>
              <select
                value={lead.status}
                onChange={(e) => changeStatus(lead.id, e.target.value)}
                style={styles.statusSelect}
              >
                {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
              <span style={{ fontSize: 12, color: '#aaa' }}>{new Date(lead.created_at).toLocaleDateString('es-CO')}</span>
            </div>
          ))}
        </div>
      )}
    </>
  )
}

const styles = {
  header: { display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' },
  back: { background: 'none', border: 'none', color: '#e94560', cursor: 'pointer', fontSize: 14 },
  h1: { fontSize: 22, color: '#1a1a2e', margin: 0 },
  table: { background: '#fff', borderRadius: 10, overflow: 'hidden', boxShadow: '0 2px 8px rgba(0,0,0,.07)' },
  row: { display: 'flex', alignItems: 'center', gap: '1rem', padding: '12px 16px', borderBottom: '1px solid #f0f0f0', fontSize: 14 },
  leadInfo: { flex: 1 },
  channelBadge: { display: 'inline-block', borderRadius: 4, padding: '2px 8px', fontSize: 12, marginLeft: 8 },
  statusSelect: { padding: '4px 8px', border: '1px solid #ddd', borderRadius: 4, fontSize: 13 },
  empty: { color: '#888', textAlign: 'center', background: '#fff', borderRadius: 10, padding: '2rem' },
}
