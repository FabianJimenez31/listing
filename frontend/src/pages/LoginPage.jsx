import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../contexts/AuthContext'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const user = await login(form.email, form.password)
      navigate(user.permissions?.includes('property:moderate') ? '/admin' : '/agente')
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Credenciales incorrectas')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Helmet><title>Iniciar sesión | Listing</title></Helmet>
      <div style={styles.wrap}>
        <div style={styles.card}>
          <h1 style={styles.h1}>Iniciar sesión</h1>

          {error && <p style={styles.error}>{error}</p>}

          <form onSubmit={submit}>
            <label style={styles.label}>Correo</label>
            <input required type="email" style={styles.input} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            <label style={styles.label}>Contraseña</label>
            <input required type="password" style={styles.input} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
            <button type="submit" disabled={loading} style={styles.btn}>
              {loading ? 'Entrando…' : 'Entrar'}
            </button>
          </form>

          <p style={styles.foot}>¿No tienes cuenta? <Link to="/registro" style={styles.link}>Regístrate</Link></p>
        </div>
      </div>
    </>
  )
}

const styles = {
  wrap: { display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' },
  card: { background: '#fff', borderRadius: 12, padding: '2.5rem', boxShadow: '0 4px 20px rgba(0,0,0,.1)', width: '100%', maxWidth: 420 },
  h1: { fontSize: 22, color: '#1a1a2e', marginBottom: '1.5rem', textAlign: 'center' },
  label: { display: 'block', fontSize: 13, color: '#555', marginBottom: 4, marginTop: 12 },
  input: { display: 'block', width: '100%', padding: '10px 12px', border: '1px solid #ddd', borderRadius: 6, fontSize: 15, boxSizing: 'border-box' },
  btn: { display: 'block', width: '100%', background: '#e94560', color: '#fff', border: 'none', borderRadius: 6, padding: '12px', fontSize: 15, fontWeight: 600, cursor: 'pointer', marginTop: '1.5rem' },
  error: { background: '#fef2f2', color: '#b91c1c', borderRadius: 6, padding: '10px 12px', fontSize: 14, marginBottom: 12 },
  foot: { textAlign: 'center', fontSize: 14, color: '#666', marginTop: '1.25rem' },
  link: { color: '#e94560' },
}
