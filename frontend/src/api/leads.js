import api from './client'

export const createLead = (data) =>
  api.post('/leads', data).then((r) => r.data)

export const getLeads = (params) =>
  api.get('/leads', { params }).then((r) => r.data)

export const updateLead = (id, data) =>
  api.patch(`/leads/${id}`, data).then((r) => r.data)
