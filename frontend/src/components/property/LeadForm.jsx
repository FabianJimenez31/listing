import { useState } from 'react'
import { createLead } from '../../api/leads'
import { IconCheck } from '../ui/icons'

export default function LeadForm({ propertyId }) {
  const [form, setForm] = useState({
    name: '', email: '', phone: '', message: '',
    channel: 'form', consent_given: false,
  })
  const [status, setStatus] = useState(null)

  const update = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const submit = async (e) => {
    e.preventDefault()
    setStatus('sending')
    try {
      await createLead({ ...form, property_id: propertyId, consent_text: 'Acepto el aviso de privacidad' })
      setStatus('ok')
    } catch {
      setStatus('error')
    }
  }

  if (status === 'ok') {
    return (
      <div className="lead-ok"><IconCheck /> ¡Mensaje enviado! Un asesor te contactará pronto.</div>
    )
  }

  return (
    <form onSubmit={submit} className="lead-form">
      <h3>¿Te interesa esta propiedad?</h3>
      <input required placeholder="Nombre *" value={form.name} onChange={(e) => update('name', e.target.value)} />
      <input placeholder="Correo" type="email" value={form.email} onChange={(e) => update('email', e.target.value)} />
      <input placeholder="Teléfono / WhatsApp" value={form.phone} onChange={(e) => update('phone', e.target.value)} />
      <textarea style={{ height: 84, resize: 'vertical' }} placeholder="Mensaje (opcional)" value={form.message} onChange={(e) => update('message', e.target.value)} />
      <label className="consent">
        <input type="checkbox" required style={{ width: 'auto', margin: 0 }} checked={form.consent_given} onChange={(e) => update('consent_given', e.target.checked)} />
        Acepto el aviso de privacidad *
      </label>
      {status === 'error' && <p style={{ color: '#D7263D', fontSize: 13, marginBottom: 8 }}>Error al enviar. Intenta de nuevo.</p>}
      <button type="submit" disabled={status === 'sending'} className="btn btn-blue" style={{ width: '100%', justifyContent: 'center' }}>
        {status === 'sending' ? 'Enviando…' : 'Enviar mensaje'}
      </button>
    </form>
  )
}
