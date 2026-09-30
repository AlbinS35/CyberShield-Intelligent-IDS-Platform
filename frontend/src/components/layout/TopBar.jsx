import { useState, useEffect, useRef } from 'react'
import { Bell, Wifi, WifiOff, X, AlertTriangle, Shield, Clock, ArrowLeft, Home } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { useQuery } from '@tanstack/react-query'
import { alertsAPI } from '../../api'
import { format } from 'date-fns'
import { clsx } from 'clsx'
import { useNavigate } from 'react-router-dom'

const SEV_STYLE = {
  CRITICAL: { cls: 'bg-red-500/15 text-red-400 border-red-500/30',    dot: 'bg-red-500' },
  HIGH:     { cls: 'bg-orange-500/15 text-orange-400 border-orange-500/30', dot: 'bg-orange-500' },
  MEDIUM:   { cls: 'bg-amber-500/15 text-amber-400 border-amber-500/30',   dot: 'bg-amber-500' },
  LOW:      { cls: 'bg-blue-500/15 text-blue-400 border-blue-500/30',      dot: 'bg-blue-400' },
}

function useRealTimeClock() {
  const [now, setNow] = useState(new Date())
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])
  return now
}

export default function TopBar({ isConnected }) {
  const { user } = useAuth()
  const now = useRealTimeClock()
  const [notifOpen, setNotifOpen] = useState(false)
  const [offlineOpen, setOfflineOpen] = useState(false)
  const [seenCount,  setSeenCount]  = useState(0)
  const notifRef  = useRef(null)
  const offlineRef = useRef(null)
  const navigate = useNavigate()

  // Fetch recent alerts for notification panel
  const { data: alertsData } = useQuery({
    queryKey: ['topbar-alerts'],
    queryFn:  () => alertsAPI.list({ page_size: 8, ordering: '-created_at' }).then(r => r.data),
    refetchInterval: 15000,
  })
  const alerts = alertsData?.results || []
  const unread = Math.max(0, alerts.length - seenCount)

  // Close dropdowns on outside click
  useEffect(() => {
    const handler = (e) => {
      if (notifRef.current  && !notifRef.current.contains(e.target))  setNotifOpen(false)
      if (offlineRef.current && !offlineRef.current.contains(e.target)) setOfflineOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleBellClick = () => {
    setNotifOpen(o => !o)
    setOfflineOpen(false)
    if (!notifOpen) setSeenCount(alerts.length)
  }

  const handleOfflineClick = () => {
    setOfflineOpen(o => !o)
    setNotifOpen(false)
  }

  return (
    <header className="h-14 shrink-0 px-6 flex items-center justify-between border-b border-cyber-cyan/10 bg-navy-950/80 backdrop-blur-sm relative z-40">

      {/* Left: Navigation and timestamp */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 border-r border-navy-700 pr-4">
          <button 
            onClick={() => navigate(-1)} 
            className="p-1.5 text-gray-400 hover:text-white hover:bg-navy-700/50 rounded transition-colors"
            title="Go Back"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <button 
            onClick={() => navigate('/')} 
            className="p-1.5 text-gray-400 hover:text-white hover:bg-navy-700/50 rounded transition-colors"
            title="Go to Home/Landing Page"
          >
            <Home className="w-4 h-4" />
          </button>
        </div>
        <span className="text-xs text-gray-500 font-mono">
          {format(now, 'dd MMM yyyy — HH:mm:ss')}
        </span>
      </div>

      {/* Right: status + bell */}
      <div className="flex items-center gap-4">

        {/* ── WebSocket / Connection Indicator ── */}
        <div className="relative" ref={offlineRef}>
          <button
            onClick={handleOfflineClick}
            title={isConnected ? 'Live WebSocket connection active' : 'WebSocket disconnected — click for info'}
            className={clsx(
              'flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border transition-all duration-200 font-mono',
              isConnected
                ? 'bg-cyber-green/8 text-cyber-green border-cyber-green/20 hover:bg-cyber-green/15'
                : 'bg-red-500/8 text-red-400 border-red-500/20 hover:bg-red-500/15 animate-pulse'
            )}
          >
            {isConnected
              ? <><Wifi className="w-3.5 h-3.5" /><span>LIVE</span></>
              : <><WifiOff className="w-3.5 h-3.5" /><span>OFFLINE</span></>
            }
          </button>

          {/* Offline info dropdown */}
          {offlineOpen && (
            <div
              className="absolute right-0 top-10 w-72 rounded-xl border border-navy-700 shadow-2xl overflow-hidden z-50"
              style={{ background: 'rgba(13,17,25,0.98)', backdropFilter: 'blur(16px)' }}
            >
              <div className="p-4 border-b border-navy-700 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {isConnected
                    ? <Wifi className="w-4 h-4 text-cyber-green" />
                    : <WifiOff className="w-4 h-4 text-red-400" />
                  }
                  <span className="text-sm font-semibold text-white">
                    WebSocket Status
                  </span>
                </div>
                <button onClick={() => setOfflineOpen(false)} className="text-gray-500 hover:text-gray-300 p-1">
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
              <div className="p-4 space-y-3">
                <div className="flex items-center gap-3">
                  <div className={clsx('w-2.5 h-2.5 rounded-full', isConnected ? 'bg-cyber-green animate-pulse' : 'bg-red-500')} />
                  <span className="text-sm text-gray-300">
                    {isConnected ? 'Connected to real-time event stream' : 'Disconnected from event stream'}
                  </span>
                </div>
                <p className="text-xs text-gray-500 leading-relaxed">
                  {isConnected
                    ? 'Live threat events and alerts are streaming via WebSocket. The dashboard auto-updates without manual refresh.'
                    : 'WebSocket connection lost. Live updates are paused. The dashboard will show cached data. Check if the Django Channels server (Daphne) is running on the backend.'
                  }
                </p>
                {!isConnected && (
                  <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 text-xs text-amber-400">
                    💡 Run: <span className="font-mono">python manage.py runserver</span> to restore the connection
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* ── Notification Bell ── */}
        <div className="relative" ref={notifRef}>
          <button
            onClick={handleBellClick}
            className="relative p-2 rounded-lg text-gray-400 hover:text-gray-100 hover:bg-navy-700/50 transition-colors"
            title={`${unread} unread alert${unread !== 1 ? 's' : ''}`}
          >
            <Bell className="w-4 h-4" />
            {unread > 0 && (
              <span className="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-red-500 border border-navy-950 text-[10px] font-bold text-white flex items-center justify-center">
                {unread > 9 ? '9+' : unread}
              </span>
            )}
          </button>

          {/* Notification Dropdown Panel */}
          {notifOpen && (
            <div
              className="absolute right-0 top-10 w-96 rounded-xl border border-navy-700 shadow-2xl overflow-hidden z-50"
              style={{ background: 'rgba(13,17,25,0.98)', backdropFilter: 'blur(16px)' }}
            >
              {/* Header */}
              <div className="flex items-center justify-between px-4 py-3 border-b border-navy-700">
                <div className="flex items-center gap-2">
                  <Bell className="w-4 h-4 text-cyber-cyan" />
                  <span className="text-sm font-semibold text-white">Recent Alerts</span>
                  {alerts.length > 0 && (
                    <span className="text-[10px] font-mono bg-cyber-cyan/10 text-cyber-cyan border border-cyber-cyan/20 px-2 py-0.5 rounded-full">
                      {alerts.length} alerts
                    </span>
                  )}
                </div>
                <button onClick={() => setNotifOpen(false)} className="text-gray-500 hover:text-gray-300 p-1">
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Alert list */}
              <div className="max-h-80 overflow-y-auto divide-y divide-navy-800">
                {alerts.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-10 text-gray-600">
                    <Shield className="w-8 h-8 mb-2 opacity-30" />
                    <p className="text-sm">No recent alerts</p>
                  </div>
                ) : (
                  alerts.map(alert => {
                    const sev = SEV_STYLE[alert.severity] || SEV_STYLE.LOW
                    return (
                      <div key={alert.id} className="px-4 py-3 hover:bg-navy-800/60 transition-colors cursor-pointer">
                        <div className="flex items-start gap-3">
                          <div className={clsx('w-2 h-2 rounded-full mt-1.5 shrink-0', sev.dot)} />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-0.5">
                              <span className={clsx('text-[10px] font-bold px-1.5 py-0.5 rounded border font-mono', sev.cls)}>
                                {alert.severity}
                              </span>
                              <span className="text-xs font-medium text-gray-200 truncate">{alert.rule_name || alert.title || 'Alert'}</span>
                            </div>
                            <p className="text-xs text-gray-500 truncate">{alert.description || alert.message || 'Threat detected'}</p>
                            <div className="flex items-center gap-1 mt-1 text-[10px] text-gray-600 font-mono">
                              <Clock className="w-2.5 h-2.5" />
                              {alert.created_at ? format(new Date(alert.created_at), 'dd MMM HH:mm:ss') : '—'}
                            </div>
                          </div>
                        </div>
                      </div>
                    )
                  })
                )}
              </div>

              {/* Footer */}
              <div className="px-4 py-3 border-t border-navy-700 flex items-center justify-between">
                <span className="text-xs text-gray-500">Auto-refreshes every 15s</span>
                <button
                  onClick={() => { setNotifOpen(false); window.location.href = '/analyst/alerts' }}
                  className="text-xs font-semibold text-cyber-cyan hover:underline"
                >
                  View all alerts →
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
