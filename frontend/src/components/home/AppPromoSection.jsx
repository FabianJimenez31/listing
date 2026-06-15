const I = { fill: 'none', stroke: 'currentColor', strokeWidth: 2, strokeLinecap: 'round', strokeLinejoin: 'round' }

const FEATURES = [
  { icon: <svg width="16" height="16" viewBox="0 0 24 24" {...I}><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9M10 21a2 2 0 0 0 4 0" /></svg>, text: 'Alertas de nuevas propiedades a tu medida' },
  { icon: <svg width="16" height="16" viewBox="0 0 24 24" {...I}><path d="M22 3H2l8 9.5V19l4 2v-8.5z" /></svg>, text: 'Filtros precisos para encontrar más fácil' },
  { icon: <svg width="16" height="16" viewBox="0 0 24 24" {...I}><path d="M12 21s-7-4.5-9.5-9A5 5 0 0 1 12 6a5 5 0 0 1 9.5 6c-2.5 4.5-9.5 9-9.5 9z" /></svg>, text: 'Guarda favoritos y recibe bajadas de precio' },
  { icon: <svg width="16" height="16" viewBox="0 0 24 24" {...I}><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>, text: 'Contacta a tu asesor en tiempo real' },
]

export default function AppPromoSection() {
  return (
    <section className="section app">
      <div className="wrap">
        <div>
          <h2>Tu próxima inversión, a una descarga</h2>
          <p className="lead">Recibe alertas de nuevas oportunidades, guarda favoritos y contacta directamente desde la app de Proppietario.</p>
          <div className="app-feats">
            {FEATURES.map((f) => (
              <div className="app-feat" key={f.text}>
                <span className="fi">{f.icon}</span>{f.text}
              </div>
            ))}
          </div>
          <div className="stores">
            <a className="store" href="#" onClick={(e) => e.preventDefault()}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M3 2.5 13.5 12 3 21.5c-.3-.2-.5-.6-.5-1V3.5c0-.4.2-.8.5-1zM15 13.5l3.7 3.4-4.2 2.4L11.5 16zm0-3L11.5 8l3-1.7 4.2 2.4zm1.8.9 2.6 1.5c.6.4.6 1.2 0 1.6l-2.6 1.5L18.4 12z" /></svg>
              <span><span className="s1">Disponible en</span><span className="s2">Google Play</span></span>
            </a>
            <a className="store" href="#" onClick={(e) => e.preventDefault()}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M16.4 1.6c.1 1-.3 2-1 2.8-.7.8-1.7 1.4-2.7 1.3-.1-1 .4-2 1-2.7.7-.8 1.8-1.3 2.7-1.4zM19.6 17c-.5 1.2-.8 1.7-1.5 2.7-.9 1.4-2.2 3.1-3.8 3.1-1.4 0-1.8-.9-3.7-.9s-2.3.9-3.7.9c-1.6 0-2.8-1.5-3.7-2.9C-1 16.4-1.4 11 .6 8.1 1.9 6.2 4 5 6 5c1.6 0 2.7 1 4 1 1.3 0 2-1 4-1 1.7 0 3.5 1 4.8 2.6-4.2 2.3-3.5 8.2.8 9.4z" /></svg>
              <span><span className="s1">Descárgala en</span><span className="s2">App Store</span></span>
            </a>
          </div>
        </div>
        <div className="phone-wrap">
          <div className="phone">
            <div className="screen">
              <div className="ph-top">Proppietario</div>
              <div className="qr"><div className="qrbox" /></div>
              <div className="ph-cap">Escanea para descargar</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
