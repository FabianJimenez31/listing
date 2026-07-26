import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../../contexts/AuthContext'
import { getLeads, updateLead } from '../../api/leads'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import { IconInbox } from '../../components/admin/adminIcons'
import Spinner from '../../components/ui/Spinner'

const STATUS_OPTIONS = ['new', 'contacted', 'visit_scheduled', 'closed_won', 'closed_lost']
const STATUS_TAG = {
  new: 'amber', contacted: 'amber', visit_scheduled: '', closed_won: 'green', closed_lost: '',
}
const CHANNEL_LABEL = { form: 'Formulario', whatsapp: 'WhatsApp', call: 'Llamada', visit: 'Visita' }

export default function LeadsPage() {
  const { user } = useAuth()
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

  useEffect(() => { if (user) load() }, [user])

  const changeStatus = async (leadId, status) => {
    await updateLead(leadId, { status }).catch(() => null)
    load()
  }

  if (loading) return <Spinner />

  return (
    <>
      <Helmet><title>Leads | Proppia</title></Helmet>

      <AdminPageHeader
        title="Leads"
        subtitle={propertyId ? `Filtrados por propiedad ${propertyId.slice(0, 8)}…` : 'Contactos de todas tus propiedades'}
        count={leads.length}
      />

      {leads.length === 0 ? (
        <div className="adm-empty">
          <span className="ico"><IconInbox size={26} /></span>
          <b>Sin leads</b>
          No hay contactos registrados todavía.
        </div>
      ) : (
        <div className="adm-table">
          {leads.map((lead) => (
            <div key={lead.id} className="adm-row">
              <div className="grow">
                <div className="name">{lead.name}</div>
                <div className="sub">{lead.email || lead.phone}</div>
              </div>
              <span className="tag">{CHANNEL_LABEL[lead.channel] || lead.channel}</span>
              <span className={`tag ${STATUS_TAG[lead.status] || ''}`}>{lead.status}</span>
              <select
                className="adm-input"
                style={{ padding: '7px 10px', fontSize: 13 }}
                value={lead.status}
                onChange={(e) => changeStatus(lead.id, e.target.value)}
              >
                {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
              <span style={{ fontSize: 12, color: 'var(--muted-2)' }}>
                {new Date(lead.created_at).toLocaleDateString('es-CO')}
              </span>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
