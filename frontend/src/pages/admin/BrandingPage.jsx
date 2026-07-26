import { useEffect, useRef, useState } from 'react'
import { Helmet } from 'react-helmet-async'
import { useSettings } from '../../contexts/SettingsContext'
import {
  uploadLogo,
  deleteLogo,
  updateSettings,
  uploadFooterLogo,
  uploadFooterBrandLogo,
  deleteFooterBrandLogo,
  uploadLegalDocument,
} from '../../api/settings'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import { IconSettings } from '../../components/admin/adminIcons'

const ACCEPT = 'image/png,image/jpeg,image/webp,image/gif'
const ACCEPT_DOC = 'application/pdf,.pdf,.doc,.docx,.txt'

const toFooterForm = (s) => ({
  footer_tagline: s?.footer_tagline || '',
  copyright_text: s?.copyright_text || '',
  social_instagram: s?.social_instagram || '',
  social_linkedin: s?.social_linkedin || '',
  social_youtube: s?.social_youtube || '',
  legal_privacy_url: s?.legal_privacy_url || '',
  legal_terms_url: s?.legal_terms_url || '',
  legal_cookies_url: s?.legal_cookies_url || '',
  footer_logos: Array.isArray(s?.footer_logos) ? s.footer_logos : [],
})

// Uploads an ally logo image on select and reports back { image_url, storage_key }.
function FooterLogoPicker({ value, onChange }) {
  const ref = useRef(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)

  const pick = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setErr(null)
    setBusy(true)
    try {
      const { url, storage_key } = await uploadFooterLogo(file)
      onChange({ image_url: url, storage_key })
    } catch {
      setErr('No se pudo subir la imagen')
    } finally {
      setBusy(false)
      if (ref.current) ref.current.value = ''
    }
  }

  return (
    <div className="logo-picker">
      {value
        ? <img src={value} alt="logo" className="footer-logo-thumb" />
        : <div className="logo-picker-empty">Sin imagen</div>}
      <input ref={ref} type="file" accept={ACCEPT} onChange={pick} style={{ display: 'none' }} />
      <button type="button" className="btn btn-outline btn-sm" disabled={busy} onClick={() => ref.current?.click()}>
        {busy ? 'Subiendo…' : value ? 'Cambiar' : 'Subir imagen'}
      </button>
      {err && <p className="admin-error" style={{ marginTop: 6 }}>{err}</p>}
    </div>
  )
}

// Un documento legal del footer: se sube un PDF (o se pega una URL externa).
// Al subir o quitar el archivo el enlace se guarda de inmediato.
function LegalDocField({ label, kind, value, onChange, onSave }) {
  const ref = useRef(null)
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)
  const [err, setErr] = useState(null)

  const pick = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setErr(null)
    setDone(false)
    setBusy(true)
    try {
      const { url } = await uploadLegalDocument(file, kind)
      await onSave(url)
      setDone(true)
    } catch (error) {
      setErr(error.response?.data?.error?.message || error.response?.data?.detail || 'No se pudo subir el documento')
    } finally {
      setBusy(false)
      if (ref.current) ref.current.value = ''
    }
  }

  const clear = async () => {
    if (!confirm(`¿Quitar el enlace de «${label}» del pie de página?`)) return
    setErr(null)
    setDone(false)
    setBusy(true)
    try {
      await onSave('')
    } catch {
      setErr('No se pudo quitar el enlace')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fg" style={{ marginTop: 14 }}>
      <label>{label}</label>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
        <input
          style={{ flex: '1 1 260px' }}
          placeholder="Sube un PDF o pega una URL"
          value={value}
          onChange={onChange}
        />
        <input ref={ref} type="file" accept={ACCEPT_DOC} onChange={pick} style={{ display: 'none' }} />
        <button type="button" className="btn btn-outline btn-sm" disabled={busy} onClick={() => ref.current?.click()}>
          {busy ? 'Subiendo…' : value ? 'Cambiar archivo' : 'Subir PDF'}
        </button>
        {value && (
          <>
            <a className="btn btn-outline btn-sm" href={value} target="_blank" rel="noreferrer">Ver</a>
            <button type="button" className="btn btn-outline btn-sm btn-danger" disabled={busy} onClick={clear}>Quitar</button>
          </>
        )}
      </div>
      {done && <p className="admin-ok" style={{ marginTop: 6 }}>Documento subido y publicado en el pie de página.</p>}
      {err && <p className="admin-error" style={{ marginTop: 6 }}>{err}</p>}
    </div>
  )
}

export default function BrandingPage() {
  const { logoUrl, footerLogoUrl, settings, setSettings, refresh } = useSettings()

  // ── Brand logo card state (header) ─────────────────────────────────────
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const inputRef = useRef(null)

  // ── Footer brand logo card state ───────────────────────────────────────
  const [fLogoFile, setFLogoFile] = useState(null)
  const [fLogoPreview, setFLogoPreview] = useState(null)
  const [fLogoBusy, setFLogoBusy] = useState(false)
  const [fLogoError, setFLogoError] = useState(null)
  const fLogoInputRef = useRef(null)

  // ── Footer config form state ───────────────────────────────────────────
  const [form, setForm] = useState(toFooterForm(settings))
  const [savingFooter, setSavingFooter] = useState(false)
  const [footerError, setFooterError] = useState(null)
  const [footerSaved, setFooterSaved] = useState(false)
  const hydrated = useRef(false)

  // Hydrate the footer form once settings arrive from the context.
  useEffect(() => {
    if (settings && !hydrated.current) {
      setForm(toFooterForm(settings))
      hydrated.current = true
    }
  }, [settings])

  const pick = (e) => {
    const f = e.target.files?.[0]
    setError(null)
    if (!f) return
    setFile(f)
    setPreview(URL.createObjectURL(f))
  }

  const reset = () => {
    setFile(null)
    setPreview(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  const save = async () => {
    if (!file) return
    setError(null)
    setBusy(true)
    try {
      await uploadLogo(file)
      await refresh()
      reset()
    } catch (err) {
      setError(err.response?.data?.error?.message || err.response?.data?.detail || 'Error al subir el logo')
    } finally {
      setBusy(false)
    }
  }

  const remove = async () => {
    if (!confirm('¿Quitar el logo actual y volver al texto?')) return
    setBusy(true)
    try {
      await deleteLogo()
      await refresh()
      reset()
    } catch {
      setError('Error al quitar el logo')
    } finally {
      setBusy(false)
    }
  }

  // ── Footer brand logo handlers ─────────────────────────────────────────
  const fLogoPick = (e) => {
    const f = e.target.files?.[0]
    setFLogoError(null)
    if (!f) return
    setFLogoFile(f)
    setFLogoPreview(URL.createObjectURL(f))
  }

  const fLogoReset = () => {
    setFLogoFile(null)
    setFLogoPreview(null)
    if (fLogoInputRef.current) fLogoInputRef.current.value = ''
  }

  const fLogoSave = async () => {
    if (!fLogoFile) return
    setFLogoError(null)
    setFLogoBusy(true)
    try {
      await uploadFooterBrandLogo(fLogoFile)
      await refresh()
      fLogoReset()
    } catch (err) {
      setFLogoError(err.response?.data?.error?.message || err.response?.data?.detail || 'Error al subir el logo del footer')
    } finally {
      setFLogoBusy(false)
    }
  }

  const fLogoRemove = async () => {
    if (!confirm('¿Quitar el logo del footer y usar el del encabezado?')) return
    setFLogoBusy(true)
    try {
      await deleteFooterBrandLogo()
      await refresh()
      fLogoReset()
    } catch {
      setFLogoError('Error al quitar el logo del footer')
    } finally {
      setFLogoBusy(false)
    }
  }

  // ── Footer form helpers ────────────────────────────────────────────────
  const upd = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))
  const addLogo = () =>
    setForm((f) => ({ ...f, footer_logos: [...f.footer_logos, { name: '', image_url: '', link: '', storage_key: '' }] }))
  const updLogo = (i, patch) =>
    setForm((f) => ({ ...f, footer_logos: f.footer_logos.map((l, idx) => (idx === i ? { ...l, ...patch } : l)) }))
  const removeLogo = (i) =>
    setForm((f) => ({ ...f, footer_logos: f.footer_logos.filter((_, idx) => idx !== i) }))

  // Guarda un enlace legal (URL subida o vacía) sin esperar el botón del formulario.
  const saveLegalUrl = (key) => async (url) => {
    const next = { ...form, [key]: url }
    setForm(next)
    const updated = await updateSettings({ ...next, footer_logos: next.footer_logos.filter((l) => l.image_url) })
    setSettings(updated)
    setForm(toFooterForm(updated))
  }

  const saveFooter = async (e) => {
    e.preventDefault()
    setFooterError(null)
    setFooterSaved(false)
    setSavingFooter(true)
    try {
      const payload = { ...form, footer_logos: form.footer_logos.filter((l) => l.image_url) }
      const updated = await updateSettings(payload)
      setSettings(updated)
      setForm(toFooterForm(updated))
      setFooterSaved(true)
    } catch (err) {
      setFooterError(err.response?.data?.error?.message || err.response?.data?.detail || 'No se pudieron guardar los cambios')
    } finally {
      setSavingFooter(false)
    }
  }

  return (
    <>
      <Helmet><title>Logo y marca | Listing Admin</title></Helmet>

      <AdminPageHeader
        title="Logo y marca"
        subtitle="Logo del sitio y configuración del pie de página"
      />

      {/* ── Logo global ─────────────────────────────────────────────── */}
      <div className="admin-card">
        <h3 className="admin-card-title">Logo actual</h3>
        <div className="brand-preview">
          {logoUrl
            ? <img src={logoUrl} alt="Logo actual" className="brand-preview-img" />
            : <span className="brand-preview-text"><span className="dot">P</span>Propp<b>ietario</b></span>}
        </div>
        {logoUrl
          ? <p className="admin-hint">Se está usando un logo personalizado (encabezado y panel; el pie de página lo usa salvo que definas uno propio abajo).</p>
          : <p className="admin-hint">Sin logo personalizado: el portal muestra el texto «Proppia».</p>}
        {logoUrl && (
          <button className="btn btn-outline btn-danger btn-sm" onClick={remove} disabled={busy} style={{ marginTop: 12 }}>
            Quitar logo
          </button>
        )}
      </div>

      <div className="admin-card admin-card-form">
        <h3 className="admin-card-title">Cambiar logo</h3>
        {error && <p className="admin-error">{error}</p>}

        <div className="fg">
          <label>Archivo (PNG, JPG, WebP o GIF · máx. 10 MB)</label>
          <input ref={inputRef} type="file" accept={ACCEPT} onChange={pick} />
        </div>

        {preview && (
          <div className="brand-preview" style={{ marginTop: 12 }}>
            <img src={preview} alt="Vista previa" className="brand-preview-img" />
          </div>
        )}

        <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
          <button className="btn btn-blue" onClick={save} disabled={!file || busy}>
            {busy ? 'Guardando…' : 'Guardar logo'}
          </button>
          {file && (
            <button className="btn btn-outline" onClick={reset} disabled={busy}>Cancelar</button>
          )}
        </div>
      </div>

      {/* ── Logo del pie de página ───────────────────────────────────── */}
      <div className="admin-card admin-card-form">
        <h3 className="admin-card-title">Logo del pie de página</h3>
        <p className="admin-hint" style={{ marginBottom: 14 }}>
          Independiente del encabezado. Si lo dejas vacío, el footer usa el logo del encabezado.
        </p>
        {fLogoError && <p className="admin-error">{fLogoError}</p>}

        <div className="brand-preview">
          {fLogoPreview || footerLogoUrl
            ? <img src={fLogoPreview || footerLogoUrl} alt="Logo del footer" className="brand-preview-img" />
            : <span className="admin-hint">Usando el logo del encabezado</span>}
        </div>

        <div className="fg" style={{ marginTop: 12 }}>
          <label>Archivo (PNG, JPG, WebP o GIF · máx. 10 MB)</label>
          <input ref={fLogoInputRef} type="file" accept={ACCEPT} onChange={fLogoPick} />
        </div>

        <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
          <button className="btn btn-blue" onClick={fLogoSave} disabled={!fLogoFile || fLogoBusy}>
            {fLogoBusy ? 'Guardando…' : 'Guardar logo del footer'}
          </button>
          {fLogoFile && (
            <button className="btn btn-outline" onClick={fLogoReset} disabled={fLogoBusy}>Cancelar</button>
          )}
          {footerLogoUrl && !fLogoFile && (
            <button className="btn btn-outline btn-danger" onClick={fLogoRemove} disabled={fLogoBusy}>
              Quitar logo del footer
            </button>
          )}
        </div>
      </div>

      {/* ── Configuración del footer ─────────────────────────────────── */}
      <form onSubmit={saveFooter}>
        {footerError && <p className="admin-error">{footerError}</p>}
        {footerSaved && <p className="admin-ok">Cambios del footer guardados.</p>}

        <div className="admin-card admin-card-form">
          <h3 className="admin-card-title">Textos del pie de página</h3>
          <div className="fg"><label>Descripción</label><textarea rows={2} value={form.footer_tagline} onChange={upd('footer_tagline')} /></div>
          <div className="fg" style={{ marginTop: 12 }}><label>Copyright</label><input value={form.copyright_text} onChange={upd('copyright_text')} /></div>
        </div>

        <div className="admin-card admin-card-form">
          <h3 className="admin-card-title">Redes sociales</h3>
          <p className="admin-hint" style={{ marginBottom: 14 }}>Deja vacío un campo para que ese ícono no enlace a ningún lado.</p>
          <div className="fg"><label>Instagram</label><input placeholder="https://instagram.com/…" value={form.social_instagram} onChange={upd('social_instagram')} /></div>
          <div className="fg" style={{ marginTop: 12 }}><label>LinkedIn</label><input placeholder="https://linkedin.com/…" value={form.social_linkedin} onChange={upd('social_linkedin')} /></div>
          <div className="fg" style={{ marginTop: 12 }}><label>YouTube</label><input placeholder="https://youtube.com/…" value={form.social_youtube} onChange={upd('social_youtube')} /></div>
        </div>

        <div className="admin-card admin-card-form">
          <h3 className="admin-card-title">Documentos legales</h3>
          <p className="admin-hint" style={{ marginBottom: 6 }}>
            Sube el PDF de cada documento (máx. 10 MB; también acepta DOC, DOCX o TXT) y el pie de página
            enlazará a él automáticamente. Si prefieres alojarlo en otro sitio, pega la URL y guarda los cambios.
            Un campo vacío oculta ese enlace del pie de página.
          </p>
          <LegalDocField
            label="Términos de uso"
            kind="terminos"
            value={form.legal_terms_url}
            onChange={upd('legal_terms_url')}
            onSave={saveLegalUrl('legal_terms_url')}
          />
          <LegalDocField
            label="Política de privacidad"
            kind="privacidad"
            value={form.legal_privacy_url}
            onChange={upd('legal_privacy_url')}
            onSave={saveLegalUrl('legal_privacy_url')}
          />
          <LegalDocField
            label="Política de cookies"
            kind="cookies"
            value={form.legal_cookies_url}
            onChange={upd('legal_cookies_url')}
            onSave={saveLegalUrl('legal_cookies_url')}
          />
        </div>

        <div className="admin-card admin-card-form">
          <h3 className="admin-card-title">Logos de aliados</h3>
          <p className="admin-hint" style={{ marginBottom: 14 }}>Se muestran como una tira en el pie de página. Cada logo puede enlazar a un sitio.</p>
          {form.footer_logos.length === 0 && <p className="admin-hint">Aún no hay logos. Agrega el primero.</p>}
          <div className="brand-logos">
            {form.footer_logos.map((logo, i) => (
              <div className="brand-logo-row" key={i}>
                <FooterLogoPicker value={logo.image_url} onChange={(patch) => updLogo(i, patch)} />
                <div className="brand-logo-fields">
                  <input placeholder="Nombre" value={logo.name} onChange={(e) => updLogo(i, { name: e.target.value })} />
                  <input placeholder="Enlace (opcional)" value={logo.link || ''} onChange={(e) => updLogo(i, { link: e.target.value })} />
                </div>
                <button type="button" className="btn btn-outline btn-sm btn-danger" onClick={() => removeLogo(i)}>Eliminar</button>
              </div>
            ))}
          </div>
          <button type="button" className="btn btn-outline btn-sm" style={{ marginTop: 12 }} onClick={addLogo}>+ Agregar logo</button>
        </div>

        <button className="btn btn-blue" disabled={savingFooter}>
          {savingFooter ? 'Guardando…' : 'Guardar configuración del footer'}
        </button>
      </form>

      <div className="adm-empty" style={{ marginTop: 18 }}>
        <span className="ico"><IconSettings size={26} /></span>
        <b>Recomendación</b>
        Usa un PNG con fondo transparente de aproximadamente 200×48&nbsp;px para que el logo se vea nítido en todas las barras.
      </div>
    </>
  )
}
