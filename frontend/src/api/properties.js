import api from './client'

export const searchProperties = (params) =>
  api.get('/properties', { params }).then((r) => r.data)

export const getProperty = (id) =>
  api.get(`/properties/${id}`).then((r) => r.data)

export const createProperty = (data) =>
  api.post('/properties', data).then((r) => r.data)

export const updateProperty = (id, data) =>
  api.put(`/properties/${id}`, data).then((r) => r.data)

export const deleteProperty = (id) =>
  api.delete(`/properties/${id}`)

export const submitProperty = (id) =>
  api.post(`/properties/${id}/submit`).then((r) => r.data)

export const approveProperty = (id) =>
  api.post(`/properties/${id}/approve`).then((r) => r.data)

export const rejectProperty = (id, reason) =>
  api.post(`/properties/${id}/reject`, { reason }).then((r) => r.data)

export const pauseProperty = (id) =>
  api.post(`/properties/${id}/pause`).then((r) => r.data)

export const reactivateProperty = (id) =>
  api.post(`/properties/${id}/reactivate`).then((r) => r.data)

export const markSold = (id) =>
  api.post(`/properties/${id}/mark-sold`).then((r) => r.data)

export const markRented = (id) =>
  api.post(`/properties/${id}/mark-rented`).then((r) => r.data)

export const duplicateProperty = (id) =>
  api.post(`/properties/${id}/duplicate`).then((r) => r.data)

export const setShowOnHome = (id, value) =>
  api.patch(`/properties/${id}/home`, { show_on_home: value }).then((r) => r.data)

export const uploadImage = (propertyId, file, role = 'gallery') => {
  const form = new FormData()
  form.append('file', file)
  return api.post(`/properties/${propertyId}/images?role=${role}`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data)
}

export const deleteImage = (propertyId, imageId) =>
  api.delete(`/properties/${propertyId}/images/${imageId}`)

export const reorderImages = (propertyId, orderedIds) =>
  api.patch(`/properties/${propertyId}/images/reorder`, { ordered_ids: orderedIds }).then((r) => r.data)

export const getFeatured = (scope = 'home') =>
  api.get('/featured', { params: { scope } }).then((r) => r.data)

export const getBanners = (position) =>
  api.get('/banners', { params: { position } }).then((r) => r.data)
