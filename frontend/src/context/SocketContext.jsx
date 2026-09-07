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
    const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const query = token ? `?token=${encodeURIComponent(token)}` : ''
    const wsUrl = `${wsProto}//${window.location.host}/ws/alerts/${query}`

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

      ws.onclose = () => {
        setIsConnected(false)
        clearInterval(ws._pingInterval)
        // Auto-reconnect after 5s
        if (WS_ENABLED) setTimeout(() => { if (user) connect() }, 5000)
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
