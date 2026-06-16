import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../../contexts/AuthContext'
import { getAdminStats } from '../../api/admin'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import Spinner from '../../components/ui/Spinner'
import {
  IconCheckCircle, IconClock, IconUsers, IconTrend, IconInbox,
  IconStar, IconBuilding, IconOffice, IconFile, IconImage, IconUserCog,
} from '../../components/admin/adminIcons'

const StatCard = ({ label, value, icon: Icon, tone, to }) => (
  <Link to={to} className="stat-card">
    <span className={`stat-ico ${tone}`}><Icon size={24} /></span>
    <span>
      <span className="stat-val">{value ?? '—'}</span>
      <span className="stat-label">{label}</span>
    </span>
  </Link>
)

const QUICK = [
  { to: '/admin/moderacion', label: 'Por aprobar', icon: IconInbox },
  { to: '/admin/destacados', label: 'Destacados', icon: IconStar },
  { to: '/agente/proyectos', label: 'Proyectos', icon: IconBuilding },
  { to: '/admin/inmobiliarias', label: 'Inmobiliarias', icon: IconOffice },
  { to: '/admin/aliados', label: 'Aliados', icon: IconUsers },
  { to: '/admin/blog', label: 'Blog', icon: IconFile },
  { to: '/admin/banners', label: 'Banners', icon: IconImage },
  { to: '/admin/usuarios', label: 'Usuarios', icon: IconUserCog },
]

export default function AdminDashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) return
    getAdminStats().then(setStats).catch(() => null).finally(() => setLoading(false))
  }, [user])

  if (loading) return <Spinner />

  return (
    <>
      <Helmet><title>Dashboard | Listing Admin</title></Helmet>

      <AdminPageHeader title="Dashboard" subtitle="Resumen general de la plataforma" />

      <div className="admin-stats">
        <StatCard label="Publicadas" value={stats?.published_properties} icon={IconCheckCircle} tone="green" to="/admin/moderacion" />
        <StatCard label="Pendientes" value={stats?.pending_properties} icon={IconClock} tone="amber" to="/admin/moderacion" />
        <StatCard label="Usuarios" value={stats?.total_users} icon={IconUsers} tone="blue" to="/admin/usuarios" />
        <StatCard label="Leads" value={stats?.total_leads} icon={IconTrend} tone="violet" to="/agente/leads" />
      </div>

      <p className="admin-section-title">Acciones rápidas</p>
      <div className="admin-quick">
        {QUICK.map((q) => (
          <Link key={q.to} to={q.to} className="quick-card">
            <span className="q-ico"><q.icon size={20} /></span>
            {q.label}
          </Link>
        ))}
      </div>
    </>
  )
}
