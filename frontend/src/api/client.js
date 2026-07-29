/**
 * Axios instance with auth interceptors.
 * Automatically attaches Bearer token and refreshes on 401.
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// Attach access token from localStorage
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// On 401, attempt token refresh once; on failure, clear tokens
let _refreshing = false
let _queue = []

const _processQueue = (error, token) => {
  _queue.forEach(({ resolve, reject }) => (error ? reject(error) : resolve(token)))
  _queue = []
}

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error)
    }
    const refreshToken = localStorage.getItem('refresh_token')
    if (!refreshToken) return Promise.reject(error)

    if (_refreshing) {
      return new Promise((resolve, reject) => {
        _queue.push({ resolve, reject })
      }).then((token) => {
        original.headers.Authorization = `Bearer ${token}`
        return api(original)
      })
    }

    original._retry = true
    _refreshing = true
    try {
      const { data } = await axios.post('/api/v1/auth/refresh', { refresh_token: refreshToken })
      localStorage.setItem('access_token', data.access_token)
      api.defaults.headers.common.Authorization = `Bearer ${data.access_token}`
      _processQueue(null, data.access_token)
      original.headers.Authorization = `Bearer ${data.access_token}`
      return api(original)
    } catch (err) {
      _processQueue(err, null)
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
      return Promise.reject(err)
    } finally {
      _refreshing = false
    }
  },
)

export default api
