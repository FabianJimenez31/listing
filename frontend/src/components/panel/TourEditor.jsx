import { useEffect, useRef, useState } from 'react'
import {
  confirmBillingPayment,
  createBillingIntent,
  createTour,
  deleteTourScene,
  generateTourScene,
  getAdminTour,
  getBillingConfig,
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
  const [ack, setAck] = useState(false)
  const [billing, setBilling] = useState(null)

  const load = () => getAdminTour(entity, entityId)
    .then((data) => { setTour(data); setAck(data.ai_disclaimer_ack) })
    .catch((err) => { if (err.response?.status !== 404) setError(apiMessage(err)) })

  useEffect(() => {
    Promise.all([load(), getTourProvider().then(setProvider).catch(() => null), getBillingConfig().then(setBilling).catch(() => null)])
      .finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entity, entityId])

  useEffect(() => {
    if (!tour?.scenes?.some((scene) => scene.state === 'pending')) return undefined
    const timer = setInterval(load, 3000)
    return () => clearInterval(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tour?.scenes?.map((scene) => `${scene.id}:${scene.state}`).join('|')])

  const run = async (action) => {
    setBusy(true)
    setError(null)
    try { await action(); await load() } catch (err) { setError(apiMessage(err)) } finally { setBusy(false) }
  }

  const startTour = () => run(async () => setTour(await createTour(entity, entityId)))

  // Flujo de pago (006): intent -> widget Wompi -> confirmacion -> crear tour.
  const payAndCreate = async () => {
    setBusy(true)
    setError(null)
    try {
      const intent = await createBillingIntent(entity, entityId)
      if (intent.already_paid) {
        setTour(await createTour(entity, entityId))
        return
      }
      const transaction = await openWompiWidget(intent)
      await confirmBillingPayment(intent.reference, transaction?.id)
      setTour(await createTour(entity, entityId))
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
  if (!tour) {
    const price = billing?.amount_in_cents ? formatCop(billing.amount_in_cents) : '$50.000'
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

  return (
    <section className="tour-editor admin-card">
      <div className="tour-editor-head">
        <div><h3>Tour 360</h3><p>{tour.scenes.length} ambientes · Estado: <b>{tour.status === 'published' ? 'Publicado' : 'Borrador'}</b></p></div>
        <button type="button" className={`btn btn-sm ${tour.status === 'published' ? 'btn-outline' : 'btn-blue'}`} disabled={busy} onClick={setPublished}>
          {tour.status === 'published' ? 'Despublicar' : 'Publicar tour'}
        </button>
      </div>
      {error && <p className="tour-error">{error}</p>}

      {tour.scenes.length > 0 && (
        <div className="tour-scene-list">
          {tour.scenes.map((scene, index) => (
            <article key={scene.id} className={`tour-scene-card ${scene.state}`}>
              <img src={scene.thumb_url || scene.pano_url || galleryImages[0]?.cdn_url} alt="" />
              <div className="tour-scene-info">
                <strong>{scene.title}</strong>
                <span>{scene.source === 'ai' ? 'Generada con IA' : 'Subida directa'} · {scene.state}</span>
                {scene.error_message && <small>{scene.error_message}</small>}
              </div>
              <div className="tour-scene-actions">
                <button type="button" disabled={index === 0 || busy} onClick={() => move(scene.id, -1)}>↑</button>
                <button type="button" disabled={index === tour.scenes.length - 1 || busy} onClick={() => move(scene.id, 1)}>↓</button>
                <button type="button" onClick={() => rename(scene)}>Renombrar</button>
                {scene.state === 'ready' && tour.scenes.length > 1 && <button type="button" onClick={() => setHotspotScene(scene)}>Hotspots</button>}
                <button type="button" className={tour.start_scene_id === scene.id ? 'selected' : ''} onClick={() => setStart(scene.id)}>Inicial</button>
                <button type="button" className="danger" onClick={() => remove(scene)}>Eliminar</button>
              </div>
            </article>
          ))}
        </div>
      )}

      {hotspotScene && (
        <TourHotspotPicker scene={hotspotScene} scenes={tour.scenes} onSave={saveHotspots} onClose={() => setHotspotScene(null)} />
      )}

      <div className="tour-create-grid">
        <div className="tour-create-box">
          <h4>Subir panorámica 2:1</h4>
          <input value={sceneTitle} onChange={(e) => setSceneTitle(e.target.value)} placeholder="Ej. Sala" />
          <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" onChange={upload} disabled={busy} />
          <small>Máximo 25 MB. Se optimiza a WebP automáticamente.</small>
        </div>

        <div className="tour-create-box">
          <h4>Generar desde la galería</h4>
          <input value={aiTitle} onChange={(e) => setAiTitle(e.target.value)} placeholder="Ej. Cocina" />
          <div className="tour-reference-grid">
            {galleryImages.map((image) => (
              <button
                type="button"
                key={image.id}
                className={selectedImages.includes(image.id) ? 'selected' : ''}
                disabled={!selectedImages.includes(image.id) && selectedImages.length >= 10}
                onClick={() => toggleReference(image.id)}
              >
                <img src={image.thumb_url || image.cdn_url} alt="" />
              </button>
            ))}
          </div>
          <small>{selectedImages.length}/10 fotos seleccionadas · máximo por escena</small>
          <label className="tour-check"><input type="checkbox" checked={seamPass} onChange={(e) => setSeamPass(e.target.checked)} /> Reparar costura para 360 completo</label>
          <button type="button" className="btn btn-blue btn-sm" disabled={busy || !provider?.available || !galleryImages.length} onClick={generate}>Generar con IA</button>
          <small>{provider?.available ? 'La escena se genera en segundos y queda en borrador para tu revisión' : provider?.reason || 'Proveedor no configurado'}</small>
        </div>
      </div>

      {tour.contains_ai && (
        <label className="tour-ack">
          <input type="checkbox" checked={ack} onChange={(e) => setAck(e.target.checked)} />
          Acepto que las escenas generadas con IA son recreaciones y deben mostrarse con aviso público.
        </label>
      )}
    </section>
  )
}
