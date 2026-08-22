import api from './client'

export const getPublishedTour = (entity, entityId) =>
  api.get(`/${entity}/${entityId}/tour`).then((r) => r.data)

export const getAdminTour = (entity, entityId) =>
  api.get(`/${entity}/${entityId}/tour/admin`).then((r) => r.data)

export const createTour = (entity, entityId) =>
  api.post(`/${entity}/${entityId}/tour`).then((r) => r.data)

export const updateTour = (entity, entityId, data) =>
  api.patch(`/${entity}/${entityId}/tour`, data).then((r) => r.data)

export const uploadTourScene = (entity, entityId, file, title, hfov = 360, vfov = 180) => {
  const form = new FormData()
  form.append('file', file)
  form.append('title', title)
  form.append('hfov_deg', hfov)
  form.append('vfov_deg', vfov)
  return api.post(`/${entity}/${entityId}/tour/scenes`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data)
}

export const updateTourScene = (sceneId, data) =>
  api.patch(`/tour/scenes/${sceneId}`, data).then((r) => r.data)

export const deleteTourScene = (sceneId) => api.delete(`/tour/scenes/${sceneId}`)

export const reorderTourScenes = (entity, entityId, orderedIds) =>
  api.patch(`/${entity}/${entityId}/tour/scenes/reorder`, { ordered_ids: orderedIds })
    .then((r) => r.data)

export const replaceTourHotspots = (sceneId, hotspots) =>
  api.put(`/tour/scenes/${sceneId}/hotspots`, { hotspots }).then((r) => r.data)

export const generateTourScene = (entity, entityId, data) =>
  api.post(`/${entity}/${entityId}/tour/scenes:generate`, data).then((r) => r.data)

export const getTourProvider = () => api.get('/tour/provider').then((r) => r.data)

export const getTourSceneStatus = (sceneId) =>
  api.get(`/tour/scenes/${sceneId}/status`).then((r) => r.data)

// ── Billing (006) ────────────────────────────────────────────────────────
export const getBillingConfig = () => api.get('/tour-billing/config').then((r) => r.data)

export const createBillingIntent = (entity, entityId) =>
  api.post('/tour-billing/intent', { entity_type: entity, entity_id: entityId }).then((r) => r.data)

export const confirmBillingPayment = (reference, transactionId) =>
  api.post('/tour-billing/confirm', { reference, transaction_id: transactionId })
    .then((r) => r.data)

export const getCreditStatus = (entity, entityId) =>
  api.get('/tour-billing/credit-status', { params: { entity_type: entity, entity_id: entityId } })
    .then((r) => r.data)

export function openWompiWidget(intent) {
  return new Promise((resolve, reject) => {
    const attach = () => {
      try {
        const checkout = new window.WidgetCheckoutCheckout({
          currency: intent.currency,
          amountInCents: String(intent.amount_in_cents),
          reference: intent.reference,
          publicKey: intent.public_key,
          integrity: intent.integrity,
          redirectUrl: `${window.location.origin}${window.location.pathname}`,
        })
        checkout.open((result) => resolve(result?.transaction || null))
      } catch (error) { reject(error) }
    }
    if (window.WidgetCheckoutCheckout) { attach(); return }
    const script = document.createElement('script')
    script.src = 'https://cdn.wompi.co/widget/js/v2.js'
    script.onload = attach
    script.onerror = () => reject(new Error('No se pudo cargar el widget de pagos'))
    document.head.appendChild(script)
  })
}
