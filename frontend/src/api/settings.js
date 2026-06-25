import api from './client'

// Public branding (logo) read by the whole app on load.
export const getSettings = () =>
  api.get('/settings').then((r) => r.data)

// Admin-only: upload/replace the brand logo (multipart).
export const uploadLogo = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/settings/logo', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data)
}

// Admin-only: clear the logo (revert to the text wordmark).
export const deleteLogo = () =>
  api.delete('/settings/logo').then((r) => r.data)

// Admin-only: update the footer config (copy, social, legal, ally logos).
export const updateSettings = (data) =>
  api.put('/settings', data).then((r) => r.data)

// Admin-only: upload an ally logo for the footer strip; returns { url, storage_key }.
export const uploadFooterLogo = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/settings/footer-logo', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data)
}
