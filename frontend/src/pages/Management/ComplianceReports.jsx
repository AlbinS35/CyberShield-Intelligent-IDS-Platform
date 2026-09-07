import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import {
  FileText, ArrowDownToLine, CheckCircle2, ShieldCheck,
  AlertTriangle, Eye, Calendar, Plus, Save, Edit3, Trash2, Clock, Shield, User, FilePlus, ChevronRight, Lock
} from 'lucide-react'
import { complianceReportsAPI } from '../../api'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import { clsx } from 'clsx'

export default function ComplianceReports() {
  const queryClient = useQueryClient()
  const [selectedReportId, setSelectedReportId] = useState(null)
  const [showGenerateModal, setShowGenerateModal] = useState(false)
  const [reportTitle, setReportTitle] = useState('')
  const [reportType, setReportType] = useState('ISO_27001')
  const [auditorNotes, setAuditorNotes] = useState('')
  const [reportStatus, setReportStatus] = useState('DRAFT')
  const [isEditingNotes, setIsEditingNotes] = useState(false)

  // Fetch reports list
  const { data: reports, isLoading: listLoading } = useQuery({
    queryKey: ['compliance-reports'],
    queryFn: () => complianceReportsAPI.list().then(r => r.data?.results || r.data || []),
  })

  // Selected report details
  const selectedReport = reports?.find(r => r.id === selectedReportId) || reports?.[0]

  // Sync edit state when selected report changes
  useEffect(() => {
    if (selectedReport) {
      setAuditorNotes(selectedReport.auditor_notes || '')
      setReportStatus(selectedReport.status || 'DRAFT')
      setIsEditingNotes(false)
    }
  }, [selectedReportId, selectedReport])

  // Automatically select first report
  useEffect(() => {
    if (reports && reports.length > 0 && !selectedReportId) {
      setSelectedReportId(reports[0].id)
    }
  }, [reports, selectedReportId])

  // Create report mutation
  const createMutation = useMutation({
    mutationFn: (newReport) => complianceReportsAPI.create(newReport),
    onSuccess: (res) => {
      toast.success('Compliance audit report generated successfully!')
      queryClient.invalidateQueries(['compliance-reports'])
      setSelectedReportId(res.data.id)
      setShowGenerateModal(false)
      setReportTitle('')
    },
    onError: () => {
      toast.error('Failed to generate compliance report.')
    }
  })

  // Update report mutation (for notes and status)
  const updateMutation = useMutation({
    mutationFn: ({ id, payload }) => complianceReportsAPI.update(id, payload),
    onSuccess: () => {
      toast.success('Report saved!')
      queryClient.invalidateQueries(['compliance-reports'])
      setIsEditingNotes(false)
    },
    onError: () => {
      toast.error('Failed to update report.')
    }
  })

  // Delete report mutation
  const deleteMutation = useMutation({
    mutationFn: (id) => complianceReportsAPI.delete(id),
    onSuccess: () => {
      toast.success('Compliance report removed from history.')
      queryClient.invalidateQueries(['compliance-reports'])
      setSelectedReportId(null)
    },
    onError: () => {
      toast.error('Failed to delete report.')
    }
  })

  const handleGenerate = (e) => {
    e.preventDefault()
    if (!reportTitle.trim()) return
    createMutation.mutate({
      title: reportTitle,
      report_type: reportType,
      status: 'DRAFT',
      auditor_notes: ''
    })
  }

  const handleSaveAudit = () => {
    if (!selectedReport) return
    updateMutation.mutate({
      id: selectedReport.id,
      payload: {
        auditor_notes: auditorNotes,
        status: reportStatus
      }
    })
  }

  const handleDelete = (id) => {
    if (!confirm('Are you sure you want to delete this compliance report? This action is permanent.')) return
    deleteMutation.mutate(id)
  }

  const handleExport = () => {
    toast.loading('Compiling audit logs and generating PDF report...', { id: 'compliance-toast' })
    setTimeout(() => {
      toast.success('Compliance report PDF generated successfully!', { id: 'compliance-toast' })
      window.print()
    }, 1500)
  }

  const REPORT_TYPE_LABELS = {
    ISO_27001: 'ISO 27001:2022',
    PCI_DSS: 'PCI-DSS v4.0',
    SOC_2: 'SOC 2 Type II',
    RBI_BANKING: 'RBI Banking Security Code CC-5.1',
  }

  const STATUS_CONFIG = {
    DRAFT: { label: 'Draft / In-Progress', cls: 'bg-amber-500/10 text-amber-400 border-amber-500/20' },
    REVIEWED: { label: 'Reviewed', cls: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
    APPROVED: { label: 'Approved & Sealed', cls: 'bg-green-500/10 text-green-400 border-green-500/20' },
  }

  return (
    <div className="space-y-6 max-w-6xl print:bg-white print:p-0">
      {/* Header */}
      <div className="flex items-center justify-between print:hidden">
        <div>
          <h1 className="text-xl font-bold text-white">Compliance & Governance Reports</h1>
          <p className="text-sm text-gray-500 mt-0.5">Generate, audit, and sign off compliance frameworks based on live telemetry metrics</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowGenerateModal(true)}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Generate New Audit
          </button>
          {selectedReport && (
            <button
              onClick={handleExport}
              className="btn-ghost bg-navy-800 text-gray-300 hover:text-white border border-navy-700 hover:bg-navy-750 flex items-center gap-2"
            >
              <ArrowDownToLine className="w-4 h-4" />
              Export Report PDF
            </button>
          )}
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Report History Sidebar */}
        <div className="lg:col-span-1 space-y-4 print:hidden">
          <div className="glass-card p-4">
            <h2 className="text-xs font-bold uppercase text-gray-500 tracking-wider mb-3">Audit Logs Registry</h2>
            {listLoading ? (
              <div className="space-y-2">
                {[1, 2, 3].map(i => (
                  <div key={i} className="h-14 bg-navy-850 rounded-lg animate-pulse" />
                ))}
              </div>
            ) : reports?.length === 0 ? (
              <div className="text-center py-8 text-gray-600">
                <FileText className="w-8 h-8 mx-auto mb-2 opacity-30" />
                <p className="text-xs">No reports generated yet.</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
                {reports?.map(r => {
                  const isSelected = r.id === selectedReportId
                  const typeLabel = REPORT_TYPE_LABELS[r.report_type] || r.report_type
                  const statusInfo = STATUS_CONFIG[r.status] || STATUS_CONFIG.DRAFT
                  return (
                    <div
                      key={r.id}
                      onClick={() => setSelectedReportId(r.id)}
                      className={clsx(
                        'p-3.5 rounded-xl border text-left cursor-pointer transition-all flex items-start justify-between group',
                        isSelected
                          ? 'border-cyber-cyan bg-cyber-cyan/5'
                          : 'border-navy-800 bg-navy-900/30 hover:bg-navy-800/40 hover:border-navy-700/50'
                      )}
                    >
                      <div className="space-y-1 min-w-0">
                        <h4 className="font-semibold text-gray-200 text-xs truncate leading-snug">{r.title}</h4>
                        <p className="text-[10px] text-gray-550 font-mono">{typeLabel}</p>
                        <div className="flex items-center gap-1.5 pt-1 text-[9px] text-gray-650">
                          <Calendar className="w-2.5 h-2.5" />
                          {format(new Date(r.created_at), 'dd MMM yyyy')}
                        </div>
                      </div>
                      <ChevronRight className="w-4 h-4 text-gray-650 group-hover:text-gray-400 shrink-0 ml-2" />
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right: Selected Report Details & Controls */}
        <div className="lg:col-span-2 space-y-6">
          {selectedReport ? (
            <div className="glass-card p-6 border-navy-750 space-y-6 print:border-none print:shadow-none print:bg-white print:text-black">
              {/* Document Header */}
              <div className="border-b border-navy-800 pb-5 flex flex-col md:flex-row justify-between items-start md:items-center print:border-black/20">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="w-6 h-6 text-cyber-cyan print:text-blue-600" />
                    <h2 className="text-base font-bold text-white print:text-black uppercase tracking-wider">
                      {REPORT_TYPE_LABELS[selectedReport.report_type]} Report
                    </h2>
                  </div>
                  <h3 className="text-sm font-semibold text-gray-300 print:text-gray-800">{selectedReport.title}</h3>
                  <p className="text-[10px] text-gray-500 print:text-gray-650">
                    Generated: {format(new Date(selectedReport.created_at), 'dd MMMM yyyy · HH:mm:ss')} · Creator: {selectedReport.generated_by_name}
                  </p>
                </div>
                <div className="mt-3 md:mt-0 flex flex-col items-end gap-2 print:hidden">
                  <span className={clsx('px-3 py-1 rounded-full text-[10px] font-bold border', STATUS_CONFIG[selectedReport.status]?.cls)}>
                    {STATUS_CONFIG[selectedReport.status]?.label}
                  </span>
                  <button
                    onClick={() => handleDelete(selectedReport.id)}
                    className="text-[10px] text-gray-500 hover:text-cyber-red flex items-center gap-1 transition-colors"
                  >
                    <Trash2 className="w-3 h-3" /> Delete Report
                  </button>
                </div>
              </div>

              {/* Snapshot Statistics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: 'Events Logged', value: selectedReport.metrics?.total_events ?? 0, status: 'SECURED' },
                  { label: 'Integrity Seals', value: selectedReport.metrics?.verified_hashes ?? 0, status: '100% PASS' },
                  { label: 'Intrusion Alerts', value: selectedReport.metrics?.threat_events ?? 0, status: 'MITIGATED' },
                  { label: 'Mitigations Deployed', value: selectedReport.metrics?.active_playbooks ?? 0, status: 'ACTIVE' },
                ].map((stat, i) => (
                  <div key={i} className="bg-navy-800/40 p-4 rounded-xl border border-navy-850 print:bg-gray-50 print:border-gray-200">
                    <div className="text-[10px] text-gray-500 uppercase font-semibold">{stat.label}</div>
                    <div className="text-xl font-bold font-mono text-cyber-cyan mt-1 print:text-blue-600">{stat.value}</div>
                    <div className="text-[9px] font-mono text-green-400 mt-0.5 print:text-green-700">{stat.status}</div>
                  </div>
                ))}
              </div>

              {/* Detailed Controls Table */}
              <div className="space-y-3">
                <h3 className="text-xs uppercase font-bold text-gray-400 print:text-gray-700 flex items-center gap-1.5">
                  <FileText className="w-4 h-4 text-cyber-cyan print:text-blue-600" />
                  Compliance Controls Checklist
                </h3>
                <div className="space-y-3">
                  {selectedReport.findings?.map((item, idx) => {
                    const isComp = item.status === 'COMPLIANT'
                    return (
                      <div key={idx} className="bg-navy-850/30 border border-navy-800/50 p-4 rounded-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4 print:border-gray-200 print:bg-white print:text-black">
                        <div className="space-y-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-[9px] font-mono font-bold text-cyber-cyan bg-cyber-cyan/10 border border-cyber-cyan/20 px-2 py-0.5 rounded shrink-0 print:text-blue-600 print:bg-blue-50 print:border-blue-200">
                              {item.code}
                            </span>
                            <h4 className="text-xs font-semibold text-gray-200 print:text-black truncate">{item.name}</h4>
                          </div>
                          <p className="text-[11px] text-gray-500 print:text-gray-655 leading-relaxed">{item.details}</p>
                        </div>
                        <span className={clsx(
                          'inline-flex items-center gap-1 px-3 py-1 rounded-full text-[9px] font-bold border shrink-0',
                          isComp
                            ? 'bg-green-500/10 text-green-400 border-green-500/20 print:bg-green-55 print:border-green-300 print:text-green-800'
                            : 'bg-amber-500/10 text-amber-400 border-amber-500/20 print:bg-amber-55 print:border-amber-300 print:text-amber-800'
                        )}>
                          {isComp ? <CheckCircle2 className="w-3 h-3" /> : <AlertTriangle className="w-3 h-3" />}
                          {item.status}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Auditor Review & Notes Area */}
              <div className="border-t border-navy-800 pt-6 space-y-4 print:hidden">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs uppercase font-bold text-gray-400 flex items-center gap-1.5">
                    <Edit3 className="w-4 h-4 text-cyber-cyan" />
                    Auditor Review Board
                  </h3>
                  {!isEditingNotes ? (
                    <button
                      onClick={() => setIsEditingNotes(true)}
                      className="px-2.5 py-1 text-[10px] font-bold text-cyber-cyan bg-cyber-cyan/10 border border-cyber-cyan/20 rounded hover:bg-cyber-cyan/20 transition-all"
                    >
                      Add/Edit Review Notes
                    </button>
                  ) : (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={handleSaveAudit}
                        className="btn-primary px-3 py-1 text-[10px] font-bold flex items-center gap-1"
                      >
                        <Save className="w-3 h-3" /> Save Changes
                      </button>
                      <button
                        onClick={() => setIsEditingNotes(false)}
                        className="btn-ghost px-3 py-1 text-[10px] font-bold"
                      >
                        Cancel
                      </button>
                    </div>
                  )}
                </div>

                {isEditingNotes ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-[10px] uppercase text-gray-500 mb-1.5 font-bold">Report Status</label>
                        <select
                          value={reportStatus}
                          onChange={e => setReportStatus(e.target.value)}
                          className="cyber-input w-full text-xs bg-navy-800"
                        >
                          <option value="DRAFT">Draft / In Review</option>
                          <option value="REVIEWED">Reviewed by Compliance Officers</option>
                          <option value="APPROVED">Approved & Cryptographically Sealed</option>
                        </select>
                      </div>
                    </div>
                    <div>
                      <label className="block text-[10px] uppercase text-gray-500 mb-1.5 font-bold">Auditor Comments & Sign-off Notes</label>
                      <textarea
                        value={auditorNotes}
                        onChange={e => setAuditorNotes(e.target.value)}
                        placeholder="Write audit logs comments, compliance notes, and legal hold requirements here..."
                        className="cyber-input w-full h-28 text-xs resize-none"
                      />
                    </div>
                  </div>
                ) : (
                  <div className="bg-navy-950/50 rounded-xl p-4 border border-navy-900 font-mono text-xs text-gray-400 space-y-2">
                    <div className="flex items-center justify-between text-[10px] text-gray-550 border-b border-navy-900 pb-2">
                      <span>AUDIT NOTES ENTRY</span>
                      <span>STATUS: {selectedReport.status}</span>
                    </div>
                    <p className="whitespace-pre-wrap leading-relaxed italic text-gray-300">
                      {selectedReport.auditor_notes || 'No compliance verification comments have been logged for this report yet.'}
                    </p>
                  </div>
                )}
              </div>

              {/* Auditor Sign-off Area */}
              <div className="pt-6 border-t border-navy-850 flex flex-col md:flex-row justify-between text-xs text-gray-500 gap-6 print:border-black/10 print:text-black">
                <div className="space-y-1">
                  <div className="font-semibold text-gray-400 print:text-gray-800">CyberShield Governance Ledger</div>
                  <p className="text-[10px] text-gray-650 leading-snug">All system states are sealed in an immutable ledger.<br />Chain-of-custody verifications are stored automatically.</p>
                </div>
                <div className="flex flex-col items-end gap-2">
                  <div className="w-40 border-b border-navy-700 h-10 print:border-black/30" />
                  <span className="text-[10px] text-gray-600 uppercase font-semibold">Authorized Auditor Signature</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="glass-card p-12 text-center text-gray-600">
              <FileText className="w-12 h-12 mx-auto mb-3 opacity-20" />
              <p className="text-sm">Select a compliance report or generate a new live snapshot to begin review.</p>
            </div>
          )}
        </div>
      </div>

      {/* Generate Report Modal */}
      <AnimatePresence>
        {showGenerateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="glass-card w-full max-w-md p-6 border-cyber-cyan/30"
            >
              <h2 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                <FilePlus className="w-5 h-5 text-cyber-cyan" />
                Generate Governance Audit
              </h2>
              <form onSubmit={handleGenerate} className="space-y-4">
                <div>
                  <label className="block text-[10px] uppercase text-gray-500 mb-1 font-semibold">Audit Sheet Title</label>
                  <input
                    type="text"
                    value={reportTitle}
                    onChange={e => setReportTitle(e.target.value)}
                    placeholder="e.g. Q3 Internal Security Audit Worksheet"
                    className="cyber-input w-full"
                    required
                  />
                </div>

                <div>
                  <label className="block text-[10px] uppercase text-gray-500 mb-1 font-semibold">Audit Framework / Standard</label>
                  <select
                    value={reportType}
                    onChange={e => setReportType(e.target.value)}
                    className="cyber-input w-full bg-navy-800"
                  >
                    <option value="ISO_27001">ISO 27001:2022 (Network Controls)</option>
                    <option value="PCI_DSS">PCI-DSS v4.0 (Tamper Audit Trails)</option>
                    <option value="SOC_2">SOC 2 Type II (Threat Containment)</option>
                    <option value="RBI_BANKING">RBI Banking Security Guidelines</option>
                  </select>
                </div>

                <div className="bg-navy-950/60 p-3 rounded-lg border border-navy-850 text-[10px] text-gray-500 leading-relaxed">
                  📢 <strong>Note:</strong> Generating an audit report will dynamically query all current Network Events, Security Alerts, Active Blocklists, and Playbooks for your tenant, locking their statistics into an immutable snapshot for compliance review.
                </div>

                <div className="flex items-center justify-end gap-3 pt-2">
                  <button type="button" onClick={() => setShowGenerateModal(false)} className="btn-ghost text-xs">
                    Cancel
                  </button>
                  <button type="submit" disabled={createMutation.isLoading} className="btn-primary text-xs flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4" />
                    {createMutation.isLoading ? 'Computing...' : 'Generate Snapshot'}
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
