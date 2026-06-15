import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../../contexts/AuthContext'
import { getAdminStats } from '../../api/admin'
import Spinner from '../../components/ui/Spinner'

export default function AdminDashboard() {
  const { user, loading: authLoading, isAdmin } = useAuth()
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!authLoading) {
      if (!user) { navigate('/login'); return }
      if (!isAdmin()) { navigate('/agente'); return }
    }
    if (user) {
      getAdminStats()
        .then(setStats)
        .catch(() => null)
        .finally(() => setLoading(false))
    }
  }, [user, authLoading])

  if (authLoading || loading) return <Spinner />

  const StatCard = ({ label, value, color = '#1a1a2e', to }) => (
    <Link to={to || '#'} style={{ textDecoration: 'none' }}>
      <div style={styles.statCard}>
        <p style={{ ...styles.statValue, color }}>{value ?? '—'}</p>
        <p style={styles.statLabel}>{label}</p>
      </div>
    </Link>
  )

  return (
    <>
      <Helmet><title>Panel admin | Listing</title></Helmet>

      <h1 style={styles.h1}>Panel de administración</h1>

      <div style={styles.statsGrid}>
        <StatCard label="Publicadas" value={stats?.published_properties} color="#2d6a4f" to="/admin/moderacion" />
        <StatCard label="Pendientes" value={stats?.pending_properties} color="#f0a500" to="/admin/moderacion" />
        <StatCard label="Usuarios" value={stats?.total_users} to="/admin/usuarios" />
        <StatCard label="Leads" value={stats?.total_leads} to="/admin/leads" />
      </div>

      <div style={styles.quickLinks}>
        <h2 style={styles.h2}>Acciones rápidas</h2>
        <div style={styles.linksGrid}>
          <Link to="/admin/moderacion" style={styles.qlink}>Moderación</Link>
          <Link to="/agente/proyectos" style={styles.qlink}>Proyectos</Link>
          <Link to="/admin/inmobiliarias" style={styles.qlink}>Inmobiliarias</Link>
          <Link to="/admin/aliados" style={styles.qlink}>Aliados</Link>
          <Link to="/admin/blog" style={styles.qlink}>Blog</Link>
          <Link to="/admin/banners" style={styles.qlink}>Banners</Link>
          <Link to="/admin/destacados" style={styles.qlink}>Destacados</Link>
          <Link to="/admin/usuarios" style={styles.qlink}>Usuarios</Link>
        </div>
      </div>
    </>
  )
}

const styles = {
  h1: { fontSize: 24, color: '#1a1a2e', marginBottom: '1.5rem' },
  h2: { fontSize: 18, color: '#1a1a2e', margin: '2rem 0 1rem' },
  statsGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(200px,1fr))', gap: '1.25rem', marginBottom: '2rem' },
  statCard: { background: '#fff', borderRadius: 10, padding: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,.07)', textAlign: 'center' },
  statValue: { fontSize: 36, fontWeight: 700, margin: '0 0 .5rem' },
  statLabel: { color: '#888', fontSize: 14, margin: 0 },
  quickLinks: {},
  linksGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(160px,1fr))', gap: '1rem' },
  qlink: { background: '#fff', borderRadius: 8, padding: '1rem', textAlign: 'center', textDecoration: 'none', color: '#1a1a2e', fontWeight: 500, boxShadow: '0 2px 8px rgba(0,0,0,.07)' },
}
