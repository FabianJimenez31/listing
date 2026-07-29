import { Link } from 'react-router-dom'
import { MORTGAGE_WHATSAPP_DISPLAY, MORTGAGE_WHATSAPP_LINK } from '../../config/mortgage'
import { IconWhatsapp } from '../ui/icons'

const I = { fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round', strokeLinejoin: 'round' }

const POINTS = [
  {
    icon: <svg width="22" height="22" viewBox="0 0 24 24" {...I}><path d="M3 10.5 12 4l9 6.5V20a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z" /><path d="M9 21v-6h6v6" /></svg>,
    title: 'Hasta el 70% del inmueble',
    text: 'Vivienda nueva, usada o leasing habitacional, en Colombia.',
  },
  {
    icon: <svg width="22" height="22" viewBox="0 0 24 24" {...I}><path d="M3 3v18h18" /><path d="m7 15 4-4 3 3 5-6" /></svg>,
    title: 'Comparamos tasas',
    text: 'Revisamos las opciones de varios bancos y te mostramos la mejor.',
  },
  {
    icon: <svg width="22" height="22" viewBox="0 0 24 24" {...I}><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>,
    title: 'Respuesta el mismo día',
    text: 'Un asesor te escribe por WhatsApp con el resultado del estudio.',
  },
]

export default function MortgageSection() {
  return (
    <section className="section mtg-promo">
      <div className="wrap">
        <div className="mtg-promo-copy">
          <span className="mtg-kicker">Crédito hipotecario</span>
          <h2>Financia tu próxima propiedad con acompañamiento real</h2>
          <p className="lead">
            Completa el formulario y te contactamos por WhatsApp con cuánto te pueden prestar,
            a qué tasa y con qué banco. El estudio no tiene costo.
          </p>
          <div className="mtg-promo-actions">
            <Link className="btn btn-blue" to="/credito-hipotecario">Solicitar mi crédito</Link>
            <a
              className="btn btn-outline"
              href={MORTGAGE_WHATSAPP_LINK('Hola, quiero información sobre crédito hipotecario.')}
              target="_blank"
              rel="noopener noreferrer"
            >
              <IconWhatsapp /> {MORTGAGE_WHATSAPP_DISPLAY}
            </a>
          </div>
        </div>
        <div className="mtg-promo-points">
          {POINTS.map((p) => (
            <div className="mtg-point" key={p.title}>
              <span className="pi">{p.icon}</span>
              <div>
                <h4>{p.title}</h4>
                <p>{p.text}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
