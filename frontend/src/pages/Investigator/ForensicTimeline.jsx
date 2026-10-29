import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { forensicsAPI, playbooksAPI, blocklistAPI } from '../../api'
import { format } from 'date-fns'
import { clsx } from 'clsx'
import toast from 'react-hot-toast'
import {
  Clock, ArrowLeft, Shield, AlertTriangle, Lock,
  Fingerprint, FileText, Activity, Server, User,
  CheckCircle2, XCircle, ChevronRight, Play, ShieldAlert,
  Plus, X
} from 'lucide-react'

const EVENT_TYPE_CONFIG = {
  ALERT_CREATED:        { color: '#FF3366', icon: AlertTriangle, label: 'Alert Created' },
  ALERT_ESCALATED:      { color: '#FF8C42', icon: AlertTriangle, label: 'Alert Escalated' },
  CASE_OPENED:          { color: '#00F5FF', icon: Fingerprint,   label: 'Case Opened' },
  EVIDENCE_UPLOADED:    { color: '#00E676', icon: FileText,      label: 'Evidence Uploaded' },
  EVIDENCE_VERIFIED:    { color: '#00E676', icon: CheckCircle2,  label: 'Evidence Verified' },
  IP_BLOCKED:           { color: '#FFB800', icon: Shield,        label: 'IP Blocked' },
  PLAYBOOK_FIRED:       { color: '#FFB800', icon: Activity,      label: 'Playbook Fired' },
  CASE_CLOSED:          { color: '#C084FC', icon: Lock,          label: 'Case Closed' },
  LOG_SEALED:           { color: '#00E676', icon: Lock,          label: 'Log Hash Sealed' },
  NOTE_ADDED:           { color: '#9CA3AF', icon: FileText,      label: 'Note Added' },
  // MITRE ATT&CK & Core Event Categories
  INITIAL_ACCESS:       { color: '#FF3366', icon: AlertTriangle, label: 'Initial Access' },
  LATERAL_MOVEMENT:     { color: '#FF8C42', icon: Activity,      label: 'Lateral Movement' },
  PRIVILEGE_ESCALATION: { color: '#C084FC', icon: ShieldAlert,   label: 'Privilege Escalation' },
  DATA_EXFILTRATION:    { color: '#EF4444', icon: Lock,          label: 'Data Exfiltration' },
  PERSISTENCE:          { color: '#A855F7', icon: Lock,          label: 'Persistence' },
  COMMAND_CONTROL:      { color: '#F97316', icon: Server,        label: 'Command & Control' },
  IMPACT:               { color: '#DC2626', icon: AlertTriangle, label: 'Impact / Destruction' },
  DETECTION:            { color: '#00F5FF', icon: Fingerprint,   label: 'Detection Event' },
  RESPONSE:             { color: '#FFB800', icon: Shield,        label: 'Response Action' },
  OTHER:                { color: '#9CA3AF', icon: Activity,      label: 'Investigation Event' },
}

function TimelineItem({ event, index, total, playbooks = [] }) {
  const eventKey = event.event_type || event.category || 'OTHER'
  const cfg = EVENT_TYPE_CONFIG[eventKey] || {
    color: '#9CA3AF', icon: Activity, label: event.category_display || eventKey
  }
  const Icon = cfg.icon
  const isLast = index === total - 1

  const timeVal = event.created_at || event.event_time || event.recorded_at
  const ip = event.ip_address || event.source_ip
  const actor = event.actor_name || event.recorded_by_name || event.source_system
  const hash = event.hash || event.log_hash || event.sha256_hash
  const evidenceFile = event.evidence_file || event.file_name

  const [showResponseControls, setShowResponseControls] = useState(false)
  const [selectedPlaybookId, setSelectedPlaybookId] = useState('')
  const [executing, setExecuting] = useState(false)
  const [blocking, setBlocking] = useState(false)

  const handleBlockIP = async () => {
    if (!ip) return
    setBlocking(true)
    try {
      await blocklistAPI.add({ ip_address: ip, reason: `Containment initiated via Forensic Case timeline.` })
      toast.success(`IP ${ip} has been successfully added to the blocklist!`)
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
    if (!ip) {
      toast.error('No target IP associated with this event.')
      return
    }
    setExecuting(true)
    try {
      await playbooksAPI.execute(selectedPlaybookId, ip)
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
          <div className="flex items-center gap-1.5 text-[10px] text-gray-400 font-mono shrink-0 mt-0.5">
            <Clock className="w-2.5 h-2.5" />
            {timeVal
              ? format(new Date(timeVal), 'dd MMM yyyy · HH:mm:ss')
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
            {actor && (
              <span className="inline-flex items-center gap-1.5 text-[10px] text-gray-400 bg-navy-800 border border-navy-700 px-2 py-1 rounded font-mono">
                <User className="w-2.5 h-2.5 text-cyber-cyan" /> {actor}
              </span>
            )}
            {ip && (
              <span className="inline-flex items-center gap-1.5 text-[10px] text-cyber-cyan bg-cyber-cyan/8 border border-cyber-cyan/20 px-2 py-1 rounded font-mono">
                <Server className="w-2.5 h-2.5" /> {ip}
              </span>
            )}
            {hash && (
              <span className="inline-flex items-center gap-1.5 text-[10px] text-cyber-green bg-cyber-green/8 border border-cyber-green/20 px-2 py-1 rounded font-mono">
                <Lock className="w-2.5 h-2.5" /> SHA-256: {hash.slice(0, 16)}…
              </span>
            )}
            {evidenceFile && (
              <span className="inline-flex items-center gap-1.5 text-[10px] text-gray-300 bg-navy-800 border border-navy-700 px-2 py-1 rounded font-mono">
                <FileText className="w-2.5 h-2.5 text-cyber-green" /> {evidenceFile}
              </span>
            )}
          </div>

          {ip && (
            <button
              onClick={() => setShowResponseControls(!showResponseControls)}
              className="text-[10px] font-bold text-cyber-cyan bg-cyber-cyan/10 hover:bg-cyber-cyan/20 border border-cyber-cyan/20 px-2.5 py-1 rounded transition-all flex items-center gap-1"
            >
              <ShieldAlert className="w-3.5 h-3.5" /> Containment Actions
            </button>
          )}
        </div>

        {/* Containment controls panel */}
        {showResponseControls && ip && (
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
                    Instantly block all inbound and outbound traffic to/from {ip} across the cluster network.
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
  const queryClient = useQueryClient()
  const [showAddModal, setShowAddModal] = useState(false)

  // Form state for adding timeline event
  const [formData, setFormData] = useState({
    title: '',
    category: 'DETECTION',
    description: '',
    source_ip: '',
  })
  const [submitting, setSubmitting] = useState(false)

  const { data: caseData, isLoading: caseLoading } = useQuery({
    queryKey: ['case-detail', caseId],
    queryFn: () => forensicsAPI.getCase(caseId).then(r => r.data),
    enabled: !!caseId,
  })

  const { data: timelineData, isLoading: timelineLoading, refetch: refetchTimeline } = useQuery({
    queryKey: ['case-timeline', caseId],
    queryFn: () => forensicsAPI.caseTimeline(caseId).then(r => r.data),
    enabled: !!caseId,
  })

  const { data: playbooksData } = useQuery({
    queryKey: ['playbooks'],
    queryFn: () => playbooksAPI.list().then(r => r.data?.results || r.data || []),
  })
  const playbooks = playbooksData || []

  const events = Array.isArray(timelineData) ? timelineData : (timelineData?.results || [])
  const isLoading = caseLoading || timelineLoading

  const handleAddEvent = async (e) => {
    e.preventDefault()
    if (!formData.title.trim()) {
      toast.error('Event title is required')
      return
    }
    setSubmitting(true)
    try {
      await forensicsAPI.addTimelineEvent({
        case: caseId,
        title: formData.title.trim(),
        category: formData.category,
        description: formData.description.trim(),
        source_ip: formData.source_ip.trim() || undefined,
        event_time: new Date().toISOString(),
      })
      toast.success('Investigation finding recorded to case timeline!')
      setShowAddModal(false)
      setFormData({ title: '', category: 'DETECTION', description: '', source_ip: '' })
      queryClient.invalidateQueries({ queryKey: ['case-timeline', caseId] })
    } catch (err) {
      toast.error(`Failed to record timeline event: ${err?.response?.data?.detail || err.message}`)
    } finally {
      setSubmitting(false)
    }
  }

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

          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowAddModal(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyber-cyan/10 text-cyber-cyan border border-cyber-cyan/30 hover:bg-cyber-cyan/20 text-xs font-semibold transition-all"
            >
              <Plus className="w-3.5 h-3.5" /> Add Finding / Note
            </button>

            {caseData && (
              <span className="text-xs font-mono text-cyber-green bg-cyber-green/10 border border-cyber-green/25 px-3 py-1.5 rounded-lg flex items-center gap-1.5">
                <Lock className="w-3 h-3" /> SHA-256 Sealed
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Timeline stats */}
      {!isLoading && events.length > 0 && (
        <div className="grid grid-cols-4 gap-3 shrink-0">
          {[
            { label: 'Total Events', value: events.length, color: '#00F5FF' },
            {
              label: 'Evidence Items',
              value: events.filter(e => e.event_type === 'EVIDENCE_UPLOADED' || e.evidence || e.evidence_file).length,
              color: '#00E676',
            },
            {
              label: 'Alerts Escalated',
              value: events.filter(e => (
                e.event_type?.includes('ALERT') ||
                e.category === 'PRIVILEGE_ESCALATION' ||
                e.category === 'INITIAL_ACCESS' ||
                e.title?.toLowerCase().includes('escalat')
              )).length,
              color: '#FF3366',
            },
            {
              label: 'Hash-Sealed Logs',
              value: events.filter(e => (e.hash || e.log_hash || e.sha256_hash || e.event_type === 'LOG_SEALED')).length,
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
            <p className="text-sm mb-1 text-gray-400 font-medium">No timeline events recorded yet</p>
            <p className="text-xs text-gray-500 mb-4 max-w-sm text-center">
              Events are populated automatically from escalated telemetry and playbooks, or you can record investigative notes manually.
            </p>
            <div className="flex items-center gap-3">
              <button
                onClick={() => refetchTimeline()}
                className="btn-secondary text-xs px-3 py-1.5"
              >
                Refresh Timeline
              </button>
              <button
                onClick={() => setShowAddModal(true)}
                className="btn-primary text-xs px-3 py-1.5 flex items-center gap-1.5"
              >
                <Plus className="w-3.5 h-3.5" /> Record Investigation Note
              </button>
            </div>
          </div>
        ) : (
          <div className="max-w-3xl pb-8">
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

      {/* Add Finding / Note Modal */}
      <AnimatePresence>
        {showAddModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="glass-card w-full max-w-lg p-6 relative border border-navy-700 bg-navy-900 shadow-2xl rounded-xl"
            >
              <div className="flex items-center justify-between pb-4 border-b border-navy-700">
                <div className="flex items-center gap-2">
                  <Fingerprint className="w-5 h-5 text-cyber-cyan" />
                  <h3 className="text-base font-bold text-white">Record Investigation Finding</h3>
                </div>
                <button
                  onClick={() => setShowAddModal(false)}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleAddEvent} className="mt-4 space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-300 mb-1">
                    Finding Title *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Reverse-shell payload identified in bash history"
                    value={formData.title}
                    onChange={e => setFormData({ ...formData, title: e.target.value })}
                    className="cyber-input w-full text-xs"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-gray-300 mb-1">
                      Event Category
                    </label>
                    <select
                      value={formData.category}
                      onChange={e => setFormData({ ...formData, category: e.target.value })}
                      className="cyber-input w-full text-xs bg-navy-800"
                    >
                      <option value="DETECTION">Detection Event</option>
                      <option value="INITIAL_ACCESS">Initial Access</option>
                      <option value="LATERAL_MOVEMENT">Lateral Movement</option>
                      <option value="PRIVILEGE_ESCALATION">Privilege Escalation</option>
                      <option value="DATA_EXFILTRATION">Data Exfiltration</option>
                      <option value="PERSISTENCE">Persistence</option>
                      <option value="COMMAND_CONTROL">Command & Control</option>
                      <option value="IMPACT">Impact / Destruction</option>
                      <option value="RESPONSE">Response Action</option>
                      <option value="NOTE_ADDED">Analyst Note</option>
                      <option value="OTHER">Other</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-300 mb-1">
                      Associated IP Address
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. 192.168.1.50"
                      value={formData.source_ip}
                      onChange={e => setFormData({ ...formData, source_ip: e.target.value })}
                      className="cyber-input w-full text-xs"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-300 mb-1">
                    Investigation Details / Evidence Log
                  </label>
                  <textarea
                    rows={4}
                    placeholder="Document artifact locations, memory dump offsets, observed IOCs, or legal custody notes..."
                    value={formData.description}
                    onChange={e => setFormData({ ...formData, description: e.target.value })}
                    className="cyber-input w-full text-xs"
                  />
                </div>

                <div className="flex items-center justify-end gap-3 pt-3 border-t border-navy-700">
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="btn-secondary text-xs px-4 py-2"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="btn-primary text-xs px-4 py-2 font-bold flex items-center gap-1.5"
                  >
                    {submitting ? 'Recording...' : 'Add to Timeline'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
