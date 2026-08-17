import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { forensicsAPI, playbooksAPI, blocklistAPI } from '../../api'
import { format } from 'date-fns'
import { clsx } from 'clsx'
import toast from 'react-hot-toast'
import {
  Clock, ArrowLeft, Shield, AlertTriangle, Lock,
  Fingerprint, FileText, Activity, Server, User,
  CheckCircle2, XCircle, ChevronRight, Play, ShieldAlert
} from 'lucide-react'

const EVENT_TYPE_CONFIG = {
  ALERT_CREATED:     { color: '#FF3366', icon: AlertTriangle, label: 'Alert Created' },
  ALERT_ESCALATED:   { color: '#FF8C42', icon: AlertTriangle, label: 'Alert Escalated' },
  CASE_OPENED:       { color: '#00F5FF', icon: Fingerprint,   label: 'Case Opened' },
  EVIDENCE_UPLOADED: { color: '#00E676', icon: FileText,      label: 'Evidence Uploaded' },
  EVIDENCE_VERIFIED: { color: '#00E676', icon: CheckCircle2,  label: 'Evidence Verified' },
  IP_BLOCKED:        { color: '#FFB800', icon: Shield,        label: 'IP Blocked' },
  PLAYBOOK_FIRED:    { color: '#FFB800', icon: Activity,      label: 'Playbook Fired' },
  CASE_CLOSED:       { color: '#C084FC', icon: Lock,          label: 'Case Closed' },
  LOG_SEALED:        { color: '#00E676', icon: Lock,          label: 'Log Hash Sealed' },
  NOTE_ADDED:        { color: '#9CA3AF', icon: FileText,      label: 'Note Added' },
}

function TimelineItem({ event, index, total, playbooks = [] }) {
  const cfg = EVENT_TYPE_CONFIG[event.event_type] || {
    color: '#9CA3AF', icon: Activity, label: event.event_type || 'Event'
  }
  const Icon = cfg.icon
  const isLast = index === total - 1

  const [showResponseControls, setShowResponseControls] = useState(false)
  const [selectedPlaybookId, setSelectedPlaybookId] = useState('')
  const [executing, setExecuting] = useState(false)
  const [blocking, setBlocking] = useState(false)

  const handleBlockIP = async () => {
    setBlocking(true)
    try {
      await blocklistAPI.add({ ip_address: event.ip_address, reason: `Containment initiated via Forensic Case timeline.` })
      toast.success(`IP ${event.ip_address} has been successfully added to the blocklist!`)
    } catch (e) {
      toast.error(`Failed to block IP: ${e?.response?.data?.detail || e.message}`)
    } finally {
      setBlocking(false)
    }
  }

  const handleRunPlaybook = async () => {
    if (!selectedPlaybookId) {
      toast.error('Please select a containment playbook.')
      return
    }
    setExecuting(true)
    try {
      await playbooksAPI.execute(selectedPlaybookId, event.ip_address)
      toast.success('Containment playbook execution task has been successfully queued!')
    } catch (e) {
      toast.error(`Failed to execute playbook: ${e?.response?.data?.detail || e.message}`)
    } finally {
      setExecuting(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: -16 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.04 }}
      className="flex gap-4"
    >
      {/* Timeline spine */}
      <div className="flex flex-col items-center shrink-0">
        <div
          className="w-9 h-9 rounded-full flex items-center justify-center border-2 z-10"
          style={{ background: `${cfg.color}18`, borderColor: `${cfg.color}55` }}
        >
          <Icon className="w-4 h-4" style={{ color: cfg.color }} />
        </div>
        {!isLast && <div className="flex-1 w-px bg-navy-700 mt-1" />}
      </div>

      {/* Event card */}
      <div className={clsx('glass-card p-4 flex-1 mb-4', isLast ? 'mb-0' : '')}>
        <div className="flex items-start justify-between gap-3 mb-2">
          <div>
            <span
              className="text-xs font-bold font-mono px-2 py-0.5 rounded border"
              style={{ color: cfg.color, background: `${cfg.color}14`, borderColor: `${cfg.color}33` }}
            >
              {cfg.label}
            </span>
            {event.title && (
              <h3 className="text-sm font-semibold text-gray-100 mt-1.5">{event.title}</h3>
            )}
          </div>
          <div className="flex items-center gap-1.5 text-[10px] text-gray-550 font-mono shrink-0 mt-0.5">
            <Clock className="w-2.5 h-2.5" />
            {event.created_at
              ? format(new Date(event.created_at), 'dd MMM yyyy · HH:mm:ss')
              : '—'
            }
          </div>
        </div>

        {event.description && (
          <p className="text-xs text-gray-400 leading-relaxed mb-3">{event.description}</p>
        )}

        {/* Metadata pills */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap gap-2">
            {event.actor_name && (
              <span className="inline-flex items-center gap-1.5 text-[10px] text-gray-550 bg-navy-800 border border-navy-700 px-2 py-1 rounded font-mono">
                <User className="w-2.5 h-2.5" /> {event.actor_name}
              </span>
            )}
            {event.ip_address && (
              <span className="inline-flex items-center gap-1.5 text-[10px] text-cyber-cyan bg-cyber-cyan/8 border border-cyber-cyan/20 px-2 py-1 rounded font-mono">
                <Server className="w-2.5 h-2.5" /> {event.ip_address}
              </span>
            )}
            {event.hash && (
              <span className="inline-flex items-center gap-1.5 text-[10px] text-cyber-green bg-cyber-green/8 border border-cyber-green/20 px-2 py-1 rounded font-mono">
                <Lock className="w-2.5 h-2.5" /> SHA-256: {event.hash.slice(0, 16)}…
              </span>
            )}
            {event.evidence_file && (
              <span className="inline-flex items-center gap-1.5 text-[10px] text-gray-400 bg-navy-800 border border-navy-700 px-2 py-1 rounded font-mono">
                <FileText className="w-2.5 h-2.5" /> {event.evidence_file}
              </span>
            )}
          </div>

          {event.ip_address && (
            <button
              onClick={() => setShowResponseControls(!showResponseControls)}
              className="text-[10px] font-bold text-cyber-cyan bg-cyber-cyan/10 hover:bg-cyber-cyan/20 border border-cyber-cyan/20 px-2.5 py-1 rounded transition-all flex items-center gap-1"
            >
              <ShieldAlert className="w-3.5 h-3.5" /> Containment Actions
            </button>
          )}
        </div>

        {/* Containment controls panel */}
        {showResponseControls && event.ip_address && (
          <div className="mt-4 p-4 border border-navy-700/85 bg-navy-950/60 rounded-xl space-y-4">
            <h4 className="text-[11px] font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5 text-cyber-red animate-pulse" />
              Active Threat Mitigation
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Block IP control */}
              <div className="bg-navy-900/40 p-3 rounded-lg border border-navy-800 flex flex-col justify-between">
                <div>
                  <h5 className="text-[11px] font-semibold text-gray-300">Containment Blocklist</h5>
                  <p className="text-[10px] text-gray-500 mt-1 leading-relaxed">
                    Instantly block all inbound and outbound traffic to/from {event.ip_address} across the cluster network.
                  </p>
                </div>
                <button
                  onClick={handleBlockIP}
                  disabled={blocking}
                  className="btn-danger w-full text-[10px] py-1.5 mt-3 font-bold flex items-center justify-center gap-1.5"
                >
                  <Lock className="w-3 h-3" /> {blocking ? 'Blocking...' : 'Block IP Address'}
                </button>
              </div>

              {/* Run playbook control */}
              <div className="bg-navy-900/40 p-3 rounded-lg border border-navy-800 space-y-3">
                <div>
                  <h5 className="text-[11px] font-semibold text-gray-300">Execute Containment Playbook</h5>
                  <p className="text-[10px] text-gray-500 mt-1 leading-relaxed">
                    Trigger automation commands against target IP to isolate the asset or snapshot host system files.
                  </p>
                </div>
                <div className="space-y-2">
                  <select
                    value={selectedPlaybookId}
                    onChange={e => setSelectedPlaybookId(e.target.value)}
                    className="cyber-input w-full text-[10px] py-1 bg-navy-800"
                  >
                    <option value="">Select containment playbook...</option>
                    {playbooks.map(p => (
                      <option key={p.id} value={p.id}>{p.name} ({p.trigger_mode})</option>
                    ))}
                  </select>
                  <button
                    onClick={handleRunPlaybook}
                    disabled={executing || !selectedPlaybookId}
                    className="btn-primary w-full text-[10px] py-1.5 font-bold flex items-center justify-center gap-1.5"
                  >
                    <Play className="w-3 h-3" /> {executing ? 'Executing...' : 'Run Containment'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </motion.div>
  )
}

export default function ForensicTimeline() {
  const { caseId } = useParams()

  const { data: caseData, isLoading: caseLoading } = useQuery({
    queryKey: ['case-detail', caseId],
    queryFn: () => forensicsAPI.getCase(caseId).then(r => r.data),
    enabled: !!caseId,
  })

  const { data: timelineData, isLoading: timelineLoading } = useQuery({
    queryKey: ['case-timeline', caseId],
    queryFn: () => forensicsAPI.caseTimeline(caseId).then(r => r.data),
    enabled: !!caseId,
  })

  const { data: playbooksData } = useQuery({
    queryKey: ['playbooks'],
    queryFn: () => playbooksAPI.list().then(r => r.data?.results || r.data || []),
  })
  const playbooks = playbooksData || []

  const events = timelineData?.results || timelineData || []
  const isLoading = caseLoading || timelineLoading

  return (
    <div className="space-y-6 h-full flex flex-col">

      {/* Header */}
      <div className="shrink-0">
        <Link
          to="/forensics"
          className="inline-flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-300 transition-colors mb-4 font-mono"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Case Vault
        </Link>

        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Fingerprint className="w-5 h-5 text-cyber-green" />
              <h1 className="text-2xl font-bold text-white">
                {caseLoading ? 'Loading...' : caseData?.title || `Case #${caseId}`}
              </h1>
            </div>
            <p className="text-sm text-gray-500 font-mono">
              Forensic Investigation Timeline · Chronological chain of custody
            </p>
          </div>

          {caseData && (
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-cyber-green bg-cyber-green/10 border border-cyber-green/25 px-3 py-1.5 rounded-lg flex items-center gap-1.5">
                <Lock className="w-3 h-3" /> SHA-256 Sealed
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Timeline stats */}
      {!isLoading && events.length > 0 && (
        <div className="grid grid-cols-4 gap-3 shrink-0">
          {[
            { label: 'Total Events', value: events.length, color: '#00F5FF' },
            {
              label: 'Evidence Items',
              value: events.filter(e => e.event_type === 'EVIDENCE_UPLOADED').length,
              color: '#00E676',
            },
            {
              label: 'Alerts Escalated',
              value: events.filter(e => e.event_type?.includes('ALERT')).length,
              color: '#FF3366',
            },
            {
              label: 'Hash-Sealed Logs',
              value: events.filter(e => e.hash).length,
              color: '#C084FC',
            },
          ].map(({ label, value, color }) => (
            <div key={label} className="glass-card px-4 py-3">
              <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">{label}</div>
              <div className="text-xl font-bold font-mono" style={{ color }}>{value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Timeline */}
      <div className="flex-1 overflow-y-auto pr-1">
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="flex gap-4">
                <div className="w-9 h-9 rounded-full bg-navy-800 animate-pulse shrink-0" />
                <div className="glass-card flex-1 p-4 h-20 animate-pulse" />
              </div>
            ))}
          </div>
        ) : events.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-gray-600">
            <Fingerprint className="w-12 h-12 mb-3 opacity-30" />
            <p className="text-sm mb-1">No timeline events recorded yet</p>
            <p className="text-xs text-gray-700">
              Events are added automatically as the investigation progresses
            </p>
          </div>
        ) : (
          <div className="max-w-3xl">
            {events.map((event, i) => (
              <TimelineItem
                key={event.id || i}
                event={event}
                index={i}
                total={events.length}
                playbooks={playbooks}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
