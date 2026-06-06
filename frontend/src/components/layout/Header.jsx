import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'

export default function Header() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/')
  }

  return (
    <header style={styles.header}>
      <div style={styles.inner}>
        <Link to="/" style={styles.logo}>Listing</Link>

        <nav style={styles.nav}>
          <Link to="/propiedades" style={styles.link}>Propiedades</Link>
          {user ? (
            <>
              <Link to="/favoritos" style={styles.link}>♥ Favoritos</Link>
              <Link to="/agente" style={styles.link}>Mi panel</Link>
              {user.permissions?.includes('property:moderate') && (
                <Link to="/admin" style={styles.link}>Admin</Link>
              )}
              <button onClick={handleLogout} style={styles.btn}>Salir</button>
            </>
          ) : (
            <>
              <Link to="/login" style={styles.link}>Iniciar sesión</Link>
              <Link to="/registro" style={{ ...styles.link, ...styles.btnPrimary }}>Registrarse</Link>
            </>
          )}
        </nav>
      </div>
    </header>
  )
}

const styles = {
  header: { background: '#1a1a2e', padding: '0 1.5rem', position: 'sticky', top: 0, zIndex: 100 },
  inner: { maxWidth: 1200, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 60 },
  logo: { color: '#e94560', fontWeight: 700, fontSize: 22, textDecoration: 'none' },
  nav: { display: 'flex', alignItems: 'center', gap: '1.25rem' },
  link: { color: '#ccc', textDecoration: 'none', fontSize: 15 },
  btn: { background: 'transparent', border: '1px solid #e94560', color: '#e94560', borderRadius: 6, padding: '6px 14px', cursor: 'pointer', fontSize: 14 },
  btnPrimary: { background: '#e94560', color: '#fff', borderRadius: 6, padding: '6px 14px' },
}
