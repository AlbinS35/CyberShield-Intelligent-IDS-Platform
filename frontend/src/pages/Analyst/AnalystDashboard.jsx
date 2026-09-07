import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import {
  AlertTriangle, ShieldCheck, Activity, Zap,
  TrendingUp, Clock, Eye, ChevronRight
} from 'lucide-react'
import {
  AreaChart, Area, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'
import { alertsAPI, mlAPI, networkEventsAPI } from '../../api'
import { useSocket } from '../../context/SocketContext'
import { format } from 'date-fns'
import toast from 'react-hot-toast'
import { clsx } from 'clsx'

// ─── Severity Config ──────────────────────────────────────────────────────────
const SEVERITY_CONFIG = {
  CRITICAL: { label: 'Critical', color: '#FF3366', bg: 'bg-red-500/10',    border: 'border-red-500/30',    cls: 'badge-critical' },
  HIGH:     { label: 'High',     color: '#FF6B35', bg: 'bg-orange-500/10', border: 'border-orange-500/30', cls: 'badge-high' },
  MEDIUM:   { label: 'Medium',   color: '#FFB800', bg: 'bg-amber-500/10',  border: 'border-amber-500/30',  cls: 'badge-medium' },
  LOW:      { label: 'Low',      color: '#3B82F6', bg: 'bg-blue-500/10',   border: 'border-blue-500/30',   cls: 'badge-low' },
  INFO:     { label: 'Info',     color: '#6B7280', bg: 'bg-gray-500/10',   border: 'border-gray-500/30',   cls: 'badge-info' },
}

const STATUS_COLORS = {
  NEW:           'text-cyber-red',
  ACKNOWLEDGED:  'text-cyber-amber',
  IN_PROGRESS:   'text-blue-400',
  RESOLVED:      'text-cyber-green',
  FALSE_POSITIVE:'text-gray-500',
  ESCALATED:     'text-cyber-purple',
}

// ─── Metric Card Component ────────────────────────────────────────────────────
function MetricCard({ icon: Icon, label, value, delta, color = 'cyan', loading }) {
  const colorMap = { cyan: 'text-cyber-cyan', green: 'text-cyber-green', red: 'text-cyber-red', amber: 'text-cyber-amber' }
  return (
    <motion.div
      className="metric-card"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className={clsx('p-2 rounded-lg bg-current/10', colorMap[color])}>
          <Icon className="w-4 h-4" />
        </div>
        {delta !== undefined && (
          <span className={clsx('text-xs font-mono', delta >= 0 ? 'text-cyber-red' : 'text-cyber-green')}>
            {delta >= 0 ? '+' : ''}{delta}%
          </span>
        )}
      </div>
      <div className={clsx('text-2xl font-bold font-mono', colorMap[color])}>
        {loading ? <span className="w-12 h-6 bg-navy-700 rounded animate-pulse block" /> : value}
      </div>
      <div className="text-xs text-gray-500 mt-0.5">{label}</div>
    </motion.div>
  )
}

// ─── Alert Row Component ──────────────────────────────────────────────────────
function AlertRow({ alert, isNew }) {
  const sev = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.INFO
  return (
    <motion.div
      initial={isNew ? { opacity: 0, x: 20, backgroundColor: 'rgba(0,245,255,0.1)' } : false}
      animate={{ opacity: 1, x: 0, backgroundColor: 'transparent' }}
      transition={{ duration: 0.5 }}
      className="flex items-center gap-4 px-4 py-3 hover:bg-navy-700/40 rounded-lg transition-colors cursor-pointer group"
    >
      <div className={clsx('w-2 h-2 rounded-full shrink-0', {
        'bg-cyber-red animate-pulse': alert.severity === 'CRITICAL',
        'bg-orange-500': alert.severity === 'HIGH',
        'bg-cyber-amber': alert.severity === 'MEDIUM',
        'bg-blue-400': alert.severity === 'LOW',
        'bg-gray-500': alert.severity === 'INFO',
      })} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className={sev.cls}>{sev.label}</span>
          <span className="text-sm text-gray-200 truncate">{alert.title}</span>
        </div>
        <div className="flex items-center gap-3 mt-0.5">
          <span className="text-xs text-gray-500 font-mono">{alert.source_ip || 'N/A'}</span>
          <span className="text-xs text-gray-600">→</span>
          <span className="text-xs text-gray-500 font-mono">{alert.destination_ip || 'N/A'}</span>
          <span className={clsx('text-xs font-medium ml-auto', STATUS_COLORS[alert.status])}>
            {alert.status}
          </span>
        </div>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <span className="text-[10px] text-gray-600 font-mono">
          {format(new Date(alert.created_at), 'HH:mm:ss')}
        </span>
        <Link
          to={`/analyst/alerts/${alert.id}`}
          className="opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <ChevronRight className="w-4 h-4 text-cyber-cyan" />
        </Link>
      </div>
    </motion.div>
  )
}

// ─── Main Analyst Dashboard ───────────────────────────────────────────────────
export default function AnalystDashboard() {
  const { subscribe, latestAlert } = useSocket()
  const [liveAlerts, setLiveAlerts] = useState([])
  const [newAlertIds, setNewAlertIds] = useState(new Set())

  // Fetch alert list
  const { data: alertsData, isLoading: alertsLoading, refetch: refetchAlerts } = useQuery({
    queryKey: ['alerts', 'dashboard'],
    queryFn: () => alertsAPI.list({ page_size: 20, ordering: '-created_at' }).then(r => r.data),
    refetchInterval: 5000,
  })

  // Fetch ML stats
  const { data: mlStats } = useQuery({
    queryKey: ['ml-stats'],
    queryFn: () => mlAPI.stats().then(r => r.data),
    refetchInterval: 10_000,
  })

  // Subscribe to live WebSocket alerts
  useEffect(() => {
    const unsub = subscribe('analyst-dashboard', (alert) => {
      setLiveAlerts(prev => [alert, ...prev].slice(0, 50))
      setNewAlertIds(prev => new Set([...prev, alert.id]))
      toast.custom((t) => (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className={clsx(
            'glass-card px-4 py-3 flex items-center gap-3 min-w-64',
            alert.severity === 'CRITICAL' && 'border-cyber-red/40'
          )}
        >
          <AlertTriangle className={clsx('w-4 h-4 shrink-0', {
            'text-cyber-red': alert.severity === 'CRITICAL',
            'text-cyber-amber': alert.severity === 'MEDIUM',
          })} />
          <div>
            <div className="text-xs font-semibold text-gray-200">{alert.severity} Alert</div>
            <div className="text-xs text-gray-400 truncate max-w-48">{alert.title}</div>
          </div>
        </motion.div>
      ), { duration: 5000 })
      setTimeout(() => setNewAlertIds(prev => { const n = new Set(prev); n.delete(alert.id); return n }), 3000)
      refetchAlerts()
    })
    return unsub
  }, [subscribe, refetchAlerts])

  // Combine live + fetched alerts
  const allAlerts = alertsData?.results || []

  // Severity distribution for donut chart
  const severityData = Object.entries(SEVERITY_CONFIG).map(([key, cfg]) => ({
    name: cfg.label,
    value: allAlerts.filter(a => a.severity === key).length,
    color: cfg.color,
  })).filter(d => d.value > 0)

  // Mock traffic time series (replace with real API)
  const trafficData = Array.from({ length: 12 }, (_, i) => ({
    time: `${String(i * 2).padStart(2, '0')}:00`,
    events: Math.floor(Math.random() * 800 + 200),
    threats: Math.floor(Math.random() * 80 + 10),
  }))

  const totalAlerts   = allAlerts.length
  const criticalCount = allAlerts.filter(a => a.severity === 'CRITICAL').length
  const newCount      = allAlerts.filter(a => a.status === 'NEW').length
  const resolvedCount = allAlerts.filter(a => a.status === 'RESOLVED').length

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Security Operations Center</h1>
          <p className="text-sm text-gray-500 mt-0.5">Real-time threat monitoring dashboard</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 text-xs text-cyber-green font-mono">
            <span className="status-dot-online" />
            LIVE MONITORING
          </div>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <MetricCard icon={AlertTriangle} label="Total Alerts"    value={totalAlerts}   color="cyan"  loading={alertsLoading} />
        <MetricCard icon={Zap}          label="Critical Threats" value={criticalCount}  color="red"   loading={alertsLoading} />
        <MetricCard icon={Clock}        label="Pending Review"   value={newCount}       color="amber" loading={alertsLoading} />
        <MetricCard icon={ShieldCheck}  label="Resolved Today"   value={resolvedCount}  color="green" loading={alertsLoading} />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Traffic Time Series */}
        <div className="glass-card p-5 xl:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-200">Network Traffic & Threat Events</h2>
            <span className="text-[10px] text-gray-500 font-mono">Last 24h</span>
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={trafficData}>
              <defs>
                <linearGradient id="eventsGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#00F5FF" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#00F5FF" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="threatsGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#FF3366" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#FF3366" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="time" tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={false} />
              <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: '#111827', border: '1px solid rgba(0,245,255,0.2)', borderRadius: 8, fontSize: 12 }}
                labelStyle={{ color: '#9ca3af' }}
              />
              <Area type="monotone" dataKey="events"  stroke="#00F5FF" fill="url(#eventsGrad)"  strokeWidth={1.5} name="Events" />
              <Area type="monotone" dataKey="threats" stroke="#FF3366" fill="url(#threatsGrad)" strokeWidth={1.5} name="Threats" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Severity Donut */}
        <div className="glass-card p-5">
          <h2 className="text-sm font-semibold text-gray-200 mb-4">Alert Severity Distribution</h2>
          {severityData.length > 0 ? (
            <ResponsiveContainer width="100%" height={160}>
              <PieChart>
                <Pie data={severityData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} paddingAngle={3} dataKey="value">
                  {severityData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} opacity={0.85} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#111827', border: '1px solid rgba(0,245,255,0.2)', borderRadius: 8, fontSize: 12 }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-40 flex items-center justify-center text-gray-600 text-sm">No alerts</div>
          )}
          <div className="mt-2 space-y-1">
            {severityData.map(d => (
              <div key={d.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full" style={{ background: d.color }} />
                  <span className="text-gray-400">{d.name}</span>
                </div>
                <span className="font-mono text-gray-300">{d.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ML Model Stats */}
      {mlStats && (
        <div className="glass-card p-5">
          <h2 className="text-sm font-semibold text-gray-200 mb-3">AI/ML Engine Status</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
            <div>
              <div className="text-gray-500">Model Type</div>
              <div className="font-mono text-cyber-cyan mt-0.5">{mlStats.model_info?.model_type || 'N/A'}</div>
            </div>
            <div>
              <div className="text-gray-500">Total Inferences</div>
              <div className="font-mono text-gray-200 mt-0.5">{mlStats.tenant_stats?.total_inferences}</div>
            </div>
            <div>
              <div className="text-gray-500">Avg Confidence</div>
              <div className="font-mono text-cyber-green mt-0.5">
                {((mlStats.tenant_stats?.avg_confidence || 0) * 100).toFixed(1)}%
              </div>
            </div>
            <div>
              <div className="text-gray-500">Avg Latency</div>
              <div className="font-mono text-gray-200 mt-0.5">
                {mlStats.tenant_stats?.avg_inference_time_ms?.toFixed(1) || '—'}ms
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Live Alert Feed */}
      <div className="glass-card">
        <div className="flex items-center justify-between px-5 py-4 border-b border-cyber-cyan/10">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyber-cyan" />
            <h2 className="text-sm font-semibold text-gray-200">Live Alert Feed</h2>
            {liveAlerts.length > 0 && (
              <span className="px-1.5 py-0.5 text-[10px] font-mono bg-cyber-red/15 text-cyber-red rounded-full border border-cyber-red/30">
                +{liveAlerts.length} NEW
              </span>
            )}
          </div>
          <Link to="/analyst/alerts" className="text-xs text-cyber-cyan hover:underline flex items-center gap-1">
            View All <ChevronRight className="w-3 h-3" />
          </Link>
        </div>
        <div className="divide-y divide-navy-700/50 py-1">
          {alertsLoading ? (
            Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="px-4 py-3 flex items-center gap-4">
                <div className="w-2 h-2 rounded-full bg-navy-700 animate-pulse" />
                <div className="flex-1 space-y-1.5">
                  <div className="h-3 bg-navy-700 rounded animate-pulse w-3/4" />
                  <div className="h-2.5 bg-navy-700 rounded animate-pulse w-1/2" />
                </div>
              </div>
            ))
          ) : allAlerts.length === 0 ? (
            <div className="py-12 text-center text-gray-600">
              <ShieldCheck className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm">No alerts detected. System is clear.</p>
            </div>
          ) : (
            allAlerts.slice(0, 15).map(alert => (
              <AlertRow key={alert.id} alert={alert} isNew={newAlertIds.has(alert.id)} />
            ))
          )}
        </div>
      </div>
    </div>
  )
}
