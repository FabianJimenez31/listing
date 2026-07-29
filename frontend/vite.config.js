import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// API target is configurable so the dev server can point at a local backend
// on any port (defaults to the conventional :8090).
const API_TARGET = process.env.VITE_API_PROXY || 'http://localhost:8090'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': API_TARGET,
      '/sitemap.xml': API_TARGET,
      '/robots.txt': API_TARGET,
    },
  },
})
