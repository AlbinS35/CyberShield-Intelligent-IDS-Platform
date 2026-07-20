import { Bell, Wifi, WifiOff, RefreshCw } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { format } from 'date-fns'

export default function TopBar({ isConnected }) {
  return (
    <header className="h-14 shrink-0 px-6 flex items-center justify-between border-b border-cyber-cyan/10 bg-navy-950/80 backdrop-blur-sm">
      <div className="flex items-center gap-2">
        <span className="text-xs text-gray-500 font-mono">
          {format(new Date(), 'dd MMM yyyy — HH:mm:ss')}
        </span>
      </div>
      <div className="flex items-center gap-4">
        {/* WebSocket connection status */}
        <div className="flex items-center gap-1.5 text-xs">
          {isConnected ? (
            <>
              <Wifi className="w-3.5 h-3.5 text-cyber-green" />
              <span className="text-cyber-green font-mono">LIVE</span>
            </>
          ) : (
            <>
              <WifiOff className="w-3.5 h-3.5 text-gray-500" />
              <span className="text-gray-500 font-mono">OFFLINE</span>
            </>
          )}
        </div>
        {/* Placeholder notification bell */}
        <button className="relative p-2 rounded-lg text-gray-400 hover:text-gray-100 hover:bg-navy-700/50 transition-colors">
          <Bell className="w-4 h-4" />
        </button>
      </div>
    </header>
  )
}
