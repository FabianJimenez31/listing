import { useState } from 'react'
import { createLead } from '../../api/leads'

export default function LeadForm({ propertyId }) {
  const [form, setForm] = useState({ name: '', email: '', phone: '', message: '', channel: 'form', consent_given: false })
  const [status, setStatus] = useState(null)

  const update = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const submit = async (e) => {
    e.preventDefault()
    setStatus('sending')
    try {
      await createLead({ ...form, property_id: propertyId, consent_text: 'Acepto el aviso de privacidad' })
      setStatus('ok')
    } catch (err) {
      setStatus('error')
    }
  }

  if (status === 'ok') {
    return <div style={styles.success}>¡Mensaje enviado! Un asesor te contactará pronto.</div>
  }

  return (
    <form onSubmit={submit} style={styles.form}>
      <h3 style={styles.heading}>¿Te interesa esta propiedad?</h3>

      <input required style={styles.input} placeholder="Nombre *" value={form.name} onChange={(e) => update('name', e.target.value)} />
      <input style={styles.input} placeholder="Correo" type="email" value={form.email} onChange={(e) => update('email', e.target.value)} />
      <input style={styles.input} placeholder="Teléfono / WhatsApp" value={form.phone} onChange={(e) => update('phone', e.target.value)} />
      <textarea style={{ ...styles.input, height: 80, resize: 'vertical' }} placeholder="Mensaje (opcional)" value={form.message} onChange={(e) => update('message', e.target.value)} />

      <label style={styles.checkLabel}>
        <input type="checkbox" checked={form.consent_given} onChange={(e) => update('consent_given', e.target.checked)} />
        {' '}Acepto el aviso de privacidad *
      </label>

      {status === 'error' && <p style={styles.error}>Error al enviar. Intenta de nuevo.</p>}

      <button type="submit" disabled={status === 'sending'} style={styles.btn}>
        {status === 'sending' ? 'Enviando…' : 'Enviar mensaje'}
      </button>

      <div style={styles.ctaRow}>
        <a href={`https://wa.me/?text=Me interesa la propiedad ${propertyId}`} target="_blank" rel="noopener noreferrer" style={styles.waBadge}>
          WhatsApp
        </a>
      </div>
    </form>
  )
}

const styles = {
  form: { background: '#fff', borderRadius: 10, padding: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,.07)' },
  heading: { margin: '0 0 1rem', fontSize: 16, color: '#1a1a2e' },
  input: { display: 'block', width: '100%', padding: '8px 10px', border: '1px solid #ddd', borderRadius: 6, fontSize: 14, marginBottom: 10, boxSizing: 'border-box' },
  checkLabel: { display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#555', marginBottom: 12 },
  btn: { width: '100%', background: '#e94560', color: '#fff', border: 'none', borderRadius: 6, padding: 10, cursor: 'pointer', fontWeight: 600, fontSize: 15 },
  success: { background: '#e6f9ed', color: '#2d6a4f', padding: '1rem', borderRadius: 8, textAlign: 'center', fontWeight: 500 },
  error: { color: '#e94560', fontSize: 13, margin: '0 0 8px' },
  ctaRow: { marginTop: '1rem', display: 'flex', gap: 8 },
  waBadge: { flex: 1, background: '#25d366', color: '#fff', borderRadius: 6, padding: '8px 0', textAlign: 'center', textDecoration: 'none', fontWeight: 600 },
}
