import api from './client'

export const getPartners = () =>
  api.get('/partners').then((r) => r.data)

export const createPartner = (data) =>
  api.post('/partners', data).then((r) => r.data)

export const deletePartner = (id) =>
  api.delete(`/partners/${id}`)
