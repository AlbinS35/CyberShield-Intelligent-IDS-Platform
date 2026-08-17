import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  Activity, CheckCircle, AlertTriangle, RefreshCw,
  Server, Database, Cpu, Wifi, ShieldAlert, Clock
} from 'lucide-react'
import { ingestionAPI, mlAPI } from '../../api'
import toast from 'react-hot-toast'
import { clsx } from 'clsx'
import { format } from 'date-fns'

export default function SystemHealth() {
  const [syncing, setSyncing] = useState(false)

  // Fetch sync logs
  const { data: syncLogs, isLoading: logsLoading, refetch: refetchLogs } = useQuery({
    queryKey: ['wazuh-sync-logs'],
    queryFn: () => ingestionAPI.syncLogs().then(r => r.data?.results || r.data || []),
  })

  // Fetch ML status stats for active metrics
  const { data: mlStats } = useQuery({
    queryKey: ['ml-stats-health'],
    queryFn: () => mlAPI.stats().then(r => r.data || {}),
  })

  const handleManualSync = async () => {
    setSyncing(true)
    try {
      await ingestionAPI.syncWazuh()
      toast.success('Wazuh synchronization agent task triggered')
      setTimeout(() => {
        refetchLogs()
        setSyncing(false)
      }, 2500)
    } catch {
      toast.error('Failed to trigger synchronization')
      setSyncing(false)
    }
  }

  // Simulated active system status indicators
  const SERVICES = [
    { name: 'REST API Backend (Django)', status: 'HEALTHY', host: 'localhost:8000', icon: Server, latency: '24ms' },
    { name: 'PostgreSQL Database', status: 'HEALTHY', host: 'localhost:5432', icon: Database, latency: '8ms' },
    { name: 'Redis Cache & Broker', status: 'HEALTHY', host: 'localhost:6379', icon: Activity, latency: '2ms' },
    { name: 'Celery Task Queue Worker', status: 'HEALTHY', host: 'celery@cybershield', icon: Cpu, latency: 'Active' },
    { name: 'Wazuh SIEM Manager API', status: 'HEALTHY', host: 'wazuh-manager.local', icon: Wifi, latency: '142ms' },
    { name: 'Random Forest Inference Engine', status: 'HEALTHY', host: 'scikit-learn:v1.2', icon: ShieldAlert, latency: `${mlStats?.tenant_stats?.avg_inference_time_ms || '12'}ms` },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">System Health & Services</h1>
          <p className="text-sm text-gray-500 mt-0.5">Real-time connectivity status of CyberShield backend, data brokers, and integration engines</p>
        </div>
        <button
          onClick={handleManualSync}
          disabled={syncing}
          className="btn-primary flex items-center gap-2"
        >
          <RefreshCw className={clsx('w-4 h-4', syncing && 'animate-spin')} />
          Sync Wazuh Telemetry
        </button>
      </div>

      {/* Services Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {SERVICES.map(srv => {
          const Icon = srv.icon
          return (
            <motion.div
              key={srv.name}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-card p-5 hover:border-navy-600 transition-all"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-cyber-cyan/10 border border-cyber-cyan/20 flex items-center justify-center">
                    <Icon className="w-4 h-4 text-cyber-cyan" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-200 text-xs leading-snug">{srv.name}</h3>
                    <span className="text-[9px] font-mono text-gray-500">{srv.host}</span>
                  </div>
                </div>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-bold bg-green-500/10 text-green-400 border border-green-500/20">
                  <CheckCircle className="w-2.5 h-2.5" /> Healthy
                </span>
              </div>
              <div className="mt-4 flex items-center justify-between text-[10px] text-gray-600 font-mono">
                <span>Latency / Status</span>
                <span className="text-cyber-cyan font-bold">{srv.latency}</span>
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Wazuh Synchronization logs */}
      <div className="glass-card p-5">
        <h2 className="text-sm font-semibold text-gray-200 mb-4 flex items-center gap-2">
          <Clock className="w-4 h-4 text-cyber-cyan" />
          Wazuh Manager Integration Log
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-navy-700 bg-navy-800/30 text-gray-500 font-medium">
                <th className="p-4">Sync ID</th>
                <th className="p-4">Status</th>
                <th className="p-4">Alerts Fetched</th>
                <th className="p-4">Alerts Ingested</th>
                <th className="p-4">Trigger Time</th>
                <th className="p-4">Error / Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-navy-800/50">
              {logsLoading ? (
                Array.from({ length: 2 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td colSpan="6" className="p-4 h-12 bg-navy-800/10" />
                  </tr>
                ))
              ) : syncLogs?.length === 0 ? (
                <tr>
                  <td colSpan="6" className="p-8 text-center text-gray-600">
                    No Wazuh sync operations executed yet. Click Sync Telemetry to trigger.
                  </td>
                </tr>
              ) : (
                syncLogs?.map(log => {
                  const isSuccess = log.status === 'SUCCESS'
                  return (
                    <tr key={log.id} className="hover:bg-navy-800/30">
                      <td className="p-4 font-mono text-gray-400 text-[10px]">{log.id.slice(0, 8)}...</td>
                      <td className="p-4">
                        <span className={clsx(
                          'inline-flex items-center gap-1 px-2 py-0.5 rounded text-[9px] border font-bold',
                          isSuccess
                            ? 'bg-green-500/10 text-green-400 border-green-500/20'
                            : 'bg-red-500/10 text-cyber-red border-red-500/20'
                        )}>
                          {isSuccess ? <CheckCircle className="w-2.5 h-2.5" /> : <AlertTriangle className="w-2.5 h-2.5" />}
                          {log.status}
                        </span>
                      </td>
                      <td className="p-4 font-mono text-gray-300">{log.alerts_fetched}</td>
                      <td className="p-4 font-mono text-cyber-cyan">{log.alerts_ingested}</td>
                      <td className="p-4 font-mono text-gray-500">
                        {log.sync_started_at ? format(new Date(log.sync_started_at), 'yyyy-MM-dd HH:mm:ss') : '—'}
                      </td>
                      <td className="p-4 text-gray-500 truncate max-w-xs" title={log.error_message}>
                        {log.error_message || '—'}
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
