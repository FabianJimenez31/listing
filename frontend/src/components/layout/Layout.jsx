import Header from './Header'

export default function Layout({ children }) {
  return (
    <div style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      <Header />
      <main style={{ maxWidth: 1200, margin: '0 auto', padding: '2rem 1.5rem' }}>
        {children}
      </main>
      <footer style={{ background: '#1a1a2e', color: '#999', textAlign: 'center', padding: '1.5rem', fontSize: 14 }}>
        © {new Date().getFullYear()} Listing — Plataforma inmobiliaria
      </footer>
    </div>
  )
}
