import { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react'
import { useAuth } from './AuthContext'
import { getAccessToken } from '../utils/tokenUtils'

const SocketContext = createContext(null)

// Enabled: backend is running with ASGI (uvicorn) and django-channels
const WS_ENABLED = true

export function SocketProvider({ children }) {
  const { user } = useAuth()
  const wsRef    = useRef(null)
  const [isConnected, setIsConnected] = useState(false)
  const [latestAlert, setLatestAlert] = useState(null)
  const handlersRef = useRef({})

  const connect = useCallback(() => {
    // Guard: skip if WS not enabled or user not logged in or already open
    if (!WS_ENABLED || !user || wsRef.current?.readyState === WebSocket.OPEN) return
    const token = getAccessToken()
    if (!token) return

    const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    // Vercel does not support WebSocket proxying via vercel.json rewrites.
    // We must connect directly to the Render backend.
    // VITE_WS_URL should be set to: wss://cybershield-backend-15ro.onrender.com
    // The /ws prefix is added here, and /alerts/ is appended below.
    const rawWsBase = import.meta.env.VITE_WS_URL || 'wss://cybershield-backend-15ro.onrender.com'
    // Strip trailing slash and ensure /ws prefix exists
    const baseWsUrl = rawWsBase.replace(/\/$/, '').replace(/\/ws$/, '') + '/ws'
    const query = `?token=${encodeURIComponent(token)}`
    const wsUrl = `${baseWsUrl}/alerts/${query}`

    try {
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        setIsConnected(true)
        console.log('[CyberShield WS] Connected to live alert feed')
        // Start keepalive ping every 30s
        ws._pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: 'ping' }))
        }, 30_000)
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

      ws.onclose = (event) => {
        setIsConnected(false)
        clearInterval(ws._pingInterval)
        // Auto-reconnect after 5s only if not unauthorized (code 4001)
        if (WS_ENABLED && event.code !== 4001) {
          setTimeout(() => { if (user) connect() }, 5000)
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

  useEffect(() => {
    if (user) connect()
    return () => {
      wsRef.current?.close()
      clearInterval(wsRef.current?._pingInterval)
    }
  }, [user, connect])

  const subscribe = useCallback((id, handler) => {
    handlersRef.current[id] = handler
    return () => { delete handlersRef.current[id] }
  }, [])

  return (
    <SocketContext.Provider value={{ isConnected, latestAlert, subscribe }}>
      {children}
    </SocketContext.Provider>
  )
}

export const useSocket = () => useContext(SocketContext)
