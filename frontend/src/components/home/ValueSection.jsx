const I = { fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round', strokeLinejoin: 'round' }

const VALUES = [
  {
    icon: <svg width="24" height="24" viewBox="0 0 24 24" {...I}><path d="M3 3v18h18" /><path d="m7 14 4-4 3 3 5-6" /></svg>,
    title: 'Asesoría con datos',
    text: 'Análisis de mercado y potencial de valorización en cada decisión patrimonial.',
  },
  {
    icon: <svg width="24" height="24" viewBox="0 0 24 24" {...I}><circle cx="12" cy="12" r="9" /><path d="M2 12h20M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" /></svg>,
    title: 'Colombia y USA',
    text: 'Invierte en dólares y pesos con estructura legal y fiscal optimizada.',
  },
  {
    icon: <svg width="24" height="24" viewBox="0 0 24 24" {...I}><path d="M9 12l2 2 4-4" /><path d="M12 3l8 4v5a8 8 0 0 1-8 8 8 8 0 0 1-8-8V7z" /></svg>,
    title: 'Portafolio curado',
    text: 'Cada propiedad pasa por una selección rigurosa antes de llegar a ti.',
  },
  {
    icon: <svg width="24" height="24" viewBox="0 0 24 24" {...I}><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM22 21v-2a4 4 0 0 0-3-3.87" /></svg>,
    title: 'Acompañamiento total',
    text: 'Un asesor dedicado de principio a fin, también en el cierre.',
  },
]

export default function ValueSection() {
  return (
    <section className="section value">
      <div className="wrap">
        <div className="sec-head" style={{ justifyContent: 'center', textAlign: 'center', flexDirection: 'column', alignItems: 'center' }}>
          <div>
            <h2>Por qué Proppietario</h2>
            <p>Un solo asesor que entiende el panorama completo de tu inversión</p>
          </div>
        </div>
        <div className="grid-val">
          {VALUES.map((v) => (
            <div className="val" key={v.title}>
              <div className="vi">{v.icon}</div>
              <h4>{v.title}</h4>
              <p>{v.text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
