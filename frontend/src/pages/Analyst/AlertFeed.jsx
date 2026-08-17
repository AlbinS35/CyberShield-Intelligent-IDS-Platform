import { useState, useEffect, useCallback } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { motion, AnimatePresence } from "framer-motion"
import {
  AlertTriangle, XCircle, ClipboardList, CheckCircle2,
  Search, Download, CheckCheck, ChevronRight, RefreshCw,
  Eye, Shield
} from "lucide-react"
import { alertsAPI } from "../../api"
import { format } from "date-fns"
import toast from "react-hot-toast"
import { clsx } from "clsx"
import { useSocket } from "../../context/SocketContext"

const SEVERITY_CONFIG = {
  CRITICAL: { label: "Critical", cls: "badge-critical" },
  HIGH:     { label: "High",     cls: "badge-high" },
  MEDIUM:   { label: "Medium",   cls: "badge-medium" },
  LOW:      { label: "Low",      cls: "badge-low" },
  INFO:     { label: "Info",     cls: "badge-info" },
}

const STATUS_CONFIG = {
  NEW:            { label: "New",          cls: "text-cyber-red" },
  ACKNOWLEDGED:   { label: "Acknowledged", cls: "text-cyber-amber" },
  IN_PROGRESS:    { label: "In Progress",  cls: "text-blue-400" },
  RESOLVED:       { label: "Resolved",     cls: "text-cyber-green" },
  FALSE_POSITIVE: { label: "False Pos.",   cls: "text-gray-500" },
  ESCALATED:      { label: "Escalated",    cls: "text-purple-400" },
}

const CLASS_OPTIONS = [
  { value: "", label: "All Classes" },
  { value: "dos",   label: "DoS" },
  { value: "probe", label: "Probe" },
  { value: "r2l",   label: "R2L" },
  { value: "u2r",   label: "U2R" },
]

function StatCard({ icon: Icon, label, value, color, loading }) {
  const c = {
    cyan:  { text: "text-cyber-cyan",  bg: "bg-cyber-cyan/10",  bar: "bg-cyber-cyan" },
    red:   { text: "text-cyber-red",   bg: "bg-cyber-red/10",   bar: "bg-cyber-red" },
    amber: { text: "text-cyber-amber", bg: "bg-cyber-amber/10", bar: "bg-cyber-amber" },
    green: { text: "text-cyber-green", bg: "bg-cyber-green/10", bar: "bg-cyber-green" },
  }[color] || { text: "text-cyber-cyan", bg: "bg-cyber-cyan/10", bar: "bg-cyber-cyan" }

  return (
    <motion.div
      className="glass-card p-5 flex flex-col gap-3"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest">{label}</span>
        <div className={clsx("p-2 rounded-lg", c.bg)}>
          <Icon className={clsx("w-4 h-4", c.text)} />
        </div>
      </div>
      {loading
        ? <div className="h-8 bg-navy-700 rounded animate-pulse w-16" />
        : <div className={clsx("text-3xl font-bold font-mono", c.text)}>{value}</div>
      }
      <div className={clsx("h-0.5 rounded-full w-16 opacity-60", c.bar)} />
    </motion.div>
  )
}

function AlertRow({ alert, isNew, selected, onSelect, onView }) {
  const sev    = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.INFO
  const status = STATUS_CONFIG[alert.status]     || { label: alert.status, cls: "text-gray-400" }
  return (
    <motion.div
      initial={isNew ? { opacity: 0, x: 16, backgroundColor: "rgba(0,245,255,0.07)" } : { opacity: 0 }}
      animate={{ opacity: 1, x: 0, backgroundColor: "transparent" }}
      transition={{ duration: 0.35 }}
      className={clsx(
        "flex items-center gap-4 px-5 py-3.5 border-b border-navy-700/40",
        "hover:bg-navy-700/30 transition-colors group",
        selected && "bg-cyber-cyan/5 border-l-2 border-l-cyber-cyan"
      )}
    >
      <input type="checkbox" checked={selected} onChange={() => onSelect(alert.id)}
        className="w-3.5 h-3.5 accent-cyber-cyan rounded shrink-0" onClick={e => e.stopPropagation()} />
      <div className={clsx("w-2 h-2 rounded-full shrink-0", {
        "bg-cyber-red animate-pulse": alert.severity === "CRITICAL",
        "bg-orange-500":              alert.severity === "HIGH",
        "bg-cyber-amber":             alert.severity === "MEDIUM",
        "bg-blue-400":                alert.severity === "LOW",
        "bg-gray-500":                alert.severity === "INFO",
      })} />
      <div className="flex-1 min-w-0 grid grid-cols-12 gap-3 items-center">
        <div className="col-span-5 flex items-center gap-2 min-w-0">
          <span className={sev.cls}>{sev.label}</span>
          <span className="text-sm text-gray-200 truncate font-medium">{alert.title}</span>
        </div>
        <div className="col-span-3 flex items-center gap-2 text-xs font-mono text-gray-500">
          <span className="truncate">{alert.source_ip || "—"}</span>
          <span className="text-gray-700">?</span>
          <span className="truncate">{alert.destination_ip || "—"}</span>
        </div>
        <div className="col-span-2">
          <span className={clsx("text-xs font-semibold", status.cls)}>{status.label}</span>
        </div>
        <div className="col-span-2 text-right">
          <span className="text-[11px] text-gray-600 font-mono">
            {format(new Date(alert.created_at), "HH:mm:ss")}
          </span>
        </div>
      </div>
      <button onClick={() => onView(alert)}
        className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-lg hover:bg-cyber-cyan/10 text-cyber-cyan shrink-0">
        <ChevronRight className="w-4 h-4" />
      </button>
    </motion.div>
  )
}

function AlertDrawer({ alert, onClose }) {
  const queryClient = useQueryClient()
  const sev = SEVERITY_CONFIG[alert?.severity] || SEVERITY_CONFIG.INFO

  const updateMutation = useMutation({
    mutationFn: ({ status }) => alertsAPI.updateStatus(alert.id, { status }),
    onSuccess: () => {
      toast.success("Alert status updated")
      queryClient.invalidateQueries(["alerts", "feed"])
      onClose()
    },
    onError: () => toast.error("Failed to update alert"),
  })

  if (!alert) return null
  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="flex-1 bg-black/50" onClick={onClose} />
      <motion.div
        className="w-96 bg-navy-900 border-l border-cyber-cyan/20 flex flex-col overflow-y-auto"
        initial={{ x: "100%" }} animate={{ x: 0 }} exit={{ x: "100%" }}
        transition={{ type: "spring", damping: 28, stiffness: 300 }}
      >
        <div className="px-5 py-4 border-b border-cyber-cyan/10 flex items-center justify-between shrink-0">
          <div>
            <div className="flex items-center gap-2">
              <span className={sev.cls}>{sev.label}</span>
              <span className="text-xs text-gray-500 font-mono">{String(alert.id).slice(0,8)}</span>
            </div>
            <div className="text-sm font-semibold text-gray-100 mt-1 pr-4">{alert.title}</div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-navy-700 text-gray-400 transition-colors shrink-0">
            <XCircle className="w-4 h-4" />
          </button>
        </div>
        <div className="p-5 space-y-4 flex-1">
          <div className="glass-card p-4">
            <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-3">Network Routing</div>
            <div className="flex items-center justify-between text-xs font-mono">
              <div><div className="text-gray-500 mb-0.5">Source</div><div className="text-cyber-cyan">{alert.source_ip || "—"}</div></div>
              <ChevronRight className="w-3 h-3 text-gray-600" />
              <div className="text-right"><div className="text-gray-500 mb-0.5">Destination</div><div className="text-gray-200">{alert.destination_ip || "—"}</div></div>
            </div>
          </div>
          <div className="space-y-2.5">
            {[
              ["Protocol",    alert.protocol],
              ["Status",      STATUS_CONFIG[alert.status]?.label || alert.status],
              ["ML Class",    alert.ml_classification || "—"],
              ["Confidence",  alert.ml_confidence ? `${(alert.ml_confidence*100).toFixed(1)}%` : "—"],
              ["Agent",       alert.agent_hostname || "—"],
              ["Detected At", format(new Date(alert.created_at), "dd MMM yyyy HH:mm:ss")],
            ].map(([label, value]) => (
              <div key={label} className="flex justify-between items-center text-xs border-b border-navy-700/50 pb-2">
                <span className="text-gray-500">{label}</span>
                <span className="text-gray-200 font-mono">{value || "—"}</span>
              </div>
            ))}
          </div>
          {alert.description && (
            <div>
              <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Description</div>
              <p className="text-xs text-gray-400 leading-relaxed">{alert.description}</p>
            </div>
          )}
        </div>
        <div className="px-5 py-4 border-t border-cyber-cyan/10 grid grid-cols-2 gap-2 shrink-0">
          <button onClick={() => updateMutation.mutate({ status: "ACKNOWLEDGED" })}
            disabled={updateMutation.isPending}
            className="btn-primary text-xs py-2 flex items-center justify-center gap-1.5">
            <CheckCheck className="w-3.5 h-3.5" /> Acknowledge
          </button>
          <button onClick={() => updateMutation.mutate({ status: "RESOLVED" })}
            disabled={updateMutation.isPending}
            className="px-3 py-2 rounded-lg text-xs font-medium border border-cyber-green/30 text-cyber-green hover:bg-cyber-green/10 transition-all flex items-center justify-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" /> Resolve
          </button>
          <button onClick={() => updateMutation.mutate({ status: "IN_PROGRESS" })}
            disabled={updateMutation.isPending}
            className="px-3 py-2 rounded-lg text-xs font-medium border border-blue-400/30 text-blue-400 hover:bg-blue-400/10 transition-all flex items-center justify-center gap-1.5">
            <Eye className="w-3.5 h-3.5" /> Investigate
          </button>
          <button onClick={() => updateMutation.mutate({ status: "FALSE_POSITIVE" })}
            disabled={updateMutation.isPending}
            className="px-3 py-2 rounded-lg text-xs font-medium border border-gray-600/40 text-gray-400 hover:bg-gray-500/10 transition-all flex items-center justify-center gap-1.5">
            <Shield className="w-3.5 h-3.5" /> False Pos.
          </button>
        </div>
      </motion.div>
    </div>
  )
}

export default function AlertFeed() {
  const queryClient = useQueryClient()
  const { subscribe } = useSocket()

  const [search,      setSearch]      = useState("")
  const [severity,    setSeverity]    = useState("")
  const [alertClass,  setAlertClass]  = useState("")
  const [page,        setPage]        = useState(1)
  const [selected,    setSelected]    = useState(new Set())
  const [newAlertIds, setNewAlertIds] = useState(new Set())
  const [activeAlert, setActiveAlert] = useState(null)

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["alerts", "feed", page, search, severity, alertClass],
    queryFn:  () => alertsAPI.list({ page, search: search || undefined, severity: severity || undefined, page_size: 30, ordering: "-created_at" }).then(r => r.data),
    keepPreviousData: true,
    refetchInterval: 30_000,
  })

  useEffect(() => {
    const unsub = subscribe("alert-feed", (alert) => {
      setNewAlertIds(prev => new Set([...prev, alert.id]))
      setTimeout(() => setNewAlertIds(prev => { const n = new Set(prev); n.delete(alert.id); return n }), 4000)
      refetch()
    })
    return unsub
  }, [subscribe, refetch])

  const alerts   = data?.results || []
  const total    = data?.count   || 0
  const critical = alerts.filter(a => a.severity === "CRITICAL").length
  const pending  = alerts.filter(a => a.status   === "NEW").length
  const resolved = alerts.filter(a => a.status   === "RESOLVED").length

  const bulkAckMutation = useMutation({
    mutationFn: async () => { await Promise.all([...selected].map(id => alertsAPI.updateStatus(id, { status: "ACKNOWLEDGED" }))) },
    onSuccess:  () => { toast.success(`${selected.size} alert(s) acknowledged`); setSelected(new Set()); queryClient.invalidateQueries(["alerts","feed"]) },
    onError:    () => toast.error("Bulk acknowledge failed"),
  })

  const handleExport = () => {
    const csv = [
      ["ID","Severity","Title","Source IP","Dest IP","Status","Timestamp"].join(","),
      ...alerts.map(a => [a.id, a.severity, `"${a.title}"`, a.source_ip||"", a.destination_ip||"", a.status, format(new Date(a.created_at),"yyyy-MM-dd HH:mm:ss")].join(","))
    ].join("\n")
    const blob = new Blob([csv], { type: "text/csv" })
    const url  = URL.createObjectURL(blob)
    const el   = document.createElement("a")
    el.href = url; el.download = `alerts-${format(new Date(),"yyyyMMdd")}.csv`; el.click()
    URL.revokeObjectURL(url)
    toast.success("CSV exported")
  }

  const toggleSelect = useCallback(id => {
    setSelected(prev => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n })
  }, [])

  const toggleAll = () => {
    setSelected(selected.size === alerts.length ? new Set() : new Set(alerts.map(a => a.id)))
  }

  return (
    <div className="space-y-5 h-full flex flex-col">
      {/* Stat Cards */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4 shrink-0">
        <StatCard icon={AlertTriangle} label="Total Active Alerts" value={total}    color="cyan"  loading={isLoading} />
        <StatCard icon={XCircle}       label="Critical Threats"    value={critical} color="red"   loading={isLoading} />
        <StatCard icon={ClipboardList} label="Pending Review"      value={pending}  color="amber" loading={isLoading} />
        <StatCard icon={CheckCircle2}  label="Resolved Today"      value={resolved} color="green" loading={isLoading} />
      </div>

      {/* Filter Bar */}
      <div className="glass-card px-4 py-3 flex flex-wrap items-center gap-3 shrink-0">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500" />
          <input type="text" value={search} onChange={e => { setSearch(e.target.value); setPage(1) }}
            placeholder="Search IP, Hash, or UUID..." className="cyber-input pl-9 text-xs h-9" />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-gray-500 uppercase tracking-wider font-semibold">Severity:</span>
          <select value={severity} onChange={e => { setSeverity(e.target.value); setPage(1) }}
            className="cyber-input text-xs h-9 w-28 bg-navy-800">
            <option value="">All</option>
            {Object.entries(SEVERITY_CONFIG).map(([k,v]) => <option key={k} value={k}>{v.label}</option>)}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-gray-500 uppercase tracking-wider font-semibold">Class:</span>
          <select value={alertClass} onChange={e => { setAlertClass(e.target.value); setPage(1) }}
            className="cyber-input text-xs h-9 w-36 bg-navy-800">
            {CLASS_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <div className="h-6 w-px bg-navy-700 hidden sm:block" />
        <button onClick={() => bulkAckMutation.mutate()} disabled={selected.size === 0 || bulkAckMutation.isPending}
          className={clsx("flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-all border",
            selected.size > 0 ? "bg-cyber-cyan/10 text-cyber-cyan border-cyber-cyan/30 hover:bg-cyber-cyan/20"
                              : "bg-navy-800 text-gray-600 border-navy-700 cursor-not-allowed")}>
          {bulkAckMutation.isPending ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <CheckCheck className="w-3.5 h-3.5" />}
          Bulk Ack{selected.size > 0 ? ` (${selected.size})` : ""}
        </button>
        <button onClick={handleExport}
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold bg-cyber-cyan text-navy-950 hover:bg-cyber-cyan/90 transition-colors">
          <Download className="w-3.5 h-3.5" /> Export CSV
        </button>
      </div>

      {/* Alert List */}
      <div className="glass-card flex-1 overflow-hidden flex flex-col min-h-0">
        <div className="flex items-center gap-4 px-5 py-3 border-b border-cyber-cyan/10 shrink-0">
          <input type="checkbox" checked={alerts.length > 0 && selected.size === alerts.length} onChange={toggleAll}
            className="w-3.5 h-3.5 accent-cyber-cyan rounded" />
          <div className="w-2" />
          <div className="flex-1 grid grid-cols-12 gap-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">
            <div className="col-span-5">Alert</div>
            <div className="col-span-3">Routing</div>
            <div className="col-span-2">Status</div>
            <div className="col-span-2 text-right">Time</div>
          </div>
          <div className="w-7" />
        </div>
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="flex items-center gap-4 px-5 py-4 border-b border-navy-700/30">
                <div className="w-3.5 h-3.5 bg-navy-700 rounded animate-pulse" />
                <div className="w-2 h-2 rounded-full bg-navy-700 animate-pulse" />
                <div className="flex-1 space-y-1.5">
                  <div className="h-3 bg-navy-700 rounded animate-pulse w-2/3" />
                  <div className="h-2.5 bg-navy-700 rounded animate-pulse w-1/3" />
                </div>
              </div>
            ))
          ) : alerts.length === 0 ? (
            <div className="py-20 text-center">
              <Shield className="w-10 h-10 mx-auto mb-3 text-gray-700" />
              <p className="text-gray-600 text-sm">No alerts found matching your filters</p>
              <button onClick={() => { setSearch(""); setSeverity(""); setAlertClass("") }}
                className="mt-3 text-xs text-cyber-cyan hover:underline">Clear filters</button>
            </div>
          ) : (
            alerts.map(alert => (
              <AlertRow key={alert.id} alert={alert} isNew={newAlertIds.has(alert.id)}
                selected={selected.has(alert.id)} onSelect={toggleSelect} onView={setActiveAlert} />
            ))
          )}
        </div>
        {total > 30 && (
          <div className="px-5 py-3 border-t border-cyber-cyan/10 flex items-center justify-between shrink-0">
            <span className="text-xs text-gray-500">
              Showing {((page-1)*30)+1}–{Math.min(page*30, total)} of {total.toLocaleString()} alerts
            </span>
            <div className="flex items-center gap-2">
              <button onClick={() => setPage(p => Math.max(1, p-1))} disabled={page === 1} className="btn-ghost text-xs py-1 px-2">? Prev</button>
              <span className="text-xs text-gray-400 font-mono">{page}/{Math.ceil(total/30)}</span>
              <button onClick={() => setPage(p => p+1)} disabled={page*30 >= total} className="btn-ghost text-xs py-1 px-2">Next ?</button>
            </div>
          </div>
        )}
      </div>

      {activeAlert && <AlertDrawer alert={activeAlert} onClose={() => setActiveAlert(null)} />}
    </div>
  )
}
