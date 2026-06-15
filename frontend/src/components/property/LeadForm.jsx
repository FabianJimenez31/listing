import { useState } from 'react'
import { createLead } from '../../api/leads'

export default function LeadForm({ propertyId }) {
  const [form, setForm] = useState({
    name: '', email: '', phone: '', message: '',
    channel: 'form', consent_given: false,
  })
  const [status, setStatus] = useState(null)

  const update = (k, v) => setForm(f => ({ ...f, [k]: v }))

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
      <div style={s.success}>
        ✓ ¡Mensaje enviado! Un asesor te contactará pronto.
      </div>
    )
  }

  return (
    <form onSubmit={submit} style={s.form}>
      <h3 style={s.heading}>¿Te interesa esta propiedad?</h3>

      <input required style={s.input} placeholder="Nombre *" value={form.name} onChange={e => update('name', e.target.value)} />
      <input style={s.input} placeholder="Correo" type="email" value={form.email} onChange={e => update('email', e.target.value)} />
      <input style={s.input} placeholder="Teléfono / WhatsApp" value={form.phone} onChange={e => update('phone', e.target.value)} />
      <textarea style={{ ...s.input, height: 80, resize: 'vertical' }} placeholder="Mensaje (opcional)" value={form.message} onChange={e => update('message', e.target.value)} />

      <label style={s.checkLabel}>
        <input type="checkbox" checked={form.consent_given} onChange={e => update('consent_given', e.target.checked)} />
        {' '}Acepto el aviso de privacidad *
      </label>

      {status === 'error' && <p style={s.error}>Error al enviar. Intenta de nuevo.</p>}

      <button type="submit" disabled={status === 'sending'} style={s.btn}>
        {status === 'sending' ? 'Enviando…' : 'Enviar mensaje'}
      </button>
    </form>
  )
}

const s = {
  form: {
    background: '#fff',
    borderRadius: 16,
    padding: '1.5rem',
    border: '1px solid #DDE8FF',
    boxShadow: '0 8px 24px rgba(8,29,103,0.06)',
  },
  heading: {
    margin: '0 0 1.25rem',
    fontSize: 16,
    fontFamily: "'Montserrat', sans-serif",
    fontWeight: 700,
    color: '#081D67',
  },
  input: {
    display: 'block',
    width: '100%',
    padding: '10px 12px',
    border: '1px solid #DDE8FF',
    borderRadius: 8,
    fontSize: 14,
    marginBottom: 10,
    boxSizing: 'border-box',
    color: '#081D67',
    outline: 'none',
    transition: 'border-color 150ms',
  },
  checkLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    fontSize: 13,
    color: '#4A5680',
    marginBottom: 12,
  },
  btn: {
    width: '100%',
    background: '#0251FD',
    color: '#fff',
    border: 'none',
    borderRadius: 12,
    padding: '12px',
    cursor: 'pointer',
    fontWeight: 700,
    fontSize: 15,
    fontFamily: "'Montserrat', sans-serif",
    transition: 'background 150ms',
  },
  success: {
    background: '#e6f9ed',
    color: '#2d6a4f',
    padding: '1.25rem',
    borderRadius: 12,
    textAlign: 'center',
    fontWeight: 600,
    fontSize: 15,
  },
  error: {
    color: '#D7263D',
    fontSize: 13,
    margin: '0 0 8px',
  },
}
