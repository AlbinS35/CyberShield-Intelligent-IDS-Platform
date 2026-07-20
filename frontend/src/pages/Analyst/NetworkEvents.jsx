import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Search, Filter, Shield, AlertTriangle, CheckCircle, RefreshCw } from 'lucide-react'
import { networkEventsAPI, ingestionAPI } from '../../api'
import { format } from 'date-fns'
import toast from 'react-hot-toast'
import { clsx } from 'clsx'

const PROTOCOL_COLORS = {
  TCP: 'text-blue-400', UDP: 'text-purple-400', ICMP: 'text-amber-400',
  HTTP: 'text-cyan-400', HTTPS: 'text-green-400', DNS: 'text-pink-400',
  UNKNOWN: 'text-gray-500',
}

const CLASS_BADGES = {
  NORMAL: { cls: 'bg-green-500/10 text-green-400 border-green-500/20', label: 'Normal' },
  DOS:    { cls: 'bg-red-500/10 text-red-400 border-red-500/20',       label: 'DoS' },
  PROBE:  { cls: 'bg-amber-500/10 text-amber-400 border-amber-500/20', label: 'Probe' },
  R2L:    { cls: 'bg-orange-500/10 text-orange-400 border-orange-500/20', label: 'R2L' },
  U2R:    { cls: 'bg-purple-500/10 text-purple-400 border-purple-500/20', label: 'U2R' },
}

export default function NetworkEvents() {
  const [search,   setSearch]   = useState('')
  const [isThreat, setIsThreat] = useState('')
  const [page,     setPage]     = useState(1)
  const [syncing,  setSyncing]  = useState(false)

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['network-events', page, search, isThreat],
    queryFn: () => networkEventsAPI.list({
      page,
      search:    search || undefined,
      is_threat: isThreat !== '' ? isThreat : undefined,
      page_size: 20,
    }).then(r => r.data),
    keepPreviousData: true,
  })

  const handleSync = async () => {
    setSyncing(true)
    try {
      await ingestionAPI.syncWazuh()
      toast.success('Wazuh sync task queued successfully.')
      setTimeout(() => refetch(), 3000)
    } catch {
      toast.error('Wazuh sync failed. Check your Wazuh configuration.')
    } finally {
      setSyncing(false)
    }
  }

  const events = data?.results || []
  const count  = data?.count   || 0

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Network Events</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {count.toLocaleString()} total ingested events
          </p>
        </div>
        <button onClick={handleSync} disabled={syncing} className="btn-primary flex items-center gap-2">
          <RefreshCw className={clsx('w-4 h-4', syncing && 'animate-spin')} />
          {syncing ? 'Syncing...' : 'Sync Wazuh'}
        </button>
      </div>

      {/* Filters */}
      <div className="glass-card p-4 flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1) }}
            placeholder="Search IP addresses, hostnames..."
            className="cyber-input pl-9"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500 shrink-0" />
          <select
            value={isThreat}
            onChange={e => { setIsThreat(e.target.value); setPage(1) }}
            className="cyber-input w-40 bg-navy-800"
          >
            <option value="">All Events</option>
            <option value="true">Threats Only</option>
            <option value="false">Clean Traffic</option>
          </select>
        </div>
      </div>

      {/* Events Table */}
      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-cyber-cyan/10">
                {['Source IP', 'Destination IP', 'Protocol', 'Classification', 'Confidence', 'Agent', 'Timestamp', 'Integrity'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-navy-700/50">
              {isLoading ? (
                Array.from({ length: 10 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 8 }).map((_, j) => (
                      <td key={j} className="px-4 py-3">
                        <div className="h-3 bg-navy-700 rounded animate-pulse" style={{ width: `${40 + j * 10}%` }} />
                      </td>
                    ))}
                  </tr>
                ))
              ) : events.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-16 text-center text-gray-600">
                    <Shield className="w-8 h-8 mx-auto mb-2 opacity-30" />
                    <p>No network events found.</p>
                  </td>
                </tr>
              ) : (
                events.map((event, idx) => {
                  const cls = event.ml_classification
                  const badge = CLASS_BADGES[cls] || { cls: 'bg-gray-500/10 text-gray-400 border-gray-500/20', label: cls || '—' }
                  return (
                    <motion.tr
                      key={event.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: idx * 0.02 }}
                      className="hover:bg-navy-700/30 transition-colors"
                    >
                      <td className="px-4 py-3 font-mono text-xs text-gray-300">{event.source_ip || '—'}</td>
                      <td className="px-4 py-3 font-mono text-xs text-gray-300">{event.destination_ip || '—'}</td>
                      <td className={clsx('px-4 py-3 font-mono text-xs font-semibold', PROTOCOL_COLORS[event.protocol] || 'text-gray-500')}>
                        {event.protocol}
                      </td>
                      <td className="px-4 py-3">
                        <span className={clsx('inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold border', badge.cls)}>
                          {badge.label}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-gray-400">
                        {event.ml_confidence != null ? `${(event.ml_confidence * 100).toFixed(1)}%` : '—'}
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-400 max-w-[140px] truncate">{event.agent_hostname || '—'}</td>
                      <td className="px-4 py-3 text-xs text-gray-500 font-mono whitespace-nowrap">
                        {format(new Date(event.event_timestamp), 'dd/MM HH:mm:ss')}
                      </td>
                      <td className="px-4 py-3">
                        {event.log_hash ? (
                          <span className="inline-flex items-center gap-1 text-[10px] text-green-400">
                            <CheckCircle className="w-3 h-3" /> SHA-256
                          </span>
                        ) : (
                          <AlertTriangle className="w-3 h-3 text-amber-400" />
                        )}
                      </td>
                    </motion.tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {count > 20 && (
          <div className="px-4 py-3 border-t border-cyber-cyan/10 flex items-center justify-between">
            <span className="text-xs text-gray-500">
              Showing {((page - 1) * 20) + 1}–{Math.min(page * 20, count)} of {count.toLocaleString()}
            </span>
            <div className="flex items-center gap-2">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="btn-ghost text-xs py-1 px-2">
                ← Previous
              </button>
              <span className="text-xs text-gray-400 font-mono">Page {page}</span>
              <button onClick={() => setPage(p => p + 1)} disabled={page * 20 >= count} className="btn-ghost text-xs py-1 px-2">
                Next →
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
