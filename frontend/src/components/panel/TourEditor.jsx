import { useEffect, useRef, useState } from 'react'
import {
  confirmBillingPayment,
  createBillingIntent,
  createTour,
  deleteTourScene,
  generateTourScene,
  getAdminTour,
  getBillingConfig,
  getCreditStatus,
  getTourProvider,
  openWompiWidget,
  reorderTourScenes,
  replaceTourHotspots,
  updateTour,
  updateTourScene,
  uploadTourScene,
} from '../../api/tours'
import TourHotspotPicker from './TourHotspotPicker'
import '../../styles/tour.css'

const apiMessage = (error) => error.response?.data?.error?.message
  || error.response?.data?.detail
  || 'No se pudo completar la acción'

function imageRatio(file) {
  return new Promise((resolve, reject) => {
    const image = new Image()
    const url = URL.createObjectURL(file)
    image.onload = () => { URL.revokeObjectURL(url); resolve(image.width / image.height) }
    image.onerror = () => { URL.revokeObjectURL(url); reject(new Error('Imagen inválida')) }
    image.src = url
  })
}

export default function TourEditor({ entity, entityId, galleryImages = [] }) {
  const fileRef = useRef(null)
  const [tour, setTour] = useState(null)
  const [provider, setProvider] = useState(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [sceneTitle, setSceneTitle] = useState('')
  const [hotspotScene, setHotspotScene] = useState(null)
  const [aiTitle, setAiTitle] = useState('')
  const [selectedImages, setSelectedImages] = useState([])
  const [seamPass, setSeamPass] = useState(false)
  const [creationMode, setCreationMode] = useState('ai')
  const [ack, setAck] = useState(false)
  const [billing, setBilling] = useState(null)
  // null = verificando; solo se muestra el editor cuando hay credito confirmado.
  const [creditActive, setCreditActive] = useState(null)

  const load = () => getAdminTour(entity, entityId)
    .then((data) => { setTour(data); setAck(data.ai_disclaimer_ack) })
    .catch((err) => { if (err.response?.status !== 404) setError(apiMessage(err)) })

  useEffect(() => {
    Promise.all([load(), getTourProvider().then(setProvider).catch(() => null), getBillingConfig().then(setBilling).catch(() => null)])
      .finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entity, entityId])

  useEffect(() => {
    if (!billing?.enabled) { setCreditActive(true); return }
    let cancelled = false
    const check = () => getCreditStatus(entity, entityId)
      .then((r) => { if (!cancelled) setCreditActive(r.active) })
      .catch(() => { if (!cancelled) setTimeout(check, 1500) })
    check()
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [billing?.enabled, entity, entityId])

  useEffect(() => {
    if (!tour?.scenes?.some((scene) => scene.state === 'pending')) return undefined
    const timer = setInterval(load, 3000)
    return () => clearInterval(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tour?.scenes?.map((scene) => `${scene.id}:${scene.state}`).join('|')])

  const run = async (action) => {
    setBusy(true)
    setError(null)
    try { await action(); await load() } catch (err) {
      // Defensa en profundidad: un 402 del backend bloquea la UI al instante.
      if (err?.response?.status === 402) setCreditActive(false)
      setError(apiMessage(err))
    } finally { setBusy(false) }
  }

  const startTour = () => run(async () => setTour(await createTour(entity, entityId)))

  // Flujo de pago (006): intent -> widget Wompi -> confirmacion. Sirve tanto para
  // crear un tour nuevo como para activar uno existente sin credito.
  const payAndCreate = async () => {
    setBusy(true)
    setError(null)
    try {
      const intent = await createBillingIntent(entity, entityId)
      if (intent.already_paid) {
        setTour(await createTour(entity, entityId))
        setCreditActive(true)
        return
      }
      const transaction = await openWompiWidget(intent)
      await confirmBillingPayment(intent.reference, transaction?.id)
      if (!tour) setTour(await createTour(entity, entityId))
      else await load()
      setCreditActive(true)
    } catch (err) {
      setError(err?.message || apiMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const formatCop = (cents) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(cents / 100)

  const upload = async (event) => {
    const file = event.target.files?.[0]
    if (!file || !sceneTitle.trim()) { setError('Escribe el nombre del ambiente y selecciona la panorámica'); return }
    try {
      const ratio = await imageRatio(file)
      if (Math.abs(ratio - 2) > 0.1) {
        setError(`La panorámica debe ser aproximadamente 2:1; esta imagen tiene relación ${ratio.toFixed(2)}:1`)
        return
      }
      await run(() => uploadTourScene(entity, entityId, file, sceneTitle.trim()))
      setSceneTitle('')
      if (fileRef.current) fileRef.current.value = ''
    } catch (err) { setError(apiMessage(err)) }
  }

  const move = (sceneId, direction) => {
    const ids = tour.scenes.map((scene) => scene.id)
    const index = ids.indexOf(sceneId)
    const target = index + direction
    if (target < 0 || target >= ids.length) return
    ;[ids[index], ids[target]] = [ids[target], ids[index]]
    run(() => reorderTourScenes(entity, entityId, ids))
  }

  const rename = (scene) => {
    const title = window.prompt('Nombre del ambiente', scene.title)
    if (title?.trim() && title.trim() !== scene.title) run(() => updateTourScene(scene.id, { title: title.trim() }))
  }

  const remove = (scene) => {
    if (window.confirm(`¿Eliminar la escena “${scene.title}”?`)) run(() => deleteTourScene(scene.id))
  }

  const setStart = (sceneId) => run(() => updateTour(entity, entityId, { start_scene_id: sceneId }))

  const saveHotspots = (hotspots) => run(async () => {
    await replaceTourHotspots(hotspotScene.id, hotspots.map(({ to_scene_id, yaw, pitch, label }) => ({ to_scene_id, yaw, pitch, label })))
    setHotspotScene(null)
  })

  const toggleReference = (imageId) => setSelectedImages((ids) => (
    ids.includes(imageId) ? ids.filter((id) => id !== imageId) : [...ids, imageId]
  ))

  const generate = () => {
    if (!aiTitle.trim() || !selectedImages.length) { setError('Indica el ambiente y selecciona al menos una foto'); return }
    if (!window.confirm(`¿Generar la escena “${aiTitle.trim()}” con IA a partir de ${selectedImages.length} foto(s)?`)) return
    run(async () => {
      await generateTourScene(entity, entityId, {
        title: aiTitle.trim(), source_image_ids: selectedImages, seam_pass: seamPass,
      })
      setAiTitle('')
      setSelectedImages([])
    })
  }

  const setPublished = () => run(() => updateTour(entity, entityId, {
    status: tour.status === 'published' ? 'draft' : 'published',
    ai_disclaimer_ack: ack,
  }))

  if (loading) return <div className="tour-editor admin-card">Cargando Tour 360…</div>
  const price = billing?.amount_in_cents ? formatCop(billing.amount_in_cents) : '$50.000'

  if (tour && billing?.enabled && creditActive === null) {
    return <div className="tour-editor admin-card">Verificando activación del tour…</div>
  }

  if (tour && billing?.enabled && !creditActive) {
    return (
      <section className="tour-editor admin-card">
        <h3>Tour 360</h3>
        {error && <p className="tour-error">{error}</p>}
        <div className="tour-paywall">
          <div className="tour-paywall-price">
            <strong>{price}</strong>
            <span> activación única de este tour</span>
          </div>
          <ul>
            <li>{tour.scenes.length} escenas actuales · hasta 10</li>
            <li>Desbloquea edición, IA y publicación</li>
          </ul>
          <button type="button" className="btn btn-blue" disabled={busy} onClick={payAndCreate}>
            {busy ? 'Abriendo pasarela…' : `Activar por ${price}`}
          </button>
          <small>Pago seguro procesado por Wompi · PSE, tarjetas, Nequi</small>
        </div>
      </section>
    )
  }

  if (!tour) {
    if (billing?.enabled) {
      return (
        <section className="tour-editor admin-card">
          <h3>Tour 360</h3>
          <p>Recorrido 360 por ambientes con flechas de navegación. Hasta 10 escenas; cada una puede subirse en 2:1 o generarse con IA.</p>
          {error && <p className="tour-error">{error}</p>}
          <div className="tour-paywall">
            <div className="tour-paywall-price">
              <strong>{price}</strong>
              <span> pago único por tour</span>
            </div>
            <ul>
              <li>Hasta 10 escenas 360°</li>
              <li>Flechas de navegación estilo Matterport</li>
              <li>Publicación directa en tu ficha</li>
            </ul>
            <button type="button" className="btn btn-blue" disabled={busy} onClick={payAndCreate}>
              {busy ? 'Abriendo pasarela…' : `Pagar ${price} y crear tour`}
            </button>
            <small>Pago seguro procesado por Wompi · PSE, tarjetas, Nequi</small>
          </div>
        </section>
      )
    }
    return (
      <section className="tour-editor admin-card">
        <h3>Tour 360</h3>
        <p>Crea recorridos por ambientes con panorámicas y hotspots.</p>
        {error && <p className="tour-error">{error}</p>}
        <button type="button" className="btn btn-blue btn-sm" disabled={busy} onClick={startTour}>Crear tour</button>
        {!billing && <small style={{ display: 'block', marginTop: 8, color: 'var(--muted)' }}>La creación de tours está temporalmente limitada mientras se activa la pasarela de pagos.</small>}
      </section>
    )
  }

  const readyScenes = tour.scenes.filter((scene) => scene.state === 'ready')
  const nextReadyScene = (scene) => {
    const index = readyScenes.findIndex((item) => item.id === scene.id)
    return index >= 0 && readyScenes.length > 1
      ? readyScenes[(index + 1) % readyScenes.length]
      : null
  }
  const publishDisabled = busy || readyScenes.length === 0 || (tour.contains_ai && !ack)

  return (
    <section className="tour-editor admin-card tour-wizard">
      <div className="tour-editor-head">
        <div>
          <span className="tour-kicker">Configuración guiada</span>
          <h3>Tour 360</h3>
          <p>Agrega los ambientes y nosotros armamos el recorrido automáticamente.</p>
        </div>
        <span className={`tour-status ${tour.status}`}>{tour.status === 'published' ? 'Publicado' : 'Borrador'}</span>
      </div>

      <ol className="tour-setup-steps">
        <li className={tour.scenes.length ? 'done' : 'active'}><span>1</span><div><b>Ambientes</b><small>{tour.scenes.length}/10 creados</small></div></li>
        <li className={readyScenes.length > 1 ? 'done' : readyScenes.length ? 'active' : ''}><span>2</span><div><b>Recorrido</b><small>{readyScenes.length > 1 ? 'Conectado' : 'Falta otro ambiente'}</small></div></li>
        <li className={tour.status === 'published' ? 'done' : ''}><span>3</span><div><b>Publicar</b><small>{tour.status === 'published' ? 'Visible' : 'Cuando esté listo'}</small></div></li>
      </ol>

      {error && <p className="tour-error" role="alert">{error}</p>}

      <section className="tour-workflow-section">
        <div className="tour-section-head">
          <span className="tour-step-number">1</span>
          <div><h4>Agrega un ambiente</h4><p>Crea Sala, Comedor, Cocina o cada espacio que quieras recorrer.</p></div>
        </div>
        <div className="tour-method-tabs" role="tablist" aria-label="Método para crear ambiente">
          <button type="button" className={creationMode === 'ai' ? 'active' : ''} onClick={() => setCreationMode('ai')}>Generar con IA</button>
          <button type="button" className={creationMode === 'upload' ? 'active' : ''} onClick={() => setCreationMode('upload')}>Ya tengo una foto 360</button>
        </div>

        {creationMode === 'ai' ? (
          <div className="tour-create-box tour-create-box-wide">
            <label className="tour-field-label" htmlFor="tour-ai-title">Nombre del ambiente</label>
            <input id="tour-ai-title" value={aiTitle} onChange={(e) => setAiTitle(e.target.value)} placeholder="Ej. Sala principal" />
            <div className="tour-field-label">Selecciona fotos del mismo ambiente</div>
            <p className="tour-field-help">Estas fotos se combinan para crear una sola vista 360.</p>
            <div className="tour-reference-grid">
              {galleryImages.map((image, index) => {
                const selected = selectedImages.includes(image.id)
                return (
                  <button
                    type="button"
                    key={image.id}
                    className={selected ? 'selected' : ''}
                    disabled={!selected && selectedImages.length >= 10}
                    onClick={() => toggleReference(image.id)}
                    aria-label={`${selected ? 'Quitar' : 'Seleccionar'} foto ${index + 1}`}
                  >
                    <img src={image.thumb_url || image.cdn_url} alt="" />
                    {selected && <span className="tour-reference-check">✓</span>}
                  </button>
                )
              })}
            </div>
            <div className="tour-create-footer">
              <span>{selectedImages.length}/10 seleccionadas</span>
              <button type="button" className="btn btn-blue" disabled={busy || !provider?.available || !galleryImages.length || !aiTitle.trim() || !selectedImages.length} onClick={generate}>
                {busy ? 'Creando ambiente…' : 'Crear escena 360'}
              </button>
            </div>
            <details className="tour-advanced">
              <summary>Opciones avanzadas</summary>
              <label className="tour-check"><input type="checkbox" checked={seamPass} onChange={(e) => setSeamPass(e.target.checked)} /> Reparar la unión de la panorámica</label>
            </details>
            {!provider?.available && <small className="tour-provider-error">{provider?.reason || 'El generador no está disponible.'}</small>}
          </div>
        ) : (
          <div className="tour-create-box tour-create-box-wide">
            <label className="tour-field-label" htmlFor="tour-upload-title">Nombre del ambiente</label>
            <input id="tour-upload-title" value={sceneTitle} onChange={(e) => setSceneTitle(e.target.value)} placeholder="Ej. Sala principal" />
            <label className="tour-upload-drop">
              <b>Seleccionar panorámica 2:1</b>
              <span>JPEG, PNG o WebP · máximo 25 MB</span>
              <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" onChange={upload} disabled={busy} />
            </label>
          </div>
        )}
      </section>

      <section className="tour-workflow-section">
        <div className="tour-section-head">
          <span className="tour-step-number">2</span>
          <div><h4>Ordena el recorrido</h4><p>Las flechas conectan automáticamente cada ambiente con el siguiente.</p></div>
        </div>

        {tour.scenes.length === 0 ? (
          <div className="tour-empty-state"><b>Aún no hay ambientes</b><span>Crea el primero en el paso anterior.</span></div>
        ) : (
          <>
            {readyScenes.length > 1 ? (
              <div className="tour-auto-route"><span>✓</span><div><b>Recorrido conectado automáticamente</b><small>Usa Subir y Bajar para cambiar el orden de visita.</small></div></div>
            ) : (
              <div className="tour-guidance"><b>Primer ambiente listo.</b> Agrega uno más y aparecerá la navegación automáticamente.</div>
            )}
            <div className="tour-scene-list">
              {tour.scenes.map((scene, index) => {
                const next = nextReadyScene(scene)
                const startsHere = (tour.start_scene_id || readyScenes[0]?.id) === scene.id
                return (
                  <article key={scene.id} className={`tour-scene-card ${scene.state}`}>
                    <span className="tour-scene-number">{index + 1}</span>
                    <img src={scene.thumb_url || scene.pano_url || galleryImages[0]?.cdn_url} alt="" />
                    <div className="tour-scene-info">
                      <strong>{scene.title}</strong>
                      <span>{scene.source === 'ai' ? 'Generada con IA' : 'Panorámica subida'} · {scene.state === 'ready' ? 'Lista' : scene.state === 'pending' ? 'Generando…' : 'Falló'}</span>
                      {startsHere && <small className="tour-start-label">Inicio del recorrido</small>}
                      {next && <small className="tour-next-label">Luego continúa a <b>{next.title}</b></small>}
                      {scene.error_message && <small className="tour-scene-error">{scene.error_message}</small>}
                    </div>
                    <div className="tour-scene-actions">
                      <div className="tour-order-actions" aria-label={`Orden de ${scene.title}`}>
                        <button type="button" disabled={index === 0 || busy} onClick={() => move(scene.id, -1)} aria-label={`Subir ${scene.title}`}>↑ <span>Subir</span></button>
                        <button type="button" disabled={index === tour.scenes.length - 1 || busy} onClick={() => move(scene.id, 1)} aria-label={`Bajar ${scene.title}`}>↓ <span>Bajar</span></button>
                      </div>
                      <button type="button" onClick={() => rename(scene)}>Editar nombre</button>
                      {!startsHere && scene.state === 'ready' && <button type="button" onClick={() => setStart(scene.id)}>Empezar aquí</button>}
                      {next && <button type="button" className="tour-adjust-link" onClick={() => setHotspotScene(scene)}>Ajustar flecha <span>(opcional)</span></button>}
                      <button type="button" className="danger" onClick={() => remove(scene)}>Eliminar</button>
                    </div>
                  </article>
                )
              })}
            </div>
          </>
        )}

        {hotspotScene && nextReadyScene(hotspotScene) && (
          <TourHotspotPicker
            key={`${hotspotScene.id}:${nextReadyScene(hotspotScene).id}`}
            scene={hotspotScene}
            targetScene={nextReadyScene(hotspotScene)}
            onSave={saveHotspots}
            onClose={() => setHotspotScene(null)}
          />
        )}
      </section>

      <section className="tour-workflow-section tour-publish-step">
        <div className="tour-section-head">
          <span className="tour-step-number">3</span>
          <div><h4>Publica el tour</h4><p>Podrás despublicarlo y seguir editándolo cuando quieras.</p></div>
        </div>
        {tour.contains_ai && (
          <label className="tour-ack">
            <input type="checkbox" checked={ack} onChange={(e) => setAck(e.target.checked)} />
            Confirmo que las escenas con IA son recreaciones visuales.
          </label>
        )}
        <div className="tour-publish-actions">
          <span>{readyScenes.length} ambiente{readyScenes.length === 1 ? '' : 's'} listo{readyScenes.length === 1 ? '' : 's'}</span>
          <button type="button" className={`btn ${tour.status === 'published' ? 'btn-outline' : 'btn-blue'}`} disabled={tour.status !== 'published' && publishDisabled} onClick={setPublished}>
            {busy ? 'Guardando…' : tour.status === 'published' ? 'Despublicar tour' : 'Publicar tour'}
          </button>
        </div>
      </section>
    </section>
  )
}
