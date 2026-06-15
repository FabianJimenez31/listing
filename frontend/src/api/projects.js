import api from './client'

export const searchProjects = (params) =>
  api.get('/projects', { params }).then((r) => r.data)

export const getProject = (slug) =>
  api.get(`/projects/${slug}`).then((r) => r.data)

export const createProject = (data) =>
  api.post('/projects', data).then((r) => r.data)

export const updateProject = (id, data) =>
  api.put(`/projects/${id}`, data).then((r) => r.data)

export const deleteProject = (id) =>
  api.delete(`/projects/${id}`)

export const submitProject = (id) =>
  api.post(`/projects/${id}/submit`).then((r) => r.data)

export const approveProject = (id) =>
  api.post(`/projects/${id}/approve`).then((r) => r.data)

export const getProjectImages = (id) =>
  api.get(`/projects/${id}/images`).then((r) => r.data)

export const addProjectImage = (id, data) =>
  api.post(`/projects/${id}/images`, data).then((r) => r.data)

export const uploadProjectImage = (id, file, role = 'gallery') => {
  const form = new FormData()
  form.append('file', file)
  return api
    .post(`/projects/${id}/images/upload?role=${role}`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((r) => r.data)
}

export const deleteProjectImage = (id, imageId) =>
  api.delete(`/projects/${id}/images/${imageId}`)
