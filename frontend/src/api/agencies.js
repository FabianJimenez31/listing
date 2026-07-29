import api from './client'

export const getAgencies = () =>
  api.get('/agencies').then((r) => r.data)

export const getAgency = (slug) =>
  api.get(`/agencies/${slug}`).then((r) => r.data)

export const createAgency = (data) =>
  api.post('/agencies', data).then((r) => r.data)

export const updateAgency = (id, data) =>
  api.put(`/agencies/${id}`, data).then((r) => r.data)

export const deleteAgency = (id) =>
  api.delete(`/agencies/${id}`)
