import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  Terminal, ShieldCheck, Clock, Search, Filter,
  Activity, ArrowDownToLine, Database, ShieldAlert
} from 'lucide-react'
import { ingestionAPI, forensicsAPI } from '../../api'
import axios from '../../api/axios' // helper for executions
import { format } from 'date-fns'
import { clsx } from 'clsx'

export default function AuditTrail() {
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState('ALL') // 'ALL', 'INGESTION', 'PLAYBOOK', 'FORENSICS'

  // Fetch sync logs
  const { data: syncLogs, isLoading: syncLoading } = useQuery({
    queryKey: ['audit-sync-logs'],
    queryFn: () => ingestionAPI.syncLogs().then(r => r.data?.results || r.data || []),
  })

  // Fetch executions
  const { data: executions, isLoading: execLoading } = useQuery({
    queryKey: ['audit-executions'],
    queryFn: () => axios.get('/detection/executions/').then(r => r.data?.results || r.data || []),
  })

  // Fetch forensic cases
  const { data: casesData, isLoading: casesLoading } = useQuery({
    queryKey: ['audit-cases'],
    queryFn: () => forensicsAPI.listCases().then(r => r.data?.results || r.data || []),
  })

  const rawSyncLogs = Array.isArray(syncLogs) ? syncLogs : []
  const rawExecutions = Array.isArray(executions) ? executions : []
  const rawCases = Array.isArray(casesData) ? casesData : []

  // Normalise all logs into a single audit format
  const auditEntries = [
    ...rawSyncLogs.map(log => ({
      id: log.id,
      timestamp: new Date(log.sync_started_at),
      type: 'INGESTION',
      action: 'Wazuh Synchronization Triggered',
      description: `Wazuh telemetry ingestion task started. Fetched: ${log.alerts_fetched}, Ingested: ${log.alerts_ingested}`,
      user: 'SYSTEM (Celery Agent)',
      status: log.status
    })),
    ...rawExecutions.map(exec => ({
      id: exec.id,
      timestamp: new Date(exec.executed_at),
      type: 'PLAYBOOK',
      action: `Playbook Executed: ${exec.playbook_name}`,
      description: `Target IP: ${exec.target_ip || 'Internal System'}, Exit Code: ${exec.exit_code ?? '0'}, Dry Run: ${exec.is_dry_run ? 'Yes' : 'No'}`,
      user: exec.triggered_by_name || 'SYSTEM (Auto-Gate)',
      status: exec.status
    })),
    ...rawCases.map(c => ({
      id: c.id,
      timestamp: new Date(c.created_at),
      type: 'FORENSICS',
      action: `Forensic Case Opened: ${c.case_number}`,
      description: `Title: ${c.title}. Lead Investigator: ${c.lead_investigator_name || 'Unassigned'}`,
      user: c.lead_investigator_name || 'System Admin',
      status: c.status === 'ARCHIVED' ? 'ARCHIVED' : 'SUCCESS'
    }))
  ].sort((a, b) => b.timestamp - a.timestamp)

  // Filter & Search Logic
  const filtered = auditEntries.filter(entry => {
    const matchesSearch =
      entry.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entry.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entry.user.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesType = filterType === 'ALL' || entry.type === filterType
    return matchesSearch && matchesType
  })

  const loading = syncLoading || execLoading || casesLoading

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-white">Immutable Audit Trail</h1>
        <p className="text-sm text-gray-500 mt-0.5">Chronological record of system integrations, manual containment overrides, and forensic investigations</p>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            placeholder="Search audit trail by event description, action, or actor..."
            className="cyber-input pl-9"
          />
        </div>
        <div className="flex gap-2">
          {['ALL', 'INGESTION', 'PLAYBOOK', 'FORENSICS'].map(t => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              className={clsx(
                'px-3 py-1.5 rounded text-xs font-semibold border transition-all',
                filterType === t
                  ? 'bg-cyber-cyan/15 text-cyber-cyan border-cyber-cyan/30'
                  : 'bg-navy-800 text-gray-500 border-navy-700 hover:text-gray-300'
              )}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Audit Logs List */}
      <div className="glass-card p-0 overflow-hidden">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-navy-700 bg-navy-800/30 text-gray-500 font-medium">
              <th className="p-4">Timestamp</th>
              <th className="p-4">Action Event</th>
              <th className="p-4">System Details</th>
              <th className="p-4">Actor</th>
              <th className="p-4">Event Group</th>
              <th className="p-4 text-right">Integrity</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-navy-800/50">
            {loading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <tr key={i} className="animate-pulse">
                  <td colSpan="6" className="p-4 h-12 bg-navy-800/10" />
                </tr>
              ))
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan="6" className="p-8 text-center text-gray-600">
                  No matching audit logs found.
                </td>
              </tr>
            ) : (
              filtered.map(entry => {
                const isSuccess = entry.status === 'SUCCESS' || entry.status === 'RUNNING'
                return (
                  <tr key={entry.id} className="hover:bg-navy-800/30">
                    <td className="p-4 font-mono text-gray-500 whitespace-nowrap">
                      {format(entry.timestamp, 'yyyy-MM-dd HH:mm:ss')}
                    </td>
                    <td className="p-4">
                      <span className="font-semibold text-gray-200 block">{entry.action}</span>
                    </td>
                    <td className="p-4 text-gray-400 max-w-sm">{entry.description}</td>
                    <td className="p-4 font-semibold text-gray-300">{entry.user}</td>
                    <td className="p-4">
                      <span className={clsx(
                        'inline-flex items-center gap-1 px-2 py-0.5 rounded text-[9px] border font-bold font-mono',
                        entry.type === 'INGESTION'
                          ? 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                          : entry.type === 'PLAYBOOK'
                            ? 'bg-orange-500/10 text-orange-400 border-orange-500/20'
                            : 'bg-purple-500/10 text-purple-400 border-purple-500/20'
                      )}>
                        {entry.type}
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      <span className="inline-flex items-center gap-1 text-[10px] text-green-400">
                        <ShieldCheck className="w-3.5 h-3.5" /> Sealed
                      </span>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
