import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authAPI } from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [loading, setLoading] = useState(true)

  // Initialize from session cookie by fetching user profile on mount
  useEffect(() => {
    const initAuth = async () => {
      try {
        const { data } = await authAPI.me()
        setUser({
          id:          data.id,
          role:        data.role,
          tenantId:    data.tenant?.id,
          tenantName:  data.tenant?.name,
          fullName:    data.full_name,
        })
      } catch (err) {
        setUser(null)
      } finally {
        setLoading(false)
      }
    }
    initAuth()
  }, [])

  const login = useCallback(async (email, password) => {
    const { data } = await authAPI.login(email, password)
    const userData = {
      id:         data.user.id,
      role:       data.user.role,
      tenantId:   data.user.tenant?.id,
      tenantName: data.user.tenant?.name,
      fullName:   data.user.full_name,
    }
    setUser(userData)
    return userData
  }, [])

  // Google OAuth login — sends Google credential to backend
  const loginWithGoogle = useCallback(async (googleCredential) => {
    const { data } = await authAPI.googleLogin(googleCredential)
    const userData = {
      id:         data.user.id,
      role:       data.user.role,
      tenantId:   data.user.tenant?.id,
      tenantName: data.user.tenant?.name,
      fullName:   data.user.full_name,
    }
    setUser(userData)
    return userData
  }, [])

  const logout = useCallback(async () => {
    try { await authAPI.logout() } catch (_) {}
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, loginWithGoogle, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
