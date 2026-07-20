// JWT Token utility functions

const ACCESS_TOKEN_KEY  = 'cs_access_token'
const REFRESH_TOKEN_KEY = 'cs_refresh_token'

export const setTokens = (access, refresh) => {
  localStorage.setItem(ACCESS_TOKEN_KEY,  access)
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
}

export const getAccessToken  = () => localStorage.getItem(ACCESS_TOKEN_KEY)
export const getRefreshToken = () => localStorage.getItem(REFRESH_TOKEN_KEY)

export const clearTokens = () => {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

/**
 * Decode JWT payload (base64url) without verification.
 * Verification happens server-side.
 */
export const getTokenPayload = (token) => {
  if (!token) return null
  try {
    const base64Url = token.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const jsonPayload = decodeURIComponent(
      atob(base64).split('').map(c =>
        '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
      ).join('')
    )
    return JSON.parse(jsonPayload)
  } catch {
    return null
  }
}

export const isTokenExpired = (token) => {
  const payload = getTokenPayload(token)
  if (!payload?.exp) return true
  return payload.exp * 1000 < Date.now()
}
