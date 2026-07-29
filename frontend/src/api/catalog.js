import api from './client'

export const getPropertyTypes = () =>
  api.get('/property-types').then((r) => r.data)

export const getFeaturedCities = (limit = 8) =>
  api.get('/cities/featured', { params: { limit } }).then((r) => r.data)

export const getLocations = (params) =>
  api.get('/locations', { params }).then((r) => r.data)

export const createLocation = (data) =>
  api.post('/locations', data).then((r) => r.data)

// City image management (admin) — a manual cover wins over the auto-derived one.
export const getCities = () =>
  api.get('/locations', { params: { level: 'city' } }).then((r) => r.data)

export const uploadCityImage = (id, file) => {
  const form = new FormData()
  form.append('file', file)
  return api
    .post(`/locations/${id}/image/upload`, form, { headers: { 'Content-Type': 'multipart/form-data' } })
    .then((r) => r.data)
}

export const clearCityImage = (id) =>
  api.delete(`/locations/${id}/image`).then((r) => r.data)
