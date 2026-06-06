import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { login as apiLogin, logout as apiLogout, getMe } from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // Restore session on mount
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) { setLoading(false); return }
    getMe()
      .then(setUser)
      .catch(() => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
      })
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email, password) => {
    const data = await apiLogin(email, password)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    const me = await getMe()
    setUser(me)
    return me
  }, [])

  const logout = useCallback(async () => {
    try { await apiLogout() } catch (_) { /* ignore */ }
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setUser(null)
  }, [])

  const hasPermission = useCallback((code) => {
    if (!user) return false
    return user.permissions?.includes(code) ?? false
  }, [user])

  const isAdmin = useCallback(() =>
    hasPermission('property:moderate'), [hasPermission])

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, hasPermission, isAdmin }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
