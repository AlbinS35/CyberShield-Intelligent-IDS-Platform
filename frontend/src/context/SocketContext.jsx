import { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react'
import { useAuth } from './AuthContext'
import { getAccessToken } from '../utils/tokenUtils'

const SocketContext = createContext(null)

export function SocketProvider({ children }) {
  const { user } = useAuth()
  const wsRef    = useRef(null)
  const [isConnected, setIsConnected] = useState(false)
  const [latestAlert, setLatestAlert] = useState(null)
  const handlersRef = useRef({})

  const connect = useCallback(() => {
    if (!user || wsRef.current?.readyState === WebSocket.OPEN) return
    const token = getAccessToken()
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/alerts/?token=${token}`
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
      const data = JSON.parse(event.data)
      if (data.type === 'alert.new') {
        setLatestAlert(data.alert)
        Object.values(handlersRef.current).forEach(fn => fn(data.alert))
      }
    }

    ws.onclose = () => {
      setIsConnected(false)
      clearInterval(ws._pingInterval)
      // Auto-reconnect after 5s if user still logged in
      setTimeout(() => { if (user) connect() }, 5000)
    }

    ws.onerror = (err) => console.error('[CyberShield WS] Error:', err)
    wsRef.current = ws
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
