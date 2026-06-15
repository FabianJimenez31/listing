import api from './client'

export const getPosts = (params) =>
  api.get('/posts', { params }).then((r) => r.data)

export const getPost = (slug) =>
  api.get(`/posts/${slug}`).then((r) => r.data)

export const createPost = (data) =>
  api.post('/posts', data).then((r) => r.data)

export const updatePost = (id, data) =>
  api.put(`/posts/${id}`, data).then((r) => r.data)

export const deletePost = (id) =>
  api.delete(`/posts/${id}`)
