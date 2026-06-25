import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../contexts/AuthContext'

export default function LoginPage() {
  const { login, verifyOtp } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '' })
  const [step, setStep] = useState('email') // 'email' | 'password' | 'otp'
  const [challengeId, setChallengeId] = useState(null)
  const [code, setCode] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const errMsg = (err, fallback) =>
    err.response?.data?.error?.message || err.response?.data?.detail || fallback

  const goByRole = (user) =>
    navigate(user.permissions?.includes('property:moderate') ? '/admin' : '/agente')

  // Step 1: email only. Staff get a code; everyone else is asked for a password.
  const submitEmail = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const res = await login(form.email, null)
      if (res.otpRequired) {
        setChallengeId(res.challengeId)
        setStep('otp')
      } else if (res.passwordRequired) {
        setStep('password')
      } else if (res.user) {
        goByRole(res.user)
      }
    } catch (err) {
      setError(errMsg(err, 'No encontramos esa cuenta'))
    } finally {
      setLoading(false)
    }
  }

  const submitPassword = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const res = await login(form.email, form.password)
      if (res.otpRequired) {
        setChallengeId(res.challengeId)
        setStep('otp')
      } else if (res.user) {
        goByRole(res.user)
      }
    } catch (err) {
      setError(errMsg(err, 'Contraseña incorrecta'))
    } finally {
      setLoading(false)
    }
  }

  const verify = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      goByRole(await verifyOtp(challengeId, code.trim()))
    } catch (err) {
      setError(errMsg(err, 'Código inválido o expirado'))
    } finally {
      setLoading(false)
    }
  }

  const back = () => {
    setStep('email')
    setCode('')
    setForm((f) => ({ ...f, password: '' }))
    setError(null)
  }

  const title = step === 'otp' ? 'Verifica tu identidad'
    : step === 'password' ? 'Ingresa tu contraseña'
    : 'Iniciar sesión'

  return (
    <div className="page-wrap">
      <Helmet><title>Iniciar sesión | Proppietario</title></Helmet>
      <div style={s.wrap}>
        <div style={s.card}>
          <div style={s.logoMark}>P</div>
          <h1 style={s.h1}>{title}</h1>

          {error && <p style={s.error}>{error}</p>}

          {step === 'email' && (
            <form onSubmit={submitEmail}>
              <label style={s.label}>Correo electrónico</label>
              <input
                required
                type="email"
                autoFocus
                style={s.input}
                value={form.email}
                onChange={e => setForm({ ...form, email: e.target.value })}
              />
              <button type="submit" disabled={loading} style={s.btn}>
                {loading ? 'Continuando…' : 'Continuar'}
              </button>
              <p style={s.foot}>¿No tienes cuenta? <Link to="/registro" style={s.link}>Regístrate</Link></p>
            </form>
          )}

          {step === 'password' && (
            <form onSubmit={submitPassword}>
              <p style={s.hint}>Cuenta: <b>{form.email}</b></p>
              <label style={s.label}>Contraseña</label>
              <input
                required
                type="password"
                autoFocus
                style={s.input}
                value={form.password}
                onChange={e => setForm({ ...form, password: e.target.value })}
              />
              <button type="submit" disabled={loading} style={s.btn}>
                {loading ? 'Entrando…' : 'Entrar'}
              </button>
              <button type="button" onClick={back} style={s.linkBtn}>← Volver</button>
            </form>
          )}

          {step === 'otp' && (
            <form onSubmit={verify}>
              <p style={s.hint}>Enviamos un código de 6 dígitos a <b>{form.email}</b>. Ingrésalo para entrar.</p>
              <label style={s.label}>Código de verificación</label>
              <input
                required
                inputMode="numeric"
                autoComplete="one-time-code"
                autoFocus
                maxLength={6}
                placeholder="••••••"
                style={{ ...s.input, letterSpacing: 6, textAlign: 'center', fontSize: 20 }}
                value={code}
                onChange={e => setCode(e.target.value.replace(/\D/g, ''))}
              />
              <button type="submit" disabled={loading || code.length < 6} style={s.btn}>
                {loading ? 'Verificando…' : 'Verificar y entrar'}
              </button>
              <button type="button" onClick={back} style={s.linkBtn}>← Volver</button>
            </form>
          )}
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
  hint: { fontSize: 14, color: '#4A5680', marginBottom: 8, lineHeight: 1.5 },
  linkBtn: {
    display: 'block',
    width: '100%',
    background: 'none',
    border: 'none',
    color: '#0251FD',
    fontSize: 14,
    fontWeight: 600,
    cursor: 'pointer',
    marginTop: 14,
    fontFamily: "'Montserrat', sans-serif",
  },
}
