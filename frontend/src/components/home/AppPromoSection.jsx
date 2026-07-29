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
        <div className="app-copy">
          <h2>Tu próxima inversión, a una descarga</h2>
          <p className="lead">Recibe alertas de nuevas oportunidades, guarda favoritos y contacta directamente desde la app de Proppia.</p>
          <div className="app-feats">
            {FEATURES.map((f) => (
              <div className="app-feat" key={f.text}>
                <span className="fi">{f.icon}</span>{f.text}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
