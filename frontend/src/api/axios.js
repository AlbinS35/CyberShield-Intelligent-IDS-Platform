import axios from 'axios'

// Base Axios instance pointing to Django backend
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  headers: { 'Content-Type': 'application/json' },
  timeout: 15_000,
  withCredentials: true, // Crucial: automatically sends/receives httpOnly secure cookies
})

// ── Response Interceptor: Auto-refresh on 401 ────────────────────────────
let isRefreshing = false
let failedQueue  = []

const processQueue = (error) => {
  failedQueue.forEach(prom => error ? prom.reject(error) : prom.resolve())
  failedQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Guard: Prevent intercepting Auth requests (login/refresh) to avoid recursion loop
    const isAuthRequest = originalRequest.url.includes('/auth/refresh/') || originalRequest.url.includes('/auth/login/') || originalRequest.url.includes('/auth/password-reset/')

    // Intercept 401 Unauthorized for expired access token
    if (error.response?.status === 401 && !originalRequest._retry && !isAuthRequest) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(() => {
          return api(originalRequest)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        // Post a request to refresh — cookies are sent and new ones set automatically by backend
        await axios.post('/api/auth/refresh/', {}, { withCredentials: true })
        processQueue(null)
        return api(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError)
        // Session completely expired — redirect to login only if accessing private routes
        const publicRoutes = ['/', '/login', '/signup', '/register', '/forgot-password', '/reset-password']
        if (!publicRoutes.includes(window.location.pathname)) {
          window.location.href = '/login'
        }
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }
    return Promise.reject(error)
  }
)

export default api
