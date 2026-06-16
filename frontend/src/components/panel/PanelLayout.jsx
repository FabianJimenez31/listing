import { useEffect, useState } from 'react'
import { Link, NavLink, Navigate, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import Spinner from '../ui/Spinner'
import {
  IconHome, IconPlus, IconBuilding, IconInbox, IconGrid, IconCheckCircle,
  IconStar, IconOffice, IconUsers, IconFile, IconImage, IconUserCog,
  IconLogout, IconExternal, IconMenu,
} from '../admin/adminIcons'

// The sidebar is a single shell for the whole back-office. Sections are
// added by capability, so a regular agent only sees "Mi trabajo" while an
// admin additionally sees "Administración" — no duplicated layout.
function buildNav({ hasPermission, isAdmin }) {
  const nav = [{
    section: 'Mi trabajo',
    items: [
      { to: '/agente', end: true, label: 'Mis propiedades', icon: IconHome },
      { to: '/agente/nueva', label: 'Nueva propiedad', icon: IconPlus },
      ...(hasPermission('project:create') ? [{ to: '/agente/proyectos', label: 'Proyectos', icon: IconBuilding }] : []),
      { to: '/agente/leads', label: 'Leads', icon: IconInbox },
    ],
  }]

  if (isAdmin()) {
    nav.push({
      section: 'Administración',
      items: [
        { to: '/admin', end: true, label: 'Dashboard', icon: IconGrid },
        { to: '/admin/moderacion', label: 'Por aprobar', icon: IconCheckCircle },
        { to: '/admin/destacados', label: 'Destacados', icon: IconStar },
        { to: '/admin/inmobiliarias', label: 'Inmobiliarias', icon: IconOffice },
        { to: '/admin/aliados', label: 'Aliados', icon: IconUsers },
        { to: '/admin/blog', label: 'Blog', icon: IconFile },
        { to: '/admin/banners', label: 'Banners', icon: IconImage },
        { to: '/admin/usuarios', label: 'Usuarios', icon: IconUserCog },
      ],
    })
  }
  return nav
}

export default function PanelLayout() {
  const { user, loading, isAdmin, hasPermission, logout } = useAuth()
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const [open, setOpen] = useState(false)

  useEffect(() => { setOpen(false) }, [pathname])

  if (loading) return <div className="admin-boot"><Spinner /></div>
  if (!user) return <Navigate to="/login" replace />
  // Admin-only area: a non-admin gets bounced back to their workspace.
  if (pathname.startsWith('/admin') && !isAdmin()) return <Navigate to="/agente" replace />

  const nav = buildNav({ hasPermission, isAdmin })
  const flat = nav.flatMap((g) => g.items)
  const current = flat.find((i) => (i.end ? pathname === i.to : pathname.startsWith(i.to)))
  const title = current?.label || (pathname.startsWith('/admin') ? 'Administración' : 'Panel')
  const initial = (user.full_name || user.email || '?').trim().charAt(0).toUpperCase()

  const handleLogout = async () => { await logout(); navigate('/') }

  return (
    <div className="admin-shell">
      <div className={`admin-scrim ${open ? 'show' : ''}`} onClick={() => setOpen(false)} />

      <aside className={`admin-sidebar ${open ? 'open' : ''}`}>
        <Link to="/agente" className="admin-brand">
          <span className="dot">P</span>
          <span className="bt"><b>Proppietario</b><small>Panel</small></span>
        </Link>

        <nav className="admin-nav">
          {nav.map((group) => (
            <div className="admin-nav-group" key={group.section}>
              <p className="admin-nav-label">{group.section}</p>
              {group.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) => `admin-nav-link ${isActive ? 'active' : ''}`}
                >
                  <item.icon size={19} />
                  {item.label}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        <div className="admin-sidebar-foot">
          <div className="admin-user">
            <span className="avatar">{initial}</span>
            <span className="meta">
              <b>{user.full_name || 'Usuario'}</b>
              <span>{user.email}</span>
            </span>
          </div>
          <button className="admin-logout" onClick={handleLogout}>
            <IconLogout size={16} /> Cerrar sesión
          </button>
        </div>
      </aside>

      <div className="admin-main">
        <header className="admin-topbar">
          <button className="admin-burger" aria-label="Abrir menú" onClick={() => setOpen((o) => !o)}>
            <IconMenu size={20} />
          </button>
          <h2>{title}</h2>
          <span className="spacer" />
          <Link to="/" className="admin-portal-link">
            <IconExternal size={15} /> Ver portal
          </Link>
        </header>

        <main className="admin-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
