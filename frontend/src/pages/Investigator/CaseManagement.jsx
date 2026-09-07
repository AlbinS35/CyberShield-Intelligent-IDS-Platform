import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import {
  FolderOpen, Plus, Search, Clock, User,
  Shield, ChevronRight, AlertTriangle
} from 'lucide-react'
import { forensicsAPI } from '../../api'
import { format } from 'date-fns'
import { clsx } from 'clsx'

const STATUS_CONFIG = {
  OPEN:           { label: 'Open',             cls: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20' },
  ACTIVE:         { label: 'Active',           cls: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
  PENDING_REVIEW: { label: 'Pending Review',   cls: 'bg-amber-500/10 text-amber-400 border-amber-500/20' },
  CLOSED:         { label: 'Closed',           cls: 'bg-gray-500/10 text-gray-400 border-gray-500/20' },
  ARCHIVED:       { label: 'Archived',         cls: 'bg-gray-600/10 text-gray-500 border-gray-600/20' },
}

const CLASSIFICATION_CONFIG = {
  CONFIDENTIAL: { label: 'Confidential', cls: 'text-red-400' },
  RESTRICTED:   { label: 'Restricted',   cls: 'text-orange-400' },
  INTERNAL:     { label: 'Internal',     cls: 'text-amber-400' },
  PUBLIC:       { label: 'Public',       cls: 'text-green-400' },
}

export default function CaseManagement() {
  const [search, setSearch]   = useState('')
  const [status, setStatus]   = useState('')
  const [showNew, setShowNew] = useState(false)
  const [newCase, setNewCase] = useState({ title: '', description: '', classification: 'CONFIDENTIAL' })
  const [saving, setSaving]   = useState(false)

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['forensic-cases', search, status],
    queryFn: () => forensicsAPI.listCases({
      search: search || undefined,
      status: status || undefined,
    }).then(r => r.data),
  })

  const cases = data?.results || []

  const handleCreate = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await forensicsAPI.createCase(newCase)
      setShowNew(false)
      setNewCase({ title: '', description: '', classification: 'CONFIDENTIAL' })
      refetch()
    } catch (err) {
      console.error(err)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Forensic Case Vault</h1>
          <p className="text-sm text-gray-500 mt-0.5">{cases.length} active investigation cases</p>
        </div>
        <button onClick={() => setShowNew(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          New Case
        </button>
      </div>

      {/* New Case Form */}
      {showNew && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-5 border-cyber-cyan/20"
        >
          <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <FolderOpen className="w-4 h-4 text-cyber-cyan" />
            Open New Investigation Case
          </h2>
          <form onSubmit={handleCreate} className="space-y-3">
            <input
              type="text"
              value={newCase.title}
              onChange={e => setNewCase(p => ({ ...p, title: e.target.value }))}
              placeholder="Case title (e.g. Ransomware Intrusion — Server-04)"
              className="cyber-input"
              required
            />
            <textarea
              value={newCase.description}
              onChange={e => setNewCase(p => ({ ...p, description: e.target.value }))}
              placeholder="Brief case description and initial observations..."
              className="cyber-input h-24 resize-none"
            />
            <div className="flex items-center gap-3">
              <select
                value={newCase.classification}
                onChange={e => setNewCase(p => ({ ...p, classification: e.target.value }))}
                className="cyber-input w-48 bg-navy-800"
              >
                <option value="CONFIDENTIAL">Confidential</option>
                <option value="RESTRICTED">Restricted</option>
                <option value="INTERNAL">Internal</option>
              </select>
              <button type="submit" disabled={saving} className="btn-primary">
                {saving ? 'Creating...' : 'Open Case'}
              </button>
              <button type="button" onClick={() => setShowNew(false)} className="btn-ghost">Cancel</button>
            </div>
          </form>
        </motion.div>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text" value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search cases..."
            className="cyber-input pl-9"
          />
        </div>
        <select
          value={status}
          onChange={e => setStatus(e.target.value)}
          className="cyber-input w-44 bg-navy-800"
        >
          <option value="">All Statuses</option>
          {Object.entries(STATUS_CONFIG).map(([v, { label }]) => (
            <option key={v} value={v}>{label}</option>
          ))}
        </select>
      </div>

      {/* Cases Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="glass-card p-5 space-y-3">
              <div className="h-4 bg-navy-700 rounded animate-pulse w-2/3" />
              <div className="h-3 bg-navy-700 rounded animate-pulse w-1/2" />
              <div className="h-3 bg-navy-700 rounded animate-pulse w-3/4" />
            </div>
          ))
        ) : cases.length === 0 ? (
          <div className="col-span-2 glass-card p-12 text-center text-gray-600">
            <Shield className="w-10 h-10 mx-auto mb-3 opacity-20" />
            <p className="text-sm">No cases found. Open a new investigation to begin.</p>
          </div>
        ) : (
          cases.map((fc, idx) => {
            const status = STATUS_CONFIG[fc.status] || STATUS_CONFIG.OPEN
            const cls    = CLASSIFICATION_CONFIG[fc.classification] || CLASSIFICATION_CONFIG.INTERNAL
            return (
              <motion.div
                key={fc.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="glass-card p-5 hover:border-cyber-cyan/20 transition-all group"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[10px] font-mono text-gray-500">{fc.case_number}</span>
                      <span className={clsx('inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold border', status.cls)}>
                        {status.label}
                      </span>
                      {fc.legal_hold && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-red-500/10 text-red-400 border border-red-500/20">
                          <AlertTriangle className="w-2.5 h-2.5" /> Legal Hold
                        </span>
                      )}
                    </div>
                    <h3 className="font-semibold text-gray-100 text-sm leading-snug">{fc.title}</h3>
                  </div>
                  <Link
                    to={`/forensics/timeline/${fc.id}`}
                    className="opacity-0 group-hover:opacity-100 transition-opacity ml-2 shrink-0"
                  >
                    <ChevronRight className="w-5 h-5 text-cyber-cyan" />
                  </Link>
                </div>

                <p className="text-xs text-gray-500 line-clamp-2 mb-4">{fc.description}</p>

                <div className="grid grid-cols-3 gap-3 text-xs">
                  <div>
                    <div className="text-gray-600 mb-0.5">Evidence</div>
                    <div className="font-mono text-cyber-cyan">{fc.evidence_count}</div>
                  </div>
                  <div>
                    <div className="text-gray-600 mb-0.5">Events</div>
                    <div className="font-mono text-gray-300">{fc.timeline_count}</div>
                  </div>
                  <div>
                    <div className="text-gray-600 mb-0.5">Classification</div>
                    <div className={clsx('font-semibold text-[10px]', cls.cls)}>{cls.label}</div>
                  </div>
                </div>

                <div className="mt-3 pt-3 border-t border-navy-700/50 flex items-center justify-between text-[10px] text-gray-600">
                  <div className="flex items-center gap-1">
                    <User className="w-3 h-3" />
                    {fc.lead_investigator_name || 'Unassigned'}
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {format(new Date(fc.created_at), 'dd MMM yyyy')}
                  </div>
                </div>
              </motion.div>
            )
          })
        )}
      </div>
    </div>
  )
}
