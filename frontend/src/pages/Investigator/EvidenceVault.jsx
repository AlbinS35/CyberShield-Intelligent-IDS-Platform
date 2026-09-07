import { useState, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Upload, Shield, CheckCircle, XCircle, Lock,
  FileText, Database, Camera, File, Search,
  Hash, Clock, User, ChevronDown
} from 'lucide-react'
import { forensicsAPI } from '../../api'
import { format } from 'date-fns'
import toast from 'react-hot-toast'
import { clsx } from 'clsx'

const EVIDENCE_ICONS = {
  LOG_FILE:    FileText,
  PCAP:        Database,
  DISK_IMAGE:  Database,
  SCREENSHOT:  Camera,
  MEMORY_DUMP: Database,
  REPORT:      FileText,
  OTHER:       File,
}

const EVIDENCE_TYPE_LABELS = {
  LOG_FILE: 'Log File', PCAP: 'PCAP Capture', DISK_IMAGE: 'Disk Image',
  SCREENSHOT: 'Screenshot', MEMORY_DUMP: 'Memory Dump', REPORT: 'Report', OTHER: 'Other',
}

function EvidenceCard({ evidence, onVerify }) {
  const [showHash, setShowHash]   = useState(false)
  const [verifying, setVerifying] = useState(false)
  const [integrity, setIntegrity] = useState(null)
  const Icon = EVIDENCE_ICONS[evidence.evidence_type] || File

  const handleVerify = async () => {
    setVerifying(true)
    try {
      const { data } = await onVerify(evidence.id)
      setIntegrity(data.integrity_valid)
      if (data.integrity_valid) {
        toast.success('SHA-256 hash verified — evidence is untampered.')
      } else {
        toast.error('Hash mismatch — evidence may be tampered!')
      }
    } catch {
      toast.error('Verification failed.')
    } finally {
      setVerifying(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-4 hover:border-cyber-cyan/20 transition-all"
    >
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 rounded-lg bg-cyber-cyan/10 border border-cyber-cyan/20 flex items-center justify-center shrink-0">
          <Icon className="w-4 h-4 text-cyber-cyan" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h3 className="text-sm font-semibold text-gray-100 truncate">{evidence.title}</h3>
              <span className="text-[10px] text-gray-500 font-mono">{EVIDENCE_TYPE_LABELS[evidence.evidence_type]}</span>
            </div>
            {/* Integrity status */}
            {integrity !== null && (
              integrity ? (
                <span className="inline-flex items-center gap-1 text-[10px] text-green-400 shrink-0">
                  <CheckCircle className="w-3 h-3" /> Valid
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-[10px] text-red-400 shrink-0">
                  <XCircle className="w-3 h-3" /> Tampered!
                </span>
              )
            )}
          </div>

          {evidence.description && (
            <p className="text-xs text-gray-500 mt-1 line-clamp-2">{evidence.description}</p>
          )}

          {/* File metadata */}
          <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-[10px] text-gray-600">
            <span className="flex items-center gap-1">
              <File className="w-3 h-3" />
              {evidence.file_name}
            </span>
            <span>{(evidence.file_size_bytes / 1024).toFixed(1)} KB</span>
            <span className="flex items-center gap-1">
              <User className="w-3 h-3" />
              {evidence.uploaded_by_name}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {format(new Date(evidence.uploaded_at), 'dd MMM yyyy HH:mm')}
            </span>
          </div>

          {/* SHA-256 Hash */}
          <div className="mt-3">
            <button
              onClick={() => setShowHash(v => !v)}
              className="flex items-center gap-1.5 text-[10px] text-gray-500 hover:text-cyber-cyan transition-colors"
            >
              <Hash className="w-3 h-3" />
              SHA-256 Fingerprint
              <ChevronDown className={clsx('w-3 h-3 transition-transform', showHash && 'rotate-180')} />
            </button>
            <AnimatePresence>
              {showHash && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="mt-1.5 overflow-hidden"
                >
                  <div className="bg-navy-800 rounded px-3 py-2 font-mono text-[9px] text-cyber-cyan break-all border border-navy-600">
                    {evidence.sha256_hash}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Actions */}
          <div className="mt-3 flex items-center gap-2">
            <button
              onClick={handleVerify}
              disabled={verifying}
              className="flex items-center gap-1.5 text-[10px] px-2.5 py-1 rounded-md bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 hover:bg-cyan-500/20 transition-colors"
            >
              <Shield className={clsx('w-3 h-3', verifying && 'animate-pulse')} />
              {verifying ? 'Verifying...' : 'Verify Integrity'}
            </button>
            <a
              href={evidence.file}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[10px] px-2.5 py-1 rounded-md bg-navy-700 text-gray-400 border border-navy-600 hover:text-gray-200 transition-colors"
            >
              Download
            </a>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

export default function EvidenceVault() {
  const [dragOver,  setDragOver]  = useState(false)
  const [uploading, setUploading] = useState(false)
  const [caseId,    setCaseId]    = useState('')
  const [evType,    setEvType]    = useState('LOG_FILE')
  const [title,     setTitle]     = useState('')
  const fileRef = useRef(null)

  const { data: casesData } = useQuery({
    queryKey: ['cases-list'],
    queryFn: () => forensicsAPI.listCases({}).then(r => r.data),
  })

  const { data: evidenceData, isLoading, refetch } = useQuery({
    queryKey: ['all-evidence'],
    queryFn: () => forensicsAPI.listCases({}).then(r => r.data),
    // In production: call a dedicated /api/forensics/evidence/ list endpoint
  })

  const cases = casesData?.results || []

  const handleUpload = async (files) => {
    if (!files[0] || !caseId || !title) {
      toast.error('Please select a case, enter a title, and choose a file.')
      return
    }
    const formData = new FormData()
    formData.append('file',          files[0])
    formData.append('case',          caseId)
    formData.append('evidence_type', evType)
    formData.append('title',         title)
    formData.append('mime_type',     files[0].type)

    setUploading(true)
    try {
      const { data } = await forensicsAPI.uploadEvidence(formData)
      toast.success(`Evidence uploaded. SHA-256: ${data.sha256_hash?.slice(0, 16)}...`)
      setTitle('')
      refetch()
    } catch {
      toast.error('Upload failed. Check your connection.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-white">Evidence Vault</h1>
        <p className="text-sm text-gray-500 mt-0.5">SHA-256 sealed forensic evidence repository</p>
      </div>

      {/* Upload Zone */}
      <div className="glass-card p-5">
        <h2 className="text-sm font-semibold text-gray-200 mb-4 flex items-center gap-2">
          <Lock className="w-4 h-4 text-cyber-cyan" />
          Upload Evidence File
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
          <select
            value={caseId}
            onChange={e => setCaseId(e.target.value)}
            className="cyber-input bg-navy-800"
          >
            <option value="">Select Investigation Case</option>
            {cases.map(c => (
              <option key={c.id} value={c.id}>{c.case_number} — {c.title}</option>
            ))}
          </select>
          <select
            value={evType}
            onChange={e => setEvType(e.target.value)}
            className="cyber-input bg-navy-800"
          >
            {Object.entries(EVIDENCE_TYPE_LABELS).map(([v, l]) => (
              <option key={v} value={v}>{l}</option>
            ))}
          </select>
          <input
            type="text" value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder="Evidence title (e.g. Apache access.log)"
            className="cyber-input"
          />
        </div>

        {/* Drop Zone */}
        <div
          onDragOver={e => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={e => { e.preventDefault(); setDragOver(false); handleUpload(e.dataTransfer.files) }}
          onClick={() => fileRef.current?.click()}
          className={clsx(
            'border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all',
            dragOver
              ? 'border-cyber-cyan bg-cyber-cyan/5'
              : 'border-navy-600 hover:border-cyber-cyan/40 hover:bg-navy-800/30'
          )}
        >
          <input
            ref={fileRef} type="file" className="hidden"
            onChange={e => handleUpload(e.target.files)}
          />
          {uploading ? (
            <div className="flex flex-col items-center gap-2">
              <div className="w-8 h-8 border-2 border-cyber-cyan/30 border-t-cyber-cyan rounded-full animate-spin" />
              <p className="text-sm text-cyber-cyan">Computing SHA-256 and uploading...</p>
            </div>
          ) : (
            <>
              <Upload className={clsx('w-8 h-8 mx-auto mb-2', dragOver ? 'text-cyber-cyan' : 'text-gray-600')} />
              <p className="text-sm text-gray-400">
                {dragOver ? 'Drop to upload' : 'Click or drag & drop evidence file'}
              </p>
              <p className="text-xs text-gray-600 mt-1">
                SHA-256 hash computed automatically on upload
              </p>
            </>
          )}
        </div>
      </div>

      {/* Evidence listing hint */}
      <div className="glass-card p-6 text-center text-gray-600">
        <Shield className="w-6 h-6 mx-auto mb-2 opacity-30" />
        <p className="text-sm">Select a case from Case Vault to view its evidence chain.</p>
        <p className="text-xs mt-1">Evidence is scoped per investigation case for chain-of-custody integrity.</p>
      </div>
    </div>
  )
}
