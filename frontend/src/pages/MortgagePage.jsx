import { useState } from 'react'
import { Helmet } from 'react-helmet-async'
import { MORTGAGE_WHATSAPP_DISPLAY, MORTGAGE_WHATSAPP_LINK } from '../config/mortgage'
import { IconCheck, IconWhatsapp } from '../components/ui/icons'

const EMPTY = {
  name: '', phone: '', email: '', city: '',
  credit_type: 'Compra de vivienda nueva',
  property_value: '', down_payment: '', income: '',
  employment: 'Empleado', term: '20 años',
  notes: '', consent: false,
}

const CREDIT_TYPES = [
  'Compra de vivienda nueva',
  'Compra de vivienda usada',
  'Leasing habitacional',
  'Compra de cartera (traslado de crédito)',
  'Remodelación o construcción',
  'Inversión / inmueble comercial',
]

const EMPLOYMENT = ['Empleado', 'Independiente', 'Pensionado', 'Empresa / persona jurídica']
const TERMS = ['5 años', '10 años', '15 años', '20 años', 'Más de 20 años']

const STEPS = [
  { n: '1', title: 'Cuéntanos tu caso', text: 'Completa el formulario con el valor del inmueble y tus ingresos. Toma dos minutos.' },
  { n: '2', title: 'Te escribimos por WhatsApp', text: 'Un asesor revisa tu perfil y te confirma cuánto te pueden prestar y con qué banco.' },
  { n: '3', title: 'Acompañamos el desembolso', text: 'Radicación, avalúo, estudio de títulos y firma: no te dejamos solo en el trámite.' },
]

const BENEFITS = [
  'Comparamos tasas de varios bancos por ti',
  'Sin costo para ti: el estudio es gratis',
  'Aplica para vivienda nueva, usada y leasing',
  'También para colombianos en el exterior',
]

// Los campos de dinero se guardan como dígitos y se muestran con separador de miles.
const onlyDigits = (value) => (value || '').replace(/\D/g, '')
const formatCOP = (digits) => (digits ? Number(digits).toLocaleString('es-CO') : '')
const money = (digits) => (digits ? `$${formatCOP(digits)}` : 'No indicado')

function buildMessage(form) {
  const value = Number(onlyDigits(form.property_value) || 0)
  const down = Number(onlyDigits(form.down_payment) || 0)
  const toFinance = value > down ? value - down : 0

  const lines = [
    '*Solicitud de crédito hipotecario*',
    '',
    `*Nombre:* ${form.name}`,
    `*Teléfono:* ${form.phone}`,
  ]
  if (form.email) lines.push(`*Correo:* ${form.email}`)
  if (form.city) lines.push(`*Ciudad:* ${form.city}`)
  lines.push(
    `*Tipo de crédito:* ${form.credit_type}`,
    `*Valor del inmueble:* ${money(form.property_value)}`,
    `*Cuota inicial:* ${money(form.down_payment)}`,
  )
  if (toFinance > 0) lines.push(`*Monto a financiar:* $${toFinance.toLocaleString('es-CO')}`)
  lines.push(
    `*Ingresos mensuales:* ${money(form.income)}`,
    `*Tipo de ingreso:* ${form.employment}`,
    `*Plazo deseado:* ${form.term}`,
  )
  if (form.notes) lines.push('', `*Observaciones:* ${form.notes}`)
  lines.push('', 'Autorizo el tratamiento de mis datos personales.')
  if (typeof window !== 'undefined') lines.push(`Enviado desde ${window.location.origin}`)

  return lines.join('\n')
}

export default function MortgagePage() {
  const [form, setForm] = useState(EMPTY)
  const [sentLink, setSentLink] = useState(null)
  const [copied, setCopied] = useState(false)

  const upd = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))
  const updMoney = (k) => (e) => setForm((f) => ({ ...f, [k]: onlyDigits(e.target.value) }))

  const submit = (e) => {
    e.preventDefault()
    const message = buildMessage(form)
    const link = MORTGAGE_WHATSAPP_LINK(message)
    // Llamada síncrona dentro del submit: así el navegador no la bloquea como popup.
    window.open(link, '_blank', 'noopener,noreferrer')
    setSentLink({ link, message })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(sentLink.message)
      setCopied(true)
    } catch {
      setCopied(false)
    }
  }

  const restart = () => { setForm(EMPTY); setSentLink(null); setCopied(false) }

  const valueDigits = Number(onlyDigits(form.property_value) || 0)
  const downDigits = Number(onlyDigits(form.down_payment) || 0)
  const toFinance = valueDigits > downDigits ? valueDigits - downDigits : 0

  return (
    <>
      <Helmet>
        <title>Crédito hipotecario | Proppia</title>
        <meta
          name="description"
          content="Solicita tu crédito hipotecario con Proppia: comparamos tasas de varios bancos y te acompañamos hasta el desembolso. Vivienda nueva, usada y leasing habitacional."
        />
      </Helmet>

      <section className="mtg-hero">
        <div className="wrap">
          <span className="mtg-kicker"><IconWhatsapp size={15} /> Respuesta por WhatsApp</span>
          <h1>Crédito hipotecario sin dar vueltas entre bancos</h1>
          <p>
            Cuéntanos qué inmueble quieres comprar y cuánto ganas. Comparamos las opciones de financiación
            disponibles y te escribimos con la mejor alternativa para tu perfil.
          </p>
          <ul className="mtg-benefits">
            {BENEFITS.map((b) => (
              <li key={b}><IconCheck /> {b}</li>
            ))}
          </ul>
        </div>
      </section>

      <section className="section mtg-body">
        <div className="wrap mtg-cols">
          <div className="mtg-steps">
            <h2>Cómo funciona</h2>
            {STEPS.map((s) => (
              <div className="mtg-step" key={s.n}>
                <span className="sn">{s.n}</span>
                <div>
                  <h4>{s.title}</h4>
                  <p>{s.text}</p>
                </div>
              </div>
            ))}
            <div className="mtg-direct">
              <p>¿Prefieres escribirnos directamente?</p>
              <a
                className="btn btn-wa"
                href={MORTGAGE_WHATSAPP_LINK('Hola, quiero información sobre crédito hipotecario.')}
                target="_blank"
                rel="noopener noreferrer"
              >
                <IconWhatsapp /> {MORTGAGE_WHATSAPP_DISPLAY}
              </a>
            </div>
          </div>

          {sentLink ? (
            <div className="mtg-form mtg-sent">
              <div className="lead-ok"><IconCheck /> ¡Solicitud lista para enviar!</div>
              <p className="mtg-hint" style={{ marginTop: 16 }}>
                Se abrió WhatsApp con tus datos. <b>Solo falta presionar «Enviar»</b> en la conversación con
                {' '}{MORTGAGE_WHATSAPP_DISPLAY}. Si no se abrió, usa el botón de abajo.
              </p>
              <div className="mtg-sent-actions">
                <a className="btn btn-wa" href={sentLink.link} target="_blank" rel="noopener noreferrer">
                  <IconWhatsapp /> Abrir WhatsApp
                </a>
                <button type="button" className="btn btn-outline" onClick={copy}>
                  {copied ? 'Datos copiados' : 'Copiar mis datos'}
                </button>
                <button type="button" className="btn btn-outline" onClick={restart}>Nueva solicitud</button>
              </div>
              <pre className="mtg-preview">{sentLink.message}</pre>
            </div>
          ) : (
            <form className="mtg-form" onSubmit={submit}>
              <h2>Solicita tu estudio de crédito</h2>
              <p className="mtg-hint">Los campos con * son obligatorios. Al enviar, se abre WhatsApp con tus datos listos.</p>

              <div className="mtg-grid">
                <div className="mtg-fg full">
                  <label>Nombre completo *</label>
                  <input required value={form.name} onChange={upd('name')} placeholder="Ana María Rodríguez" />
                </div>
                <div className="mtg-fg">
                  <label>Teléfono / WhatsApp *</label>
                  <input required value={form.phone} onChange={upd('phone')} placeholder="300 123 4567" />
                </div>
                <div className="mtg-fg">
                  <label>Correo electrónico</label>
                  <input type="email" value={form.email} onChange={upd('email')} placeholder="tucorreo@email.com" />
                </div>
                <div className="mtg-fg">
                  <label>Ciudad del inmueble</label>
                  <input value={form.city} onChange={upd('city')} placeholder="Bogotá" />
                </div>
                <div className="mtg-fg">
                  <label>Tipo de crédito</label>
                  <select value={form.credit_type} onChange={upd('credit_type')}>
                    {CREDIT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div className="mtg-fg">
                  <label>Valor del inmueble (COP)</label>
                  <input inputMode="numeric" value={formatCOP(form.property_value)} onChange={updMoney('property_value')} placeholder="450.000.000" />
                </div>
                <div className="mtg-fg">
                  <label>Cuota inicial disponible (COP)</label>
                  <input inputMode="numeric" value={formatCOP(form.down_payment)} onChange={updMoney('down_payment')} placeholder="90.000.000" />
                </div>
                <div className="mtg-fg">
                  <label>Ingresos mensuales (COP)</label>
                  <input inputMode="numeric" value={formatCOP(form.income)} onChange={updMoney('income')} placeholder="8.000.000" />
                </div>
                <div className="mtg-fg">
                  <label>Tipo de ingreso</label>
                  <select value={form.employment} onChange={upd('employment')}>
                    {EMPLOYMENT.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div className="mtg-fg">
                  <label>Plazo deseado</label>
                  <select value={form.term} onChange={upd('term')}>
                    {TERMS.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div className="mtg-fg full">
                  <label>Observaciones (opcional)</label>
                  <textarea rows={3} value={form.notes} onChange={upd('notes')} placeholder="Cuéntanos si ya tienes un inmueble en mira, si estás reportado o cualquier detalle útil." />
                </div>
              </div>

              {toFinance > 0 && (
                <p className="mtg-finance">Monto a financiar: <b>${toFinance.toLocaleString('es-CO')}</b></p>
              )}

              <label className="mtg-consent">
                <input
                  type="checkbox"
                  required
                  checked={form.consent}
                  onChange={(e) => setForm((f) => ({ ...f, consent: e.target.checked }))}
                />
                Autorizo el tratamiento de mis datos personales para ser contactado sobre mi solicitud de crédito. *
              </label>

              <button type="submit" className="btn btn-wa mtg-submit">
                <IconWhatsapp /> Enviar por WhatsApp
              </button>
            </form>
          )}
        </div>
      </section>
    </>
  )
}
