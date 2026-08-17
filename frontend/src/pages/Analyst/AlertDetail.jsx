import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ShieldAlert, Activity, CheckCircle, ArrowLeft, Clock,
  User, Play, Shield, ShieldCheck, Terminal, AlertTriangle, AlertCircle
} from 'lucide-react'
import { alertsAPI, playbooksAPI } from '../../api'
import axios from '../../api/axios' // helper for explanations
import toast from 'react-hot-toast'
import { clsx } from 'clsx'
import { format } from 'date-fns'

const SEVERITY_COLORS = {
  CRITICAL: { text: 'text-red-400 bg-red-500/10 border-red-500/20', label: 'Critical' },
  HIGH:     { text: 'text-orange-400 bg-orange-500/10 border-orange-500/20', label: 'High' },
  MEDIUM:   { text: 'text-amber-400 bg-amber-500/10 border-amber-500/20', label: 'Medium' },
  LOW:      { text: 'text-blue-400 bg-blue-500/10 border-blue-500/20', label: 'Low' },
  INFO:     { text: 'text-gray-400 bg-gray-500/10 border-gray-500/20', label: 'Info' },
}

const STATUS_LABELS = {
  NEW: 'New Alert',
  ACKNOWLEDGED: 'Acknowledged',
  IN_PROGRESS: 'In Progress',
  RESOLVED: 'Resolved',
  FALSE_POSITIVE: 'False Positive',
  ESCALATED: 'Escalated to Incident',
}

export default function AlertDetail() {
  const { id } = useParams()
  const [triggering, setTriggering] = useState(false)
  const [selectedPlaybook, setSelectedPlaybook] = useState('')

  // Query details
  const { data: alert, isLoading, refetch } = useQuery({
    queryKey: ['alert-detail', id],
    queryFn: () => alertsAPI.detail(id).then(r => r.data),
    enabled: !!id,
  })

  // Query SHAP explanation
  const { data: shapData, isLoading: shapLoading } = useQuery({
    queryKey: ['alert-explanation', id],
    queryFn: () => axios.get(`/detection/alerts/${id}/explain/`).then(r => r.data),
    enabled: !!id && alert?.status !== 'RESOLVED',
    retry: 2,
    retryDelay: 3000
  })

  // Query Playbooks (for trigger menu)
  const { data: playbooks } = useQuery({
    queryKey: ['playbooks-list-alert'],
    queryFn: () => playbooksAPI.list().then(r => r.data?.results || r.data || []),
  })

  const handleUpdateStatus = async (status) => {
    try {
      await alertsAPI.updateStatus(id, { status })
      toast.success(`Alert status marked as ${status}`)
      refetch()
    } catch {
      toast.error('Failed to update status')
    }
  }

  const handleTriggerPlaybook = async () => {
    if (!selectedPlaybook) {
      toast.error('Please select a containment playbook')
      return
    }
    setTriggering(true)
    try {
      await alertsAPI.triggerPlaybook(id, { playbook_id: selectedPlaybook })
      toast.success('Active containment playbook fired successfully')
    } catch {
      toast.error('Failed to trigger playbook')
    } finally {
      setTriggering(false)
    }
  }

  const handleEscalate = async () => {
    try {
      await alertsAPI.escalate(id, {})
      toast.success('Incident ticket spawned successfully')
      refetch()
    } catch {
      toast.error('Escalation failed')
    }
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4 text-gray-500 font-mono text-xs">
        <div className="w-8 h-8 border-2 border-cyber-cyan/30 border-t-cyber-cyan rounded-full animate-spin" />
        Resolving alert logs...
      </div>
    )
  }

  if (!alert) {
    return (
      <div className="text-center py-20 text-gray-500 font-mono text-xs space-y-4">
        <AlertCircle className="w-10 h-10 mx-auto text-cyber-red opacity-55" />
        <p>Security Alert not found or removed from workspace.</p>
        <Link to="/analyst/alerts" className="text-cyber-cyan hover:underline">&larr; Return to alert feed</Link>
      </div>
    )
  }

  const sev = SEVERITY_COLORS[alert.severity] || SEVERITY_COLORS.MEDIUM

  return (
    <div className="space-y-6 h-full flex flex-col">
      {/* Back button */}
      <div>
        <Link to="/analyst/alerts" className="inline-flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-300 transition-colors font-mono">
          <ArrowLeft className="w-3.5 h-3.5" /> Return to Alert Feed
        </Link>
      </div>

      {/* Header Panel */}
      <div className="glass-card p-6 border-navy-700/80 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="space-y-1.5 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className={clsx('inline-flex px-2 py-0.5 rounded text-[10px] font-bold border uppercase', sev.text)}>
              {sev.label}
            </span>
            <span className="inline-flex px-2 py-0.5 rounded text-[10px] font-bold border border-navy-700 bg-navy-800 text-gray-400">
              {STATUS_LABELS[alert.status]}
            </span>
            {alert.ml_confidence && (
              <span className="inline-flex px-2 py-0.5 rounded text-[10px] font-bold border border-cyber-cyan/20 bg-cyber-cyan/10 text-cyber-cyan font-mono">
                ML CONF: {(alert.ml_confidence * 100).toFixed(1)}%
              </span>
            )}
          </div>
          <h1 className="text-xl font-bold text-white leading-snug">{alert.title}</h1>
          <p className="text-xs text-gray-400 leading-relaxed max-w-2xl">{alert.description}</p>
        </div>

        {/* Action Panel */}
        <div className="flex flex-wrap gap-2 shrink-0">
          {alert.status !== 'RESOLVED' && alert.status !== 'FALSE_POSITIVE' && (
            <>
              <button
                onClick={() => handleUpdateStatus('ACKNOWLEDGED')}
                className="px-3 py-1.5 rounded text-xs font-semibold bg-navy-800 text-gray-300 border border-navy-700 hover:bg-navy-700 transition-all"
              >
                Acknowledge
              </button>
              <button
                onClick={handleEscalate}
                className="px-3 py-1.5 rounded text-xs font-semibold bg-orange-500/10 text-orange-400 border border-orange-500/20 hover:bg-orange-500/20 transition-all"
              >
                Escalate
              </button>
              <button
                onClick={() => handleUpdateStatus('RESOLVED')}
                className="btn-primary text-xs flex items-center gap-1.5"
              >
                <CheckCircle className="w-3.5 h-3.5" /> Resolve Threat
              </button>
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Core telemetry details */}
        <div className="glass-card p-5 lg:col-span-2 space-y-6">
          <h3 className="text-xs uppercase font-bold text-gray-400 flex items-center gap-1.5">
            <Activity className="w-4 h-4 text-cyber-cyan" /> Event Metadata
          </h3>
          <div className="grid grid-cols-2 gap-4 text-xs font-mono text-gray-400">
            {[
              { label: 'Source IP Address', value: alert.source_ip || '—', cls: 'text-cyber-red font-bold' },
              { label: 'Destination IP Address', value: alert.destination_ip || '—', cls: 'text-cyber-cyan' },
              { label: 'Affected Infrastructure Asset', value: alert.affected_asset || '—' },
              { label: 'Anomaly Attack Type', value: alert.attack_type || '—', cls: 'text-orange-400 font-bold' },
              { label: 'Fired Timestamp', value: alert.created_at ? format(new Date(alert.created_at), 'yyyy-MM-dd HH:mm:ss.SSS') : '—' },
              { label: 'Assignee Representative', value: alert.assigned_to_display || 'Unassigned' },
            ].map(item => (
              <div key={item.label} className="space-y-1 bg-navy-800/20 p-3 rounded border border-navy-850">
                <div className="text-[10px] text-gray-500 uppercase font-semibold">{item.label}</div>
                <div className={clsx('text-gray-200 mt-0.5', item.cls)}>{item.value}</div>
              </div>
            ))}
          </div>

          {/* Direct Playbook Containment Launcher */}
          {alert.status !== 'RESOLVED' && alert.status !== 'FALSE_POSITIVE' && (
            <div className="bg-navy-950 border border-navy-850 p-4 rounded-xl space-y-4">
              <h4 className="text-xs font-bold text-gray-200 flex items-center gap-1.5">
                <ShieldAlert className="w-4 h-4 text-cyber-red" />
                Emergency Incident Prevention Containment
              </h4>
              <p className="text-[11px] text-gray-500 leading-snug">Fire active containment scripts targeting firewall controls to immediately isolate {alert.source_ip || 'the source host'}.</p>
              <div className="flex gap-3">
                <select
                  value={selectedPlaybook}
                  onChange={e => setSelectedPlaybook(e.target.value)}
                  className="cyber-input flex-1 bg-navy-800 text-xs"
                >
                  <option value="">Choose Active Playbook...</option>
                  {playbooks?.map(pb => (
                    <option key={pb.id} value={pb.id}>{pb.name}</option>
                  ))}
                </select>
                <button
                  onClick={handleTriggerPlaybook}
                  disabled={triggering || !selectedPlaybook}
                  className="btn-primary bg-cyber-red border-red-500 hover:bg-red-600/80 text-xs flex items-center gap-1.5"
                >
                  <Play className="w-3.5 h-3.5 fill-current" /> Fire Mitigation
                </button>
              </div>
            </div>
          )}
        </div>

        {/* SHAP explainability panel */}
        <div className="glass-card p-5 space-y-4">
          <h3 className="text-xs uppercase font-bold text-gray-400 flex items-center gap-1.5">
            <Terminal className="w-4 h-4 text-cyber-cyan" />
            ML Explanation (SHAP)
          </h3>
          <p className="text-[11px] text-gray-500 leading-snug">
            SHAP (SHapley Additive exPlanations) values indicate how individual network flow features influenced the classifier prediction.
          </p>

          <div className="space-y-3">
            {shapLoading ? (
              Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="space-y-1 animate-pulse">
                  <div className="h-2 bg-navy-700 rounded w-1/3" />
                  <div className="h-6 bg-navy-800 rounded w-full" />
                </div>
              ))
            ) : !shapData?.explanation || shapData.explanation.length === 0 ? (
              <div className="text-center py-8 text-[11px] text-gray-600 italic">
                SHAP explanation stats not generated.
              </div>
            ) : (
              shapData.explanation.map(feat => {
                const isRisk = feat.direction === 'increases_risk'
                const pct = Math.min(Math.max(Math.abs(feat.shap_value) * 100, 5), 100)
                return (
                  <div key={feat.feature} className="space-y-1">
                    <div className="flex justify-between text-[10px] font-mono">
                      <span className="text-gray-400">{feat.feature}</span>
                      <span className={clsx(isRisk ? 'text-cyber-red' : 'text-green-400')}>
                        {feat.value} ({isRisk ? '+' : '-'}{Math.abs(feat.shap_value).toFixed(2)})
                      </span>
                    </div>
                    <div className="w-full bg-navy-900 rounded-full h-1.5 overflow-hidden border border-navy-850">
                      <div
                        className={clsx('h-full rounded-full', isRisk ? 'bg-cyber-red' : 'bg-green-400')}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
