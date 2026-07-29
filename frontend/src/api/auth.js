import api from './client'

export const login = (email, password) =>
  api.post('/auth/login', { email, password: password ?? null }).then((r) => r.data)

// Second step of staff 2FA: exchange the emailed code for tokens.
export const verifyLogin = (challengeId, code) =>
  api.post('/auth/login/verify', { challenge_id: challengeId, code }).then((r) => r.data)

export const register = (email, password, full_name) =>
  api.post('/auth/register', { email, password, full_name }).then((r) => r.data)

export const logout = () => api.post('/auth/logout')

export const getMe = () => api.get('/auth/me').then((r) => r.data)
