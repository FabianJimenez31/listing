import { useEffect, useRef, useState } from 'react'

// Styled replacement for window.prompt() — pide un nombre y lo entrega a
// `onSubmit(value)`. El submit puede lanzar para mostrar el error sin cerrar.
export default function PromptModal({ title, label, placeholder, submitLabel = 'Agregar', onSubmit, onClose }) {
  const [value, setValue] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)
  const inputRef = useRef(null)

  useEffect(() => {
    inputRef.current?.focus()
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'  // lock background scroll while open
    return () => { document.body.style.overflow = prev }
  }, [])

  const submit = async (e) => {
    e?.preventDefault()
    const name = value.trim()
    if (!name || busy) return
    setBusy(true); setErr(null)
    try {
      await onSubmit(name)
      onClose()
    } catch (ex) {
      setErr(ex?.response?.data?.error?.message || ex?.message || 'No se pudo guardar')
      setBusy(false)
    }
  }

  return (
    <div style={s.overlay} onMouseDown={() => !busy && onClose()} role="dialog" aria-modal="true">
      <form style={s.card} onMouseDown={(e) => e.stopPropagation()} onSubmit={submit}>
        <h3 style={s.title}>{title}</h3>
        {label && <label style={s.label}>{label}</label>}
        <input
          ref={inputRef}
          className="pf-input"
          value={value}
          placeholder={placeholder}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Escape' && !busy) onClose() }}
        />
        {err && <p style={s.err}>{err}</p>}
        <div style={s.actions}>
          <button type="button" style={s.btn} onClick={onClose} disabled={busy}>Cancelar</button>
          <button type="submit" style={s.btnPrimary} disabled={busy || !value.trim()}>
            {busy ? 'Guardando…' : submitLabel}
          </button>
        </div>
      </form>
    </div>
  )
}

const s = {
  overlay: { position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(8,29,103,0.45)', backdropFilter: 'saturate(140%) blur(2px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 },
  card: { display: 'flex', flexDirection: 'column', gap: 12, width: 'min(440px, 94vw)', background: '#fff', border: '1px solid #DDE8FF', borderRadius: 16, padding: 24, boxShadow: '0 24px 60px rgba(8,29,103,0.28)' },
  title: { margin: 0, fontSize: 18, fontWeight: 800, color: '#081D67' },
  label: { fontSize: 13, fontWeight: 600, color: '#6B7686' },
  err: { margin: 0, color: '#D7263D', fontSize: 13 },
  actions: { display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 4 },
  btn: { background: '#F4F6FB', color: '#0251FD', border: '1px solid #DDE8FF', borderRadius: 10, padding: '8px 16px', fontSize: 13, fontWeight: 700, cursor: 'pointer' },
  btnPrimary: { background: '#0251FD', color: '#fff', border: 'none', borderRadius: 10, padding: '8px 16px', fontSize: 13, fontWeight: 700, cursor: 'pointer' },
}
