import { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react'
import { useAuth } from './AuthContext'
import { getAccessToken, getRefreshToken, setTokens, isTokenExpired } from '../utils/tokenUtils'
import { authAPI } from '../api'

const SocketContext = createContext(null)

// Enabled: backend is running with ASGI (uvicorn) and django-channels
const WS_ENABLED = true

export function SocketProvider({ children }) {
  const { user } = useAuth()
  const wsRef    = useRef(null)
  const reconnectTimeoutRef = useRef(null)
  const [isConnected, setIsConnected] = useState(false)
  const [latestAlert, setLatestAlert] = useState(null)
  const handlersRef = useRef({})

  const connect = useCallback(async () => {
    // Guard: skip if WS not enabled or user not logged in or already connected
    if (!WS_ENABLED || !user || wsRef.current?.readyState === WebSocket.OPEN) return

    let token = getAccessToken()
    if (!token || isTokenExpired(token)) {
      try {
        const refresh = getRefreshToken()
        const res = await authAPI.refresh(refresh)
        if (res.data?.access) {
          setTokens(res.data.access, res.data.refresh || refresh)
          token = res.data.access
        }
      } catch (err) {
        console.warn('[CyberShield WS] Token refresh failed before connect:', err)
      }
    }

    const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    const defaultWsHost = isLocalhost ? `${wsProto}//${window.location.hostname}:8000` : 'wss://cybershield-backend-15ro.onrender.com'
    const rawWsBase = import.meta.env.VITE_WS_URL || defaultWsHost
    const baseWsUrl = rawWsBase.replace(/\/$/, '').replace(/\/ws$/, '') + '/ws'
    const query = token ? `?token=${encodeURIComponent(token)}` : ''
    const wsUrl = `${baseWsUrl}/alerts/${query}`

    try {
      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.close()
      }

      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        setIsConnected(true)
        console.log('[CyberShield WS] Connected to live alert feed')
        // Start keepalive ping every 25s
        ws._pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: 'ping' }))
        }, 25_000)
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'alert.new') {
            setLatestAlert(data.alert)
            Object.values(handlersRef.current).forEach(fn => fn(data.alert))
          }
        } catch (e) {
          console.error('[CyberShield WS] Parse error:', e)
        }
      }

      ws.onclose = async (event) => {
        setIsConnected(false)
        clearInterval(ws._pingInterval)

        // If closed due to token expiry or auth error (code 4001)
        if (event.code === 4001) {
          console.warn('[CyberShield WS] Unauthorized (4001). Refreshing token and reconnecting...')
          try {
            const refresh = getRefreshToken()
            const res = await authAPI.refresh(refresh)
            if (res.data?.access) {
              setTokens(res.data.access, res.data.refresh || refresh)
              clearTimeout(reconnectTimeoutRef.current)
              reconnectTimeoutRef.current = setTimeout(() => { if (user) connect() }, 1000)
              return
            }
          } catch (e) {
            console.error('[CyberShield WS] Re-auth refresh failed:', e)
          }
        }

        // Automatic retry after 4s
        if (WS_ENABLED && user) {
          clearTimeout(reconnectTimeoutRef.current)
          reconnectTimeoutRef.current = setTimeout(() => { if (user) connect() }, 4000)
        }
      }

      ws.onerror = (err) => {
        console.warn('[CyberShield WS] Notice:', err)
      }
      wsRef.current = ws
    } catch (err) {
      console.warn('[CyberShield WS] Connection error:', err)
    }
  }, [user])

  const reconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
    }
    connect()
  }, [connect])

  useEffect(() => {
    if (user) connect()
    return () => {
      clearTimeout(reconnectTimeoutRef.current)
      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.close()
      }
      clearInterval(wsRef.current?._pingInterval)
    }
  }, [user, connect])

  const subscribe = useCallback((id, handler) => {
    handlersRef.current[id] = handler
    return () => { delete handlersRef.current[id] }
  }, [])

  return (
    <SocketContext.Provider value={{ isConnected, latestAlert, subscribe, reconnect }}>
      {children}
    </SocketContext.Provider>
  )
}

export const useSocket = () => useContext(SocketContext)
