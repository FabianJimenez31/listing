import api from './client'

export const getModerationQueue = (params) =>
  api.get('/admin/moderation', { params }).then((r) => r.data)

export const getAdminStats = () =>
  api.get('/admin/stats').then((r) => r.data)

export const getAdminUsers = (params) =>
  api.get('/admin/users', { params }).then((r) => r.data)

export const getBanners = (params) =>
  api.get('/banners', { params }).then((r) => r.data)

export const createBanner = (data) =>
  api.post('/banners', data).then((r) => r.data)

export const deleteBanner = (id) =>
  api.delete(`/banners/${id}`)

export const getFeatured = (params) =>
  api.get('/featured', { params }).then((r) => r.data)

export const createFeatured = (data) =>
  api.post('/featured', data).then((r) => r.data)

export const deleteFeatured = (id) =>
  api.delete(`/featured/${id}`)

export const trackEvent = (eventType, propertyId, sessionHash) =>
  api.post('/metrics/event', { event_type: eventType, entity_id: propertyId, session_hash: sessionHash })
