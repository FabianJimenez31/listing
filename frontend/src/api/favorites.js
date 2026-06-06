import api from './client'

export const getFavorites = (params) =>
  api.get('/favorites', { params }).then((r) => r.data)

export const addFavorite = (propertyId) =>
  api.post('/favorites', { property_id: propertyId }).then((r) => r.data)

export const removeFavorite = (propertyId) =>
  api.delete(`/favorites/${propertyId}`)
