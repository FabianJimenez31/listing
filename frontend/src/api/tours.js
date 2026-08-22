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
