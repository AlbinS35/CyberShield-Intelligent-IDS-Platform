import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authAPI } from '../api/auth'
import { getTokenPayload, clearTokens, setTokens, getAccessToken } from '../utils/tokenUtils'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [loading, setLoading] = useState(true)

  // Initialize from stored JWT on mount
  useEffect(() => {
    const token = getAccessToken()
    if (token) {
      const payload = getTokenPayload(token)
      if (payload && payload.exp * 1000 > Date.now()) {
        setUser({
          id:          payload.user_id,
          role:        payload.role,
          tenantId:    payload.tenant_id,
          tenantName:  payload.tenant_name,
          fullName:    payload.full_name,
        })
      } else {
        clearTokens()
      }
    }
    setLoading(false)
  }, [])

  const login = useCallback(async (email, password) => {
    const { data } = await authAPI.login(email, password)
    setTokens(data.access, data.refresh)
    const payload = getTokenPayload(data.access)
    const userData = {
      id:         payload.user_id,
      role:       payload.role,
      tenantId:   payload.tenant_id,
      tenantName: payload.tenant_name,
      fullName:   payload.full_name,
      ...data.user,
    }
    setUser(userData)
    return userData
  }, [])

  const logout = useCallback(async () => {
    try { await authAPI.logout() } catch (_) {}
    clearTokens()
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
