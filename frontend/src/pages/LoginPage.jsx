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
    <div className="page-wrap">
      <Helmet><title>Iniciar sesión | Proppietario</title></Helmet>
      <div style={s.wrap}>
        <div style={s.card}>
          <div style={s.logoMark}>P</div>
          <h1 style={s.h1}>Iniciar sesión</h1>

          {error && <p style={s.error}>{error}</p>}

          <form onSubmit={submit}>
            <label style={s.label}>Correo electrónico</label>
            <input
              required
              type="email"
              style={s.input}
              value={form.email}
              onChange={e => setForm({ ...form, email: e.target.value })}
            />
            <label style={s.label}>Contraseña</label>
            <input
              required
              type="password"
              style={s.input}
              value={form.password}
              onChange={e => setForm({ ...form, password: e.target.value })}
            />
            <button type="submit" disabled={loading} style={s.btn}>
              {loading ? 'Entrando…' : 'Entrar'}
            </button>
          </form>

          <p style={s.foot}>¿No tienes cuenta? <Link to="/registro" style={s.link}>Regístrate</Link></p>
        </div>
      </div>
    </div>
  )
}

const s = {
  wrap: { display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' },
  card: {
    background: '#fff',
    borderRadius: 24,
    padding: '2.5rem',
    boxShadow: '0 8px 24px rgba(8,29,103,0.08)',
    border: '1px solid #DDE8FF',
    width: '100%',
    maxWidth: 420,
  },
  logoMark: {
    width: 48,
    height: 48,
    background: 'linear-gradient(135deg, #081D67, #0251FD)',
    borderRadius: 14,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontFamily: "'Montserrat', sans-serif",
    fontWeight: 800,
    fontSize: 24,
    color: '#fff',
    margin: '0 auto 1.5rem',
  },
  h1: {
    fontSize: 22,
    fontFamily: "'Montserrat', sans-serif",
    fontWeight: 700,
    color: '#081D67',
    marginBottom: '1.5rem',
    textAlign: 'center',
  },
  label: { display: 'block', fontSize: 13, fontWeight: 600, color: '#4A5680', marginBottom: 4, marginTop: 12 },
  input: {
    display: 'block',
    width: '100%',
    padding: '10px 12px',
    border: '1px solid #DDE8FF',
    borderRadius: 8,
    fontSize: 15,
    boxSizing: 'border-box',
    color: '#081D67',
    outline: 'none',
  },
  btn: {
    display: 'block',
    width: '100%',
    background: '#0251FD',
    color: '#fff',
    border: 'none',
    borderRadius: 12,
    padding: '13px',
    fontSize: 15,
    fontWeight: 700,
    cursor: 'pointer',
    marginTop: '1.5rem',
    fontFamily: "'Montserrat', sans-serif",
  },
  error: {
    background: '#fef2f2',
    color: '#D7263D',
    borderRadius: 8,
    padding: '10px 12px',
    fontSize: 14,
    marginBottom: 12,
  },
  foot: { textAlign: 'center', fontSize: 14, color: '#4A5680', marginTop: '1.25rem' },
  link: { color: '#0251FD', fontWeight: 600 },
}
