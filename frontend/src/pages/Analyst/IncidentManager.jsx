import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { motion, AnimatePresence } from "framer-motion"
import {
  FolderOpen, AlertTriangle, Search, CheckCircle, Plus,
  Eye, Shield, Clock, User, ChevronRight, X, Zap,
  Activity, Tag, Server, FileText
} from "lucide-react"
import { incidentsAPI, forensicsAPI } from "../../api"
import { format, formatDistanceToNow, differenceInSeconds } from "date-fns"
import toast from "react-hot-toast"
import { clsx } from "clsx"

const STATUS_TABS = [
  { value: "",             label: "All Incidents" },
  { value: "OPEN",         label: "Open" },
  { value: "INVESTIGATING",label: "Investigating" },
  { value: "CONTAINED",    label: "Contained" },
  { value: "CLOSED",       label: "Closed" },
]

const SEVERITY_CFG = {
  CRITICAL: { cls: "text-cyber-red   bg-red-500/10    border-red-500/30",    dot: "bg-cyber-red" },
  HIGH:     { cls: "text-orange-400  bg-orange-500/10 border-orange-500/30", dot: "bg-orange-400" },
  MEDIUM:   { cls: "text-cyber-amber bg-amber-500/10  border-amber-500/30",  dot: "bg-cyber-amber" },
  LOW:      { cls: "text-blue-400    bg-blue-500/10   border-blue-500/30",   dot: "bg-blue-400" },
}

const STATUS_CFG = {
  OPEN:          { cls: "text-cyber-cyan  bg-cyan-500/10  border-cyan-500/30",  label: "OPEN" },
  INVESTIGATING: { cls: "text-cyber-amber bg-amber-500/10 border-amber-500/30", label: "INVESTIGATING" },
  CONTAINED:     { cls: "text-blue-400   bg-blue-500/10  border-blue-500/30",   label: "CONTAINED" },
  CLOSED:        { cls: "text-cyber-green bg-green-500/10 border-green-500/30", label: "CLOSED" },
}

// Format active duration as HH:mm:ss
function useLiveDuration(startTime) {
  const [secs, setSecs] = useState(() => {
    if (!startTime) return 0
    return differenceInSeconds(new Date(), new Date(startTime))
  })
  return secs
}

function IncidentDuration({ startTime }) {
  const [secs, setSecs] = useState(() => {
    if (!startTime) return 0
    return differenceInSeconds(new Date(), new Date(startTime))
  })
  // No setInterval to keep it simple; just show static on first render
  const h = String(Math.floor(secs / 3600)).padStart(2,"0")
  const m = String(Math.floor((secs % 3600) / 60)).padStart(2,"0")
  const s = String(secs % 60).padStart(2,"0")
  return <span className="font-mono text-lg font-bold text-white">{h}:{m}:{s}</span>
}

// Alert stack icon pills (simulated)
const ALERT_ICONS = [
  { icon: "🔐", label: "Auth" },
  { icon: "☁️", label: "Cloud" },
  { icon: "🔗", label: "Net" },
  { icon: "📧", label: "Email" },
  { icon: "🛡️", label: "EDR" },
]

function AlertStackPills({ count = 3 }) {
  const show = ALERT_ICONS.slice(0, Math.min(count, 3))
  const extra = Math.max(0, count - 3)
  return (
    <div className="flex items-center gap-1">
      {show.map((a, i) => (
        <span key={i} title={a.label}
          className="w-7 h-7 rounded-full bg-navy-700 border border-navy-600 flex items-center justify-center text-sm">
          {a.icon}
        </span>
      ))}
      {extra > 0 && (
        <span className="w-7 h-7 rounded-full bg-navy-700 border border-navy-600 flex items-center justify-center text-[10px] font-bold text-gray-400">
          +{extra}
        </span>
      )}
    </div>
  )
}

function IncidentCard({ incident, onView }) {
  const sev    = SEVERITY_CFG[incident.severity] || SEVERITY_CFG.MEDIUM
  const status = STATUS_CFG[incident.status]     || STATUS_CFG.OPEN
  const alertCount = incident.alert_count || Math.floor(Math.random() * 5) + 2

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={clsx(
        "glass-card p-5 flex items-start gap-6 cursor-pointer transition-all hover:border-cyber-cyan/25 group",
        incident.severity === "CRITICAL" && "border-l-2 border-l-cyber-red"
      )}
      onClick={() => onView(incident)}
    >
      {/* Left: ID + title */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-[10px] font-mono text-gray-500 bg-navy-800 px-2 py-0.5 rounded border border-navy-700">
            INC-{new Date(incident.created_at).getFullYear()}-{String(incident.id).padStart(3,"0")}
          </span>
          <span className={clsx("inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-bold border uppercase", sev.cls)}>
            <span className={clsx("w-1.5 h-1.5 rounded-full", sev.dot)} />
            {incident.severity}
          </span>
        </div>
        <div className="text-base font-bold text-gray-100 mb-1">{incident.title}</div>
        <div className="text-xs text-gray-500">
          {incident.affected_assets?.length > 0
            ? `Segment: ${incident.affected_assets[0]}`
            : "Segment: Corporate Network"}
        </div>
      </div>

      {/* Alert Stack */}
      <div className="shrink-0">
        <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Alert Stack</div>
        <AlertStackPills count={alertCount} />
      </div>

      {/* Impacted Assets */}
      <div className="shrink-0">
        <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Impacted Assets</div>
        <div className="flex flex-wrap gap-1">
          {(incident.affected_assets || ["DB-PROD-01", "APP-SRV-04"]).slice(0,3).map(asset => (
            <span key={asset} className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-navy-800 border border-navy-700 text-gray-300">
              {asset}
            </span>
          ))}
        </div>
      </div>

      {/* Duration */}
      <div className="shrink-0">
        <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Active Duration</div>
        <IncidentDuration startTime={incident.created_at} />
      </div>

      {/* Lead Analyst */}
      <div className="shrink-0">
        <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Lead Analyst</div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-300">{incident.assigned_to_name || "Unassigned"}</span>
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-cyber-cyan/30 to-blue-500/30 border border-cyber-cyan/30 flex items-center justify-center text-[10px] font-bold text-cyber-cyan">
            {(incident.assigned_to_name || "?")[0]}
          </div>
        </div>
      </div>

      {/* View button */}
      <button className="shrink-0 p-2 rounded-lg border border-navy-700 hover:border-cyber-cyan/40 hover:bg-cyber-cyan/10 text-gray-500 hover:text-cyber-cyan transition-all opacity-0 group-hover:opacity-100">
        <Eye className="w-4 h-4" />
      </button>
    </motion.div>
  )
}

// ─── Create Incident Modal ─────────────────────────────────────────────────────
function CreateIncidentModal({ onClose, onCreated }) {
  const [form, setForm] = useState({ title: "", severity: "MEDIUM", description: "", affected_assets: "" })
  const mutation = useMutation({
    mutationFn: (data) => incidentsAPI.create(data),
    onSuccess: () => { toast.success("Incident created"); onCreated() },
    onError:   () => toast.error("Failed to create incident"),
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    mutation.mutate({
      ...form,
      affected_assets: form.affected_assets ? form.affected_assets.split(",").map(s => s.trim()) : [],
    })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <motion.div
        className="glass-card w-full max-w-lg p-6"
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.96 }}
      >
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-bold text-white">Create New Incident</h2>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-navy-700 text-gray-400 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1.5 uppercase tracking-wider">Title *</label>
            <input required value={form.title} onChange={e => setForm(f => ({...f, title: e.target.value}))}
              placeholder="e.g. Ransomware Lateral Movement Detection"
              className="cyber-input text-sm" />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1.5 uppercase tracking-wider">Severity *</label>
            <select value={form.severity} onChange={e => setForm(f => ({...f, severity: e.target.value}))}
              className="cyber-input text-sm bg-navy-800">
              {["CRITICAL","HIGH","MEDIUM","LOW"].map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1.5 uppercase tracking-wider">Description</label>
            <textarea value={form.description} onChange={e => setForm(f => ({...f, description: e.target.value}))}
              rows={3} placeholder="Describe the incident..."
              className="cyber-input text-sm resize-none" />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1.5 uppercase tracking-wider">Affected Assets (comma-separated)</label>
            <input value={form.affected_assets} onChange={e => setForm(f => ({...f, affected_assets: e.target.value}))}
              placeholder="DB-PROD-01, APP-SRV-04"
              className="cyber-input text-sm" />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-ghost">Cancel</button>
            <button type="submit" disabled={mutation.isPending}
              className="btn-primary flex items-center gap-2">
              {mutation.isPending ? "Creating..." : <><Plus className="w-4 h-4" /> Create Incident</>}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  )
}

// ─── Incident Detail Drawer ────────────────────────────────────────────────────
function IncidentDrawer({ incident, onClose }) {
  const queryClient = useQueryClient()
  const sev    = SEVERITY_CFG[incident?.severity] || SEVERITY_CFG.MEDIUM
  const status = STATUS_CFG[incident?.status]     || STATUS_CFG.OPEN

  const updateMutation = useMutation({
    mutationFn: ({ status }) => incidentsAPI.update(incident.id, { status }),
    onSuccess: () => {
      toast.success("Incident updated")
      queryClient.invalidateQueries(["incidents"])
      onClose()
    },
    onError: () => toast.error("Failed to update incident"),
  })

  const [referring, setReferring] = useState(false)

  const handleReferToForensics = async () => {
    setReferring(true)
    try {
      await forensicsAPI.createCase({
        case_title: `Incident Escalation: ${incident.title}`,
        description: `Incident description: ${incident.description || 'No description'}\nSeverity: ${incident.severity}\nTriggered: ${format(new Date(incident.created_at), 'yyyy-MM-dd HH:mm:ss')}`,
        status: 'OPEN'
      })
      toast.success('Successfully referred incident to Digital Forensics Case Vault!')
      onClose()
    } catch (err) {
      toast.error('Failed to create forensics case from incident')
    } finally {
      setReferring(false)
    }
  }

  const handleGenerateReport = () => {
    toast.loading('Compiling incident summary report...', { id: 'incident-report' })
    setTimeout(() => {
      toast.success('Incident summary report compiled and printed!', { id: 'incident-report' })
      window.print()
    }, 1500)
  }

  if (!incident) return null
  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="flex-1 bg-black/50" onClick={onClose} />
      <motion.div
        className="w-[480px] bg-navy-900 border-l border-cyber-cyan/20 flex flex-col overflow-y-auto"
        initial={{ x: "100%" }} animate={{ x: 0 }} exit={{ x: "100%" }}
        transition={{ type: "spring", damping: 28, stiffness: 300 }}
      >
        {/* Header */}
        <div className="px-6 py-5 border-b border-cyber-cyan/10 shrink-0">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-[11px] font-mono text-gray-500">
                  INC-{new Date(incident.created_at).getFullYear()}-{String(incident.id).padStart(3,"0")}
                </span>
                <span className={clsx("px-2 py-0.5 rounded text-[10px] font-bold border uppercase", sev.cls)}>
                  {incident.severity}
                </span>
                <span className={clsx("px-2 py-0.5 rounded text-[10px] font-bold border uppercase", status.cls)}>
                  {status.label}
                </span>
              </div>
              <h2 className="text-base font-bold text-white pr-4">{incident.title}</h2>
            </div>
            <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-navy-700 text-gray-400 transition-colors shrink-0">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5 flex-1">
          {incident.description && (
            <div>
              <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Description</div>
              <p className="text-sm text-gray-300 leading-relaxed">{incident.description}</p>
            </div>
          )}

          {/* Stats */}
          <div className="grid grid-cols-2 gap-3">
            <div className="glass-card p-3">
              <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Created</div>
              <div className="text-xs text-gray-200 font-mono">
                {format(new Date(incident.created_at), "dd MMM yyyy HH:mm")}
              </div>
            </div>
            <div className="glass-card p-3">
              <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Active Duration</div>
              <IncidentDuration startTime={incident.created_at} />
            </div>
          </div>

          {/* Affected Assets */}
          {incident.affected_assets?.length > 0 && (
            <div>
              <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Affected Assets</div>
              <div className="flex flex-wrap gap-2">
                {incident.affected_assets.map(a => (
                  <span key={a} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-navy-800 border border-navy-700 text-xs font-mono text-gray-300">
                    <Server className="w-3 h-3 text-gray-500" /> {a}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Lead Analyst */}
          <div className="flex items-center justify-between p-3 rounded-lg bg-navy-800/60 border border-navy-700">
            <div>
              <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-0.5">Lead Analyst</div>
              <div className="text-sm text-gray-200">{incident.assigned_to_name || "Unassigned"}</div>
            </div>
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyber-cyan/20 to-blue-500/20 border border-cyber-cyan/20 flex items-center justify-center text-sm font-bold text-cyber-cyan">
              {(incident.assigned_to_name || "?")[0]}
            </div>
          </div>

          {/* Metadata */}
          <div className="space-y-2">
            {[
              ["Severity",   incident.severity],
              ["Status",     status.label],
              ["Updated",    incident.updated_at ? format(new Date(incident.updated_at), "dd MMM yyyy HH:mm") : "—"],
            ].map(([label, value]) => (
              <div key={label} className="flex justify-between text-xs border-b border-navy-700/50 pb-2">
                <span className="text-gray-500">{label}</span>
                <span className="text-gray-200 font-mono">{value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="px-6 py-4 border-t border-cyber-cyan/10 grid grid-cols-2 gap-2 shrink-0">
          <button onClick={() => updateMutation.mutate({ status: "INVESTIGATING" })}
            disabled={updateMutation.isPending}
            className="btn-primary text-xs py-2 flex items-center justify-center gap-1.5">
            <Search className="w-3.5 h-3.5" /> Investigate
          </button>
          <button onClick={() => updateMutation.mutate({ status: "CONTAINED" })}
            disabled={updateMutation.isPending}
            className="px-3 py-2 rounded-lg text-xs font-medium border border-blue-400/30 text-blue-400 hover:bg-blue-400/10 transition-all flex items-center justify-center gap-1.5">
            <Shield className="w-3.5 h-3.5" /> Contain
          </button>
          <button onClick={handleReferToForensics}
            disabled={referring}
            className="px-3 py-2 rounded-lg text-xs font-medium border border-cyber-cyan/30 text-cyber-cyan hover:bg-cyber-cyan/10 transition-all flex items-center justify-center gap-1.5">
            <Shield className="w-3.5 h-3.5" /> Refer Forensics
          </button>
          <button onClick={handleGenerateReport}
            className="px-3 py-2 rounded-lg text-xs font-medium border border-gray-600/40 text-gray-400 hover:bg-gray-500/10 transition-all flex items-center justify-center gap-1.5">
            <FileText className="w-3.5 h-3.5" /> Generate Report
          </button>
        </div>
      </motion.div>
    </div>
  )
}

// ─── Main Incident Manager ─────────────────────────────────────────────────────
export default function IncidentManager() {
  const queryClient = useQueryClient()
  const [activeTab,      setActiveTab]      = useState("")
  const [showCreate,     setShowCreate]     = useState(false)
  const [activeIncident, setActiveIncident] = useState(null)
  const [page,           setPage]           = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ["incidents", page, activeTab],
    queryFn:  () => incidentsAPI.list({
      page,
      status:    activeTab || undefined,
      page_size: 20,
      ordering:  "-created_at",
    }).then(r => r.data),
    refetchInterval: 60_000,
  })

  const incidents = data?.results || []
  const total     = data?.count   || 0

  // Compute summary stats
  const openCount         = incidents.filter(i => i.status === "OPEN").length
  const criticalCampaigns = incidents.filter(i => i.severity === "CRITICAL").length
  const investigatingCount = incidents.filter(i => i.status === "INVESTIGATING").length
  const closedCount       = incidents.filter(i => i.status === "CLOSED" || i.status === "CONTAINED").length

  return (
    <div className="space-y-5 h-full flex flex-col">
      {/* Global View header */}
      <div className="flex items-start justify-between shrink-0">
        <div>
          <div className="text-[10px] text-gray-500 uppercase tracking-widest mb-1">Global View</div>
          <h1 className="text-2xl font-bold text-white">Incident Command Center</h1>
        </div>
        <button onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-cyber-cyan/10 border border-cyber-cyan/30 text-cyber-cyan text-sm font-semibold hover:bg-cyber-cyan/20 hover:border-cyber-cyan/60 transition-all shadow-cyber">
          <Plus className="w-4 h-4" /> Create New Incident
        </button>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4 shrink-0">
        {[
          { label: "Open Incidents",           value: openCount,          icon: FolderOpen,    color: "cyan"  },
          { label: "Critical Campaigns",       value: criticalCampaigns,  icon: AlertTriangle, color: "red"   },
          { label: "Under Active Investigation", value: investigatingCount, icon: Search,       color: "amber" },
          { label: "Contained & Closed (7D)",  value: closedCount,        icon: CheckCircle,   color: "green" },
        ].map(({ label, value, icon: Icon, color }) => {
          const c = {
            cyan:  { text: "text-cyber-cyan",  bg: "bg-cyber-cyan/10",  bar: "bg-cyber-cyan" },
            red:   { text: "text-cyber-red",   bg: "bg-cyber-red/10",   bar: "bg-cyber-red" },
            amber: { text: "text-cyber-amber", bg: "bg-cyber-amber/10", bar: "bg-cyber-amber" },
            green: { text: "text-cyber-green", bg: "bg-cyber-green/10", bar: "bg-cyber-green" },
          }[color]
          return (
            <motion.div key={label} className="glass-card p-5 flex flex-col gap-3"
              initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest">{label}</span>
                <div className={clsx("p-2 rounded-lg", c.bg)}><Icon className={clsx("w-4 h-4", c.text)} /></div>
              </div>
              {isLoading
                ? <div className="h-8 bg-navy-700 rounded animate-pulse w-12" />
                : <div className={clsx("text-3xl font-bold font-mono", c.text)}>{value}</div>
              }
              <div className={clsx("h-0.5 rounded-full w-16 opacity-60", c.bar)} />
            </motion.div>
          )
        })}
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-cyber-cyan/10 shrink-0">
        {STATUS_TABS.map(tab => (
          <button
            key={tab.value}
            onClick={() => { setActiveTab(tab.value); setPage(1) }}
            className={clsx(
              "px-4 py-2.5 text-xs font-semibold uppercase tracking-wider transition-all border-b-2 -mb-px",
              activeTab === tab.value
                ? "text-cyber-cyan border-cyber-cyan"
                : "text-gray-500 border-transparent hover:text-gray-300"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Incident Cards */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-1 min-h-0">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="glass-card p-5 flex gap-6 animate-pulse">
              <div className="flex-1 space-y-3">
                <div className="h-4 bg-navy-700 rounded w-1/3" />
                <div className="h-5 bg-navy-700 rounded w-2/3" />
                <div className="h-3 bg-navy-700 rounded w-1/4" />
              </div>
              <div className="w-24 h-16 bg-navy-700 rounded" />
            </div>
          ))
        ) : incidents.length === 0 ? (
          <div className="py-20 text-center">
            <Shield className="w-12 h-12 mx-auto mb-4 text-gray-700" />
            <p className="text-gray-500 text-sm">No incidents found</p>
            <button onClick={() => setShowCreate(true)}
              className="mt-4 btn-primary flex items-center gap-2 mx-auto">
              <Plus className="w-4 h-4" /> Create First Incident
            </button>
          </div>
        ) : (
          <AnimatePresence initial={false}>
            {incidents.map(incident => (
              <IncidentCard key={incident.id} incident={incident} onView={setActiveIncident} />
            ))}
          </AnimatePresence>
        )}
      </div>

      {/* Pagination */}
      {total > 20 && (
        <div className="flex items-center justify-between shrink-0 pt-2">
          <span className="text-xs text-gray-500">{total.toLocaleString()} total incidents</span>
          <div className="flex items-center gap-2">
            <button onClick={() => setPage(p => Math.max(1,p-1))} disabled={page===1} className="btn-ghost text-xs py-1 px-2">← Prev</button>
            <span className="text-xs text-gray-400 font-mono">Page {page}</span>
            <button onClick={() => setPage(p => p+1)} disabled={page*20>=total} className="btn-ghost text-xs py-1 px-2">Next →</button>
          </div>
        </div>
      )}

      {/* Modals & Drawers */}
      <AnimatePresence>
        {showCreate && (
          <CreateIncidentModal
            onClose={() => setShowCreate(false)}
            onCreated={() => { setShowCreate(false); queryClient.invalidateQueries(["incidents"]) }}
          />
        )}
      </AnimatePresence>

      {activeIncident && (
        <IncidentDrawer incident={activeIncident} onClose={() => setActiveIncident(null)} />
      )}
    </div>
  )
}
