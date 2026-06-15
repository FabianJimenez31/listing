import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { IconLogin } from '../ui/icons'

const NAV = [
  { label: 'Proyectos', to: '/proyectos' },
  { label: 'Venta', to: '/propiedades?operation_type=sale' },
  { label: 'Arriendo', to: '/propiedades?operation_type=rent' },
  { label: 'Mercado USA', to: '/usa' },
  { label: 'Inmobiliarias', to: '/inmobiliarias' },
  { label: 'Blog', to: '/blog' },
]

const mobileLink = { padding: '11px 0', fontWeight: 600, color: 'var(--text)' }

export default function Header() {
  const { user, logout, hasPermission } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)

  const close = () => setOpen(false)
  const handleLogout = async () => {
    await logout()
    close()
    navigate('/')
  }

  return (
    <header className="site-header">
      <div className="wrap nav">
        <Link to="/" className="logo" onClick={close}>
          <span className="dot">P</span>Propp<b>ietario</b>
        </Link>

        <nav className="nav-links">
          {NAV.map((n) => (
            <Link key={n.label} to={n.to}>{n.label}</Link>
          ))}
        </nav>

        <div className="nav-right">
          {user ? (
            <>
              <Link className="publish" to="/favoritos">Favoritos</Link>
              <Link className="publish" to="/agente">Panel</Link>
              {hasPermission('property:moderate') && (
                <Link className="publish" to="/admin">Admin</Link>
              )}
              <button className="btn btn-outline" onClick={handleLogout}>Salir</button>
            </>
          ) : (
            <>
              <Link className="publish" to="/agente/nueva">Publica tu propiedad</Link>
              <Link className="btn btn-blue" to="/login"><IconLogin /> Ingresar</Link>
            </>
          )}
        </div>

        <button className="nav-burger" aria-label="Abrir menú" onClick={() => setOpen((o) => !o)}>
          ☰
        </button>
      </div>

      {open && (
        <div className="wrap" style={{ paddingBottom: 16 }}>
          <nav style={{ display: 'flex', flexDirection: 'column', borderTop: '1px solid var(--line)', paddingTop: 8 }}>
            {NAV.map((n) => (
              <Link key={n.label} to={n.to} onClick={close} style={mobileLink}>{n.label}</Link>
            ))}
            {user ? (
              <>
                <Link to="/favoritos" onClick={close} style={mobileLink}>Favoritos</Link>
                <Link to="/agente" onClick={close} style={mobileLink}>Panel</Link>
                {hasPermission('property:moderate') && (
                  <Link to="/admin" onClick={close} style={mobileLink}>Admin</Link>
                )}
                <button className="btn btn-outline" onClick={handleLogout} style={{ marginTop: 10, justifyContent: 'center' }}>Salir</button>
              </>
            ) : (
              <Link className="btn btn-blue" to="/login" onClick={close} style={{ marginTop: 10, justifyContent: 'center' }}>
                Ingresar
              </Link>
            )}
          </nav>
        </div>
      )}
    </header>
  )
}
