import api from './client'

export const getPropertyTypes = () =>
  api.get('/property-types').then((r) => r.data)

export const getFeaturedCities = (limit = 8) =>
  api.get('/cities/featured', { params: { limit } }).then((r) => r.data)

export const getLocations = (params) =>
  api.get('/locations', { params }).then((r) => r.data)
