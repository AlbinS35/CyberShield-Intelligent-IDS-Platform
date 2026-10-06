import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ShieldAlert, Activity, Shield, Plus, Power, Trash2, Edit2, Play,
  Terminal, ShieldCheck, Clock, CheckCircle, XCircle, Search, Copy, User
} from 'lucide-react'
import { playbooksAPI, blocklistAPI } from '../../api'
import axios from '../../api/axios' // direct fetch helper for execution audits
import toast from 'react-hot-toast'
import { clsx } from 'clsx'
import { format } from 'date-fns'
import { useAuth } from '../../context/AuthContext'

const SEVERITY_COLORS = {
  CRITICAL: 'text-red-400 bg-red-500/10 border-red-500/20',
  HIGH:     'text-orange-400 bg-orange-500/10 border-orange-500/20',
  MEDIUM:   'text-amber-400 bg-amber-500/10 border-amber-500/20',
  LOW:      'text-blue-400 bg-blue-500/10 border-blue-500/20',
  INFO:     'text-gray-400 bg-gray-500/10 border-gray-500/20',
}

export default function PlaybookManager() {
  const { user: currentUser } = useAuth()
  const [activeTab, setActiveTab] = useState('playbooks') // 'playbooks', 'blocklist', 'executions', 'users', 'rules'
  const [showPlaybookModal, setShowPlaybookModal] = useState(false)
  const [editingPlaybook, setEditingPlaybook] = useState(null)
  const [savingPlaybook, setSavingPlaybook] = useState(false)

  // Blocklist states
  const [showBlockModal, setShowBlockModal] = useState(false)
  const [blockIp, setBlockIp] = useState('')
  const [blockReason, setBlockReason] = useState('')
  const [blocking, setBlocking] = useState(false)

  // User management states
  const [showUserModal, setShowUserModal] = useState(false)
  const [userForm, setUserForm] = useState({ email: '', password: '', role: 'Analyst', status: 'ACTIVE', user: '' })
  const [savingUser, setSavingUser] = useState(false)

  // Execution detailed log modal
  const [selectedExecution, setSelectedExecution] = useState(null)

  // Playbook Form State
  const [playbookForm, setPlaybookForm] = useState({
    name: '',
    description: '',
    trigger_mode: 'MANUAL',
    trigger_severity: 'HIGH',
    commands: [''],
    is_active: true
  })

  // Queries
  const { data: playbooks, isLoading: playbooksLoading, refetch: refetchPlaybooks } = useQuery({
    queryKey: ['playbooks'],
    queryFn: () => playbooksAPI.list().then(r => r.data?.results || r.data || []),
    refetchInterval: 5000, // Fetch every 5 seconds
  })

  const { data: blocklist, isLoading: blocklistLoading, refetch: refetchBlocklist } = useQuery({
    queryKey: ['blocklist'],
    queryFn: () => blocklistAPI.list().then(r => r.data?.results || r.data || []),
    refetchInterval: 5000,
  })

  const { data: executions, isLoading: executionsLoading, refetch: refetchExecutions } = useQuery({
    queryKey: ['playbook-executions'],
    queryFn: () => axios.get('/detection/executions/').then(r => r.data?.results || r.data || []),
    refetchInterval: 3000,
  })

  const { data: users, isLoading: usersLoading, refetch: refetchUsers } = useQuery({
    queryKey: ['admin-users-list'],
    queryFn: () => axios.get('/core/logins/').then(r => r.data?.results || r.data || []),
    refetchInterval: 10000,
  })

  const { data: coreUsers } = useQuery({
    queryKey: ['admin-core-users'],
    queryFn: () => axios.get('/core/users/').then(r => r.data?.results || r.data || []),
    refetchInterval: 30000,
  })

  const handleCreateUser = async (e) => {
    e.preventDefault()
    setSavingUser(true)
    try {
      await axios.post('/core/logins/', {
        user: userForm.user,
        email: userForm.email,
        password: userForm.password || 'TemporaryPassword@2024',
        role: userForm.role,
        status: userForm.status
      })
      toast.success('User credentials created successfully!')
      setShowUserModal(false)
      setUserForm({ email: '', password: '', role: 'Analyst', status: 'ACTIVE', user: '' })
      refetchUsers()
    } catch (err) {
      toast.error(err.response?.data ? JSON.stringify(err.response.data) : 'Failed to register user credentials')
    } finally {
      setSavingUser(false)
    }
  }

  const handleEditUser = (u) => {
    toast.error("Edit user functionality coming soon.")
  }

  const handleDeleteUser = async (login_id) => {
    if (!window.confirm("Are you sure you want to delete this user? This cannot be undone.")) return
    try {
      await axios.delete(`/core/logins/${login_id}/`)
      toast.success("User deleted successfully.")
      refetchUsers()
    } catch (err) {
      toast.error("Failed to delete user.")
    }
  }

  // Playbook Handlers
  const handleOpenPlaybookModal = (playbook = null) => {
    if (playbook) {
      setEditingPlaybook(playbook)
      setPlaybookForm({
        name: playbook.name,
        description: playbook.description || '',
        trigger_mode: playbook.trigger_mode,
        trigger_severity: playbook.trigger_severity || 'HIGH',
        commands: Array.isArray(playbook.commands) ? playbook.commands : [''],
        is_active: playbook.is_active
      })
    } else {
      setEditingPlaybook(null)
      setPlaybookForm({
        name: '',
        description: '',
        trigger_mode: 'MANUAL',
        trigger_severity: 'HIGH',
        commands: [''],
        is_active: true
      })
    }
    setShowPlaybookModal(true)
  }

  const handleSavePlaybook = async (e) => {
    e.preventDefault()
    setSavingPlaybook(true)
    const cleanedCommands = playbookForm.commands.filter(c => c.trim() !== '')
    const payload = { ...playbookForm, commands: cleanedCommands }
    try {
      if (editingPlaybook) {
        await playbooksAPI.update(editingPlaybook.id, payload)
        toast.success('Playbook updated')
      } else {
        await playbooksAPI.create(payload)
        toast.success('Playbook created')
      }
      setShowPlaybookModal(false)
      refetchPlaybooks()
    } catch {
      toast.error('Failed to save playbook')
    } finally {
      setSavingPlaybook(false)
    }
  }

  const handleDeletePlaybook = async (id) => {
    if (!confirm('Are you sure you want to delete this playbook?')) return
    try {
      await playbooksAPI.delete(id)
      toast.success('Playbook deleted')
      refetchPlaybooks()
    } catch {
      toast.error('Failed to delete playbook')
    }
  }

  const handleTogglePlaybook = async (playbook) => {
    try {
      await playbooksAPI.update(playbook.id, { is_active: !playbook.is_active })
      toast.success(playbook.is_active ? 'Playbook deactivated' : 'Playbook activated')
      refetchPlaybooks()
    } catch {
      toast.error('Status change failed')
    }
  }

  // Blocklist Handlers
  const handleBlockManual = async (e) => {
    e.preventDefault()
    if (!blockIp) return
    setBlocking(true)
    try {
      await blocklistAPI.add({ ip_address: blockIp, reason: blockReason || 'Manually blocked by admin' })
      toast.success(`IP ${blockIp} added to Blocklist`)
      setBlockIp('')
      setBlockReason('')
      setShowBlockModal(false)
      refetchBlocklist()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to block IP')
    } finally {
      setBlocking(false)
    }
  }

  const handleUnblock = async (id) => {
    if (!confirm('Unblock this IP? This will delete the firewall rule.')) return
    try {
      await blocklistAPI.remove(id)
      toast.success('IP unblocked and rules cleared')
      refetchBlocklist()
    } catch {
      toast.error('Unblock failed')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Active Response Playbooks</h1>
          <p className="text-sm text-gray-500 mt-0.5">Define automated threat containment, manage IP blocks, and review execution logs</p>
        </div>
        <div className="flex items-center gap-2">
          {activeTab === 'playbooks' && (
            <button onClick={() => handleOpenPlaybookModal()} className="btn-primary flex items-center gap-2">
              <Plus className="w-4 h-4" /> Add Playbook
            </button>
          )}
          {activeTab === 'blocklist' && (
            <button onClick={() => setShowBlockModal(true)} className="btn-ghost flex items-center gap-2 bg-red-500/10 text-cyber-red border border-red-500/20 hover:bg-red-500/20">
              <ShieldAlert className="w-4 h-4" /> Block IP Address
            </button>
          )}
          {activeTab === 'users' && (
            <button onClick={() => setShowUserModal(true)} className="btn-primary flex items-center gap-2">
              <Plus className="w-4 h-4" /> Add User Credentials
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-navy-700/50 flex gap-4">
        {[
          { id: 'playbooks', label: 'Response Playbooks', icon: Shield },
          { id: 'blocklist', label: 'IP Blocklist', icon: ShieldAlert },
          { id: 'executions', label: 'Audit Trail / Logs', icon: Terminal },
          { id: 'users', label: 'User Management', icon: User },
          { id: 'rules', label: 'Detection Rules', icon: ShieldCheck },
        ].map(tab => {
          const Icon = tab.icon || Shield
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={clsx(
                'flex items-center gap-2 px-4 py-3 text-xs font-semibold border-b-2 -mb-[2px] transition-all',
                activeTab === tab.id
                  ? 'border-cyber-cyan text-cyber-cyan font-bold'
                  : 'border-transparent text-gray-500 hover:text-gray-300'
              )}
            >
              <Icon className="w-3.5 h-3.5" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Main Content Areas */}
      <div className="space-y-4">
        {/* 1. PLAYBOOKS TAB */}
        {activeTab === 'playbooks' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {playbooksLoading ? (
              Array.from({ length: 2 }).map((_, i) => (
                <div key={i} className="glass-card p-5 space-y-3 animate-pulse">
                  <div className="h-4 bg-navy-700 rounded w-2/3" />
                  <div className="h-12 bg-navy-700 rounded w-full" />
                </div>
              ))
            ) : playbooks?.length === 0 ? (
              <div className="col-span-full glass-card p-12 text-center text-gray-600">
                <Shield className="w-10 h-10 mx-auto mb-3 opacity-20" />
                <p className="text-sm">No response playbooks configured. Create one to begin automated protection.</p>
              </div>
            ) : (
              playbooks?.map(pb => (
                <motion.div
                  key={pb.id}
                  layout
                  className="glass-card p-5 hover:border-navy-600 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h3 className="font-semibold text-gray-100 text-sm leading-snug">{pb.name}</h3>
                        <p className="text-xs text-gray-500 mt-0.5">{pb.description || 'No description provided'}</p>
                      </div>
                      <button
                        onClick={() => handleTogglePlaybook(pb)}
                        className={clsx(
                          'p-1.5 rounded border transition-colors',
                          pb.is_active
                            ? 'text-green-400 bg-green-500/10 border-green-500/20 hover:bg-green-500/20'
                            : 'text-gray-500 bg-gray-500/10 border-gray-500/20 hover:bg-gray-500/20'
                        )}
                        title={pb.is_active ? 'Deactivate' : 'Activate'}
                      >
                        <Power className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    <div className="flex flex-wrap gap-2 mb-4 text-[10px] font-mono">
                      <span className="inline-flex px-2 py-0.5 rounded border bg-navy-800 text-gray-400 border-navy-700">
                        Trigger: {pb.trigger_mode === 'AUTO' ? 'Auto (ML Prediction)' : 'Manual Execution'}
                      </span>
                      {pb.trigger_mode === 'AUTO' && pb.trigger_severity && (
                        <span className={clsx('inline-flex px-2 py-0.5 rounded border', SEVERITY_COLORS[pb.trigger_severity])}>
                          Severity: {pb.trigger_severity}
                        </span>
                      )}
                    </div>

                    {/* Commands Terminal View */}
                    <div className="bg-navy-950 rounded-lg p-3 font-mono text-[10px] text-cyber-cyan border border-navy-800 mb-4 overflow-x-auto max-h-24">
                      {pb.commands?.map((cmd, i) => (
                        <div key={i} className="flex gap-1.5">
                          <span className="text-gray-600">$</span>
                          <span className="text-gray-300 break-all">{cmd}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="pt-3 border-t border-navy-800 flex items-center justify-between text-xs text-gray-500">
                    <span className="text-[10px] font-mono">Created {format(new Date(pb.created_at), 'dd MMM yyyy')}</span>
                    <div className="flex items-center gap-2">
                      <button onClick={() => handleOpenPlaybookModal(pb)} className="p-1 rounded hover:bg-navy-700 text-gray-400 hover:text-white transition-colors">
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button onClick={() => handleDeletePlaybook(pb.id)} className="p-1 rounded hover:bg-red-500/10 text-gray-400 hover:text-cyber-red transition-colors">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </motion.div>
              ))
            )}
          </div>
        )}

        {/* 2. BLOCKLIST TAB */}
        {activeTab === 'blocklist' && (
          <div className="glass-card p-0 overflow-hidden">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-navy-700 bg-navy-800/30 text-gray-500 font-medium">
                  <th className="p-4">IP Address</th>
                  <th className="p-4">Reason</th>
                  <th className="p-4">Blocked At</th>
                  <th className="p-4">Expires</th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-800/50">
                {blocklistLoading ? (
                  Array.from({ length: 3 }).map((_, i) => (
                    <tr key={i} className="animate-pulse">
                      <td colSpan="5" className="p-4 h-12 bg-navy-800/10" />
                    </tr>
                  ))
                ) : blocklist?.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="p-8 text-center text-gray-600">
                      No blocked IP addresses. System is clear.
                    </td>
                  </tr>
                ) : (
                  blocklist?.map(item => (
                    <tr key={item.id} className="hover:bg-navy-800/30">
                      <td className="p-4 font-mono font-bold text-cyber-red">{item.ip_address}</td>
                      <td className="p-4 text-gray-400">{item.reason}</td>
                      <td className="p-4 font-mono text-gray-500">{format(new Date(item.blocked_at), 'yyyy-MM-dd HH:mm')}</td>
                      <td className="p-4 font-mono text-gray-500">
                        {item.expires_at ? format(new Date(item.expires_at), 'yyyy-MM-dd HH:mm') : 'Permanent'}
                      </td>
                      <td className="p-4 text-right">
                        <button
                          onClick={() => handleUnblock(item.id)}
                          className="px-2.5 py-1 text-[10px] font-bold text-green-400 bg-green-500/10 border border-green-500/20 rounded hover:bg-green-500/20 transition-colors"
                        >
                          Unblock
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* 3. EXECUTIONS TAB */}
        {activeTab === 'executions' && (
          <div className="glass-card p-0 overflow-hidden">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-navy-700 bg-navy-800/30 text-gray-500 font-medium">
                  <th className="p-4">Playbook</th>
                  <th className="p-4">Target IP</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Triggered At</th>
                  <th className="p-4 text-right">Audits</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-800/50">
                {executionsLoading ? (
                  Array.from({ length: 3 }).map((_, i) => (
                    <tr key={i} className="animate-pulse">
                      <td colSpan="5" className="p-4 h-12 bg-navy-800/10" />
                    </tr>
                  ))
                ) : executions?.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="p-8 text-center text-gray-600">
                      No playbook executions logged.
                    </td>
                  </tr>
                ) : (
                  executions?.map(exec => {
                    const isSuccess = exec.status === 'SUCCESS'
                    const isDry = exec.status === 'DRY_RUN'
                    return (
                      <tr key={exec.id} className="hover:bg-navy-800/30">
                        <td className="p-4 font-semibold text-gray-200">{exec.playbook_name}</td>
                        <td className="p-4 font-mono text-cyber-cyan">{exec.target_ip || '—'}</td>
                        <td className="p-4">
                          <span className={clsx(
                            'inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] border font-bold',
                            isSuccess
                              ? 'bg-green-500/10 text-green-400 border-green-500/20'
                              : isDry
                                ? 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                                : 'bg-red-500/10 text-cyber-red border-red-500/20'
                          )}>
                            {isSuccess ? <CheckCircle className="w-2.5 h-2.5" /> : <XCircle className="w-2.5 h-2.5" />}
                            {exec.status}
                          </span>
                        </td>
                        <td className="p-4 font-mono text-gray-500">{format(new Date(exec.executed_at), 'dd MMM HH:mm:ss')}</td>
                        <td className="p-4 text-right">
                          <button
                            onClick={() => setSelectedExecution(exec)}
                            className="px-2.5 py-1 text-[10px] font-bold text-cyber-cyan bg-cyber-cyan/10 border border-cyber-cyan/20 rounded hover:bg-cyber-cyan/20 transition-colors"
                          >
                            View Logs
                          </button>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* 4. USER MANAGEMENT TAB */}
        {activeTab === 'users' && (
          <div className="glass-card p-0 overflow-hidden">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-navy-700 bg-navy-800/30 text-gray-500 font-medium">
                  <th className="p-4">Full Name</th>
                  <th className="p-4">Email</th>
                  <th className="p-4">Role</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Organization</th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-800/50">
                {usersLoading ? (
                  Array.from({ length: 3 }).map((_, i) => (
                    <tr key={i} className="animate-pulse">
                      <td colSpan="6" className="p-4 h-12 bg-navy-800/10" />
                    </tr>
                  ))
                ) : users?.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="p-8 text-center text-gray-600">
                      No user accounts registered.
                    </td>
                  </tr>
                ) : (
                  users?.map(u => (
                    <tr key={u.login_id} className="hover:bg-navy-800/30">
                      <td className="p-4 font-semibold text-gray-200">{u.user_name}</td>
                      <td className="p-4 font-mono text-gray-400">{u.email}</td>
                      <td className="p-4">
                        <span className="inline-flex px-2 py-0.5 rounded text-[10px] font-bold border border-navy-750 bg-navy-800 text-cyber-cyan">
                          {u.role}
                        </span>
                      </td>
                      <td className="p-4">
                        <span className={clsx(
                          'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-bold border',
                          u.status === 'ACTIVE'
                            ? 'bg-green-500/10 text-green-400 border-green-500/20'
                            : 'bg-red-500/10 text-cyber-red border-red-500/20'
                        )}>
                          {u.status}
                        </span>
                      </td>
                      <td className="p-4 text-gray-500">{u.org_name}</td>
                      <td className="p-4 flex items-center justify-end gap-2">
                        {u.email !== currentUser?.email ? (
                          <>
                            <button onClick={() => handleEditUser(u)} className="p-1.5 hover:bg-navy-700 rounded text-gray-400 hover:text-cyber-cyan transition-colors" title="Edit User">
                              <Edit2 className="w-4 h-4" />
                            </button>
                            <button onClick={() => handleDeleteUser(u.login_id)} className="p-1.5 hover:bg-navy-700 rounded text-gray-400 hover:text-cyber-red transition-colors" title="Delete User">
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </>
                        ) : (
                          <span className="text-gray-600 text-[10px] uppercase font-bold tracking-widest mr-2">You</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* 5. DETECTION RULES TAB */}
        {activeTab === 'rules' && (
          <div className="glass-card p-0 overflow-hidden">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-navy-700 bg-navy-800/30 text-gray-500 font-medium">
                  <th className="p-4">Rule Code</th>
                  <th className="p-4">Rule Name</th>
                  <th className="p-4">Threshold Condition</th>
                  <th className="p-4">Severity</th>
                  <th className="p-4">Mitigation Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-800/50">
                {[
                  { code: 'RULE-10001', name: 'Excessive SSH Authentication Failures', threshold: '5 failed logins in 60 seconds', severity: 'HIGH', action: 'Trigger Playbook (Block IP)' },
                  { code: 'RULE-10002', name: 'TCP SYN Flooding Detection', threshold: '100 connections in 1 second', severity: 'CRITICAL', action: 'Trigger Playbook (Throttle Segment)' },
                  { code: 'RULE-10003', name: 'Port Scan Reconnaissance Activity', threshold: '20 ports scanned in 10 seconds', severity: 'MEDIUM', action: 'Notify Security Analyst Group' },
                  { code: 'RULE-10004', name: 'Unauthorized HTTP Admin Directory Scan', threshold: '3 target folder accesses in 5 seconds', severity: 'HIGH', action: 'Trigger Playbook (Quarantine Node)' },
                ].map(rule => (
                  <tr key={rule.code} className="hover:bg-navy-800/30">
                    <td className="p-4 font-mono font-bold text-cyber-cyan">{rule.code}</td>
                    <td className="p-4 font-semibold text-gray-200">{rule.name}</td>
                    <td className="p-4 text-gray-400 font-mono">{rule.threshold}</td>
                    <td className="p-4">
                      <span className={clsx(
                        'inline-flex px-2 py-0.5 rounded text-[10px] font-bold border uppercase',
                        rule.severity === 'CRITICAL' ? 'bg-red-500/10 text-cyber-red border-red-500/20' :
                        rule.severity === 'HIGH' ? 'bg-orange-500/10 text-orange-400 border-orange-500/20' :
                        'bg-amber-500/10 text-amber-400 border-amber-500/20'
                      )}>
                        {rule.severity}
                      </span>
                    </td>
                    <td className="p-4 text-gray-500">{rule.action}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Manual User Modal */}
      <AnimatePresence>
        {showUserModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="glass-card w-full max-w-sm p-6 border-cyber-cyan/20"
            >
              <h2 className="text-base font-bold text-white mb-4">Add User Credentials</h2>
              <form onSubmit={handleCreateUser} className="space-y-4">
                <div>
                  <label className="block text-[10px] uppercase text-gray-500 mb-1 font-semibold">Select Monitored User Profile</label>
                  <select
                    value={userForm.user}
                    onChange={e => setUserForm(p => ({ ...p, user: e.target.value }))}
                    className="cyber-input w-full bg-navy-800 text-xs"
                    required
                  >
                    <option value="">Choose User Profile...</option>
                    {coreUsers?.map(cu => (
                      <option key={cu.user_id} value={cu.user_id}>{cu.full_name} ({cu.org_name})</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] uppercase text-gray-500 mb-1 font-semibold">Login Email</label>
                  <input
                    type="email"
                    value={userForm.email}
                    onChange={e => setUserForm(p => ({ ...p, email: e.target.value }))}
                    placeholder="user@organization.local"
                    className="cyber-input w-full text-xs"
                    required
                  />
                </div>

                <div>
                  <label className="block text-[10px] uppercase text-gray-500 mb-1 font-semibold">Password</label>
                  <input
                    type="text"
                    value={userForm.password}
                    onChange={e => setUserForm(p => ({ ...p, password: e.target.value }))}
                    placeholder="Enter password (default: TemporaryPassword@2024)"
                    className="cyber-input w-full text-xs"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[10px] uppercase text-gray-500 mb-1 font-semibold">Assign Role</label>
                    <select
                      value={userForm.role}
                      onChange={e => setUserForm(p => ({ ...p, role: e.target.value }))}
                      className="cyber-input w-full bg-navy-800 text-xs"
                    >
                      <option value="Analyst">Security Analyst</option>
                      <option value="Investigator">Digital Forensic Investigator</option>
                      <option value="Admin">System Administrator</option>
                      <option value="Management">Organization Manager</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] uppercase text-gray-500 mb-1 font-semibold">Initial Status</label>
                    <select
                      value={userForm.status}
                      onChange={e => setUserForm(p => ({ ...p, status: e.target.value }))}
                      className="cyber-input w-full bg-navy-800 text-xs"
                    >
                      <option value="ACTIVE">Active</option>
                      <option value="INACTIVE">Inactive</option>
                    </select>
                  </div>
                </div>

                <div className="flex items-center justify-end gap-3 pt-2">
                  <button type="button" onClick={() => setShowUserModal(false)} className="btn-ghost text-xs">
                    Cancel
                  </button>
                  <button type="submit" disabled={savingUser} className="btn-primary text-xs">
                    {savingUser ? 'Creating...' : 'Register User'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Playbook Edit/Create Modal */}
      <AnimatePresence>
        {showPlaybookModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="glass-card w-full max-w-lg p-6 border-cyber-cyan/30"
            >
              <h2 className="text-base font-bold text-white mb-4">
                {editingPlaybook ? 'Update Response Playbook' : 'Add Response Playbook'}
              </h2>
              <form onSubmit={handleSavePlaybook} className="space-y-4">
                <div>
                  <label className="block text-[10px] uppercase text-gray-500 mb-1 font-semibold">Playbook Name</label>
                  <input
                    type="text"
                    value={playbookForm.name}
                    onChange={e => setPlaybookForm(p => ({ ...p, name: e.target.value }))}
                    placeholder="e.g. Block Brute-Forcer Firewall Rule"
                    className="cyber-input w-full"
                    required
                  />
                </div>

                <div>
                  <label className="block text-[10px] uppercase text-gray-500 mb-1 font-semibold">Description</label>
                  <textarea
                    value={playbookForm.description}
                    onChange={e => setPlaybookForm(p => ({ ...p, description: e.target.value }))}
                    placeholder="Describe threat scenarios and response mitigations..."
                    className="cyber-input w-full h-16 resize-none text-xs"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[10px] uppercase text-gray-500 mb-1 font-semibold">Trigger Mode</label>
                    <select
                      value={playbookForm.trigger_mode}
                      onChange={e => setPlaybookForm(p => ({ ...p, trigger_mode: e.target.value }))}
                      className="cyber-input w-full bg-navy-800"
                    >
                      <option value="MANUAL">Manual Trigger</option>
                      <option value="AUTO">Automatic (Confidence Gate)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] uppercase text-gray-500 mb-1 font-semibold">Minimum Severity</label>
                    <select
                      value={playbookForm.trigger_severity}
                      onChange={e => setPlaybookForm(p => ({ ...p, trigger_severity: e.target.value }))}
                      className="cyber-input w-full bg-navy-800"
                      disabled={playbookForm.trigger_mode !== 'AUTO'}
                    >
                      <option value="LOW">Low</option>
                      <option value="MEDIUM">Medium</option>
                      <option value="HIGH">High</option>
                      <option value="CRITICAL">Critical</option>
                    </select>
                  </div>
                </div>

                {/* Commands Array Field */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-[10px] uppercase text-gray-500 font-semibold">Playbook Command Steps</label>
                    <button
                      type="button"
                      onClick={() => setPlaybookForm(p => ({ ...p, commands: [...p.commands, ''] }))}
                      className="text-[10px] text-cyber-cyan hover:underline"
                    >
                      + Add Command
                    </button>
                  </div>
                  <div className="space-y-2 max-h-36 overflow-y-auto pr-1">
                    {playbookForm.commands.map((cmd, index) => (
                      <div key={index} className="flex gap-2 items-center">
                        <Terminal className="w-3.5 h-3.5 text-gray-600 shrink-0" />
                        <input
                          type="text"
                          value={cmd}
                          onChange={e => {
                            const copy = [...playbookForm.commands]
                            copy[index] = e.target.value
                            setPlaybookForm(p => ({ ...p, commands: copy }))
                          }}
                          placeholder="e.g. iptables -A INPUT -s {ip} -j DROP"
                          className="cyber-input flex-1 font-mono text-[10px] py-1.5"
                          required
                        />
                        {playbookForm.commands.length > 1 && (
                          <button
                            type="button"
                            onClick={() => {
                              const copy = playbookForm.commands.filter((_, i) => i !== index)
                              setPlaybookForm(p => ({ ...p, commands: copy }))
                            }}
                            className="text-gray-500 hover:text-cyber-red shrink-0"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                  <p className="text-[9px] text-gray-600 mt-1 font-mono">Use {"{ip}"} as a wildcard token for target IP address replacement.</p>
                </div>

                <div className="flex items-center justify-end gap-3 pt-2">
                  <button type="button" onClick={() => setShowPlaybookModal(false)} className="btn-ghost text-xs">
                    Cancel
                  </button>
                  <button type="submit" disabled={savingPlaybook} className="btn-primary text-xs">
                    {savingPlaybook ? 'Saving...' : 'Save Playbook'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Add Manual Block IP Modal */}
      <AnimatePresence>
        {showBlockModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="glass-card w-full max-w-sm p-6 border-red-500/20"
            >
              <h2 className="text-base font-bold text-cyber-red mb-4 flex items-center gap-2">
                <ShieldAlert className="w-5 h-5" /> Block Remote IP
              </h2>
              <form onSubmit={handleBlockManual} className="space-y-4">
                <div>
                  <label className="block text-[10px] uppercase text-gray-500 mb-1 font-semibold">IP Address</label>
                  <input
                    type="text"
                    value={blockIp}
                    onChange={e => setBlockIp(e.target.value)}
                    placeholder="e.g. 185.220.101.5"
                    className="cyber-input w-full font-mono text-xs"
                    required
                  />
                </div>

                <div>
                  <label className="block text-[10px] uppercase text-gray-500 mb-1 font-semibold">Reason</label>
                  <input
                    type="text"
                    value={blockReason}
                    onChange={e => setBlockReason(e.target.value)}
                    placeholder="Brute forcing, SSH scan, etc."
                    className="cyber-input w-full text-xs"
                    required
                  />
                </div>

                <div className="flex items-center justify-end gap-3 pt-2">
                  <button type="button" onClick={() => setShowBlockModal(false)} className="btn-ghost text-xs">
                    Cancel
                  </button>
                  <button type="submit" disabled={blocking} className="btn-primary bg-cyber-red border-red-500 hover:bg-red-600/80 text-xs">
                    {blocking ? 'Blocking...' : 'Deploy Block Rule'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Execution Detailed Log View Modal */}
      <AnimatePresence>
        {selectedExecution && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="glass-card w-full max-w-2xl p-6 border-navy-700/80"
            >
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-base font-bold text-white">Playbook Execution Audit Log</h2>
                  <p className="text-[10px] text-gray-500 font-mono mt-0.5">Execution ID: {selectedExecution.id}</p>
                </div>
                <button
                  onClick={() => setSelectedExecution(null)}
                  className="btn-ghost text-xs"
                >
                  Close
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4 text-xs">
                <div className="space-y-1 bg-navy-800/40 p-2.5 rounded border border-navy-850">
                  <div className="text-gray-600 text-[10px] uppercase">Playbook</div>
                  <div className="text-gray-200 font-medium">{selectedExecution.playbook_name}</div>
                </div>
                <div className="space-y-1 bg-navy-800/40 p-2.5 rounded border border-navy-850">
                  <div className="text-gray-600 text-[10px] uppercase">Target IP Address</div>
                  <div className="text-cyber-cyan font-mono font-bold">{selectedExecution.target_ip || 'Internal System'}</div>
                </div>
              </div>

              <div className="space-y-2">
                <div className="text-xs font-semibold text-gray-400">Terminal Log Outputs</div>
                <div className="bg-navy-950 rounded-lg border border-navy-800 p-4 font-mono text-[10px] max-h-60 overflow-y-auto leading-relaxed">
                  {selectedExecution.stdout ? (
                    <pre className="text-green-400 whitespace-pre-wrap">{selectedExecution.stdout}</pre>
                  ) : (
                    <div className="text-gray-600 italic">No output logged to stdout.</div>
                  )}
                  {selectedExecution.stderr && (
                    <pre className="text-cyber-red mt-3 whitespace-pre-wrap">{selectedExecution.stderr}</pre>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-between mt-4 pt-3 border-t border-navy-800 text-[10px] text-gray-500 font-mono">
                <span>Exit Code: {selectedExecution.exit_code ?? '0'}</span>
                <span>Completed: {format(new Date(selectedExecution.completed_at || selectedExecution.executed_at), 'yyyy-MM-dd HH:mm:ss')}</span>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
