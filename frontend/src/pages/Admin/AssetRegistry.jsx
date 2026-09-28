import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Server, Plus, Search, Trash2, Edit2, ShieldAlert,
  Activity, CheckCircle, AlertTriangle, Monitor, Cpu
} from 'lucide-react'
import { assetsAPI } from '../../api'
import axios from '../../api/axios' // fallback or helper for direct fetches if needed
import toast from 'react-hot-toast'
import { clsx } from 'clsx'

const OS_CONFIG = {
  Linux:     { icon: Cpu,        color: 'text-amber-400 bg-amber-500/10 border-amber-500/20' },
  Windows:   { icon: Monitor,    color: 'text-blue-400 bg-blue-500/10 border-blue-500/20' },
  macOS:     { icon: Monitor,    color: 'text-purple-400 bg-purple-500/10 border-purple-500/20' },
  CiscoIOS:  { icon: Server,     color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' },
}

const STATUS_CONFIG = {
  ONLINE:      { label: 'Online',      icon: CheckCircle,    cls: 'bg-green-500/10 text-green-400 border-green-500/20' },
  OFFLINE:     { label: 'Offline',     icon: AlertTriangle,  cls: 'bg-gray-500/10 text-gray-400 border-gray-500/20' },
  MAINTENANCE: { label: 'Maintenance', icon: Activity,       cls: 'bg-amber-500/10 text-amber-400 border-amber-500/20' },
  COMPROMISED: { label: 'Compromised', icon: ShieldAlert,    cls: 'bg-red-500/15 text-cyber-red border-red-500/30 font-bold animate-pulse' },
}

export default function AssetRegistry() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingAsset, setEditingAsset] = useState(null)
  const [saving, setSaving] = useState(false)

  // Form State
  const [formData, setFormData] = useState({
    asset_name: '',
    ip_address: '',
    os_type: 'Linux',
    wazuh_agent_id: '',
    status: 'ONLINE',
    org: ''
  })

  // Fetch Assets
  const { data: assets, isLoading, refetch } = useQuery({
    queryKey: ['assets', search, statusFilter],
    queryFn: () => assetsAPI.list({
      search: search || undefined,
      status: statusFilter || undefined
    }).then(r => r.data?.results || r.data || []),
  })

  // Fetch Organizations (for selector)
  const { data: organizations } = useQuery({
    queryKey: ['organizations'],
    queryFn: () => axios.get('/core/organizations/').then(r => r.data?.results || r.data || []),
  })

  const openAddModal = () => {
    setEditingAsset(null)
    setFormData({
      asset_name: '',
      ip_address: '',
      os_type: 'Linux',
      wazuh_agent_id: '',
      status: 'ONLINE',
      org: organizations?.[0]?.org_id || ''
    })
    setShowModal(true)
  }

  const openEditModal = (asset) => {
    setEditingAsset(asset)
    setFormData({
      asset_name: asset.asset_name,
      ip_address: asset.ip_address,
      os_type: asset.os_type,
      wazuh_agent_id: asset.wazuh_agent_id || '',
      status: asset.status,
      org: asset.org
    })
    setShowModal(true)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      if (editingAsset) {
        await assetsAPI.update(editingAsset.asset_id, formData)
        toast.success('Asset updated successfully')
      } else {
        await assetsAPI.create(formData)
        toast.success('Asset registered successfully')
      }
      setShowModal(false)
      refetch()
    } catch (err) {
      const msg = err.response?.data ? JSON.stringify(err.response.data) : 'Operation failed'
      toast.error(msg)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to remove this asset? This cannot be undone.')) return
    try {
      await assetsAPI.delete(id)
      toast.success('Asset removed')
      refetch()
    } catch {
      toast.error('Failed to delete asset')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Infrastructure Asset Registry</h1>
          <p className="text-sm text-gray-500 mt-0.5">Register and manage servers, workstations, and network endpoints</p>
        </div>
        <button onClick={openAddModal} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Register Asset
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search assets by name, IP, or Agent ID..."
            className="cyber-input pl-9"
          />
        </div>
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className="cyber-input w-44 bg-navy-800"
        >
          <option value="">All Statuses</option>
          {Object.entries(STATUS_CONFIG).map(([v, { label }]) => (
            <option key={v} value={v}>{label}</option>
          ))}
        </select>
      </div>

      {/* Asset Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="glass-card p-5 space-y-3">
              <div className="h-4 bg-navy-700 rounded animate-pulse w-2/3" />
              <div className="h-3 bg-navy-700 rounded animate-pulse w-1/2" />
              <div className="h-6 bg-navy-700 rounded animate-pulse w-full" />
            </div>
          ))
        ) : assets?.length === 0 ? (
          <div className="col-span-full glass-card p-12 text-center text-gray-600">
            <Server className="w-10 h-10 mx-auto mb-3 opacity-20" />
            <p className="text-sm">No assets registered yet. Add one to begin monitoring.</p>
          </div>
        ) : (
          assets?.map((asset) => {
            const status = STATUS_CONFIG[asset.status] || STATUS_CONFIG.OFFLINE
            const StatusIcon = status.icon
            const os = OS_CONFIG[asset.os_type] || { icon: Cpu, color: 'text-gray-400 bg-gray-500/10 border-gray-500/20' }
            const OsIcon = os.icon

            return (
              <motion.div
                key={asset.asset_id}
                layout
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-card p-5 hover:border-cyber-cyan/20 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-gray-100 text-sm leading-snug">{asset.asset_name}</h3>
                      <span className="text-[10px] font-mono text-gray-500">{asset.ip_address}</span>
                    </div>
                    <span className={clsx('inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold border', status.cls)}>
                      <StatusIcon className="w-3 h-3" />
                      {status.label}
                    </span>
                  </div>

                  <div className="flex flex-wrap gap-2 mb-4">
                    <span className={clsx('inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] border', os.color)}>
                      <OsIcon className="w-3 h-3" />
                      {asset.os_type}
                    </span>
                    {asset.wazuh_agent_id && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] bg-navy-800 text-cyber-cyan border border-navy-700 font-mono">
                        Agent ID: {asset.wazuh_agent_id}
                      </span>
                    )}
                  </div>
                </div>

                <div className="pt-3 border-t border-navy-700/50 flex items-center justify-between text-xs text-gray-500">
                  <span>{asset.org_name || 'Organization Tenant'}</span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => openEditModal(asset)}
                      className="p-1 rounded hover:bg-navy-700 text-gray-400 hover:text-white transition-colors"
                      title="Edit Asset"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleDelete(asset.asset_id)}
                      className="p-1 rounded hover:bg-red-500/10 text-gray-400 hover:text-cyber-red transition-colors"
                      title="Delete Asset"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </motion.div>
            )
          })
        )}
      </div>

      {/* Register/Edit Modal */}
      <AnimatePresence>
        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="glass-card w-full max-w-md p-6 border-cyber-cyan/30"
            >
              <h2 className="text-base font-bold text-white mb-4">
                {editingAsset ? 'Edit Infrastructure Asset' : 'Register New Asset'}
              </h2>
              <form onSubmit={handleSave} className="space-y-4">
                <div>
                  <label className="block text-[10px] uppercase text-gray-500 mb-1 font-semibold">Asset Name</label>
                  <input
                    type="text"
                    value={formData.asset_name}
                    onChange={e => setFormData(p => ({ ...p, asset_name: e.target.value }))}
                    placeholder="e.g. core-router-east"
                    className="cyber-input w-full"
                    required
                  />
                </div>

                <div>
                  <label className="block text-[10px] uppercase text-gray-500 mb-1 font-semibold">IP Address</label>
                  <input
                    type="text"
                    value={formData.ip_address}
                    onChange={e => setFormData(p => ({ ...p, ip_address: e.target.value }))}
                    placeholder="e.g. 10.0.0.1"
                    className="cyber-input w-full"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[10px] uppercase text-gray-500 mb-1 font-semibold">OS Type</label>
                    <select
                      value={formData.os_type}
                      onChange={e => setFormData(p => ({ ...p, os_type: e.target.value }))}
                      className="cyber-input w-full bg-navy-800"
                    >
                      <option value="Linux">Linux</option>
                      <option value="Windows">Windows</option>
                      <option value="macOS">macOS</option>
                      <option value="CiscoIOS">Cisco IOS</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] uppercase text-gray-500 mb-1 font-semibold">Status</label>
                    <select
                      value={formData.status}
                      onChange={e => setFormData(p => ({ ...p, status: e.target.value }))}
                      className="cyber-input w-full bg-navy-800"
                    >
                      <option value="ONLINE">Online</option>
                      <option value="OFFLINE">Offline</option>
                      <option value="MAINTENANCE">Maintenance</option>
                      <option value="COMPROMISED">Compromised</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-[10px] uppercase text-gray-500 mb-1 font-semibold">Wazuh Agent ID (Optional)</label>
                  <input
                    type="text"
                    value={formData.wazuh_agent_id}
                    onChange={e => setFormData(p => ({ ...p, wazuh_agent_id: e.target.value }))}
                    placeholder="e.g. 014"
                    className="cyber-input w-full font-mono"
                  />
                </div>

                <div>
                  <label className="block text-[10px] uppercase text-gray-500 mb-1 font-semibold">Tenant Organization</label>
                  <select
                    value={formData.org}
                    onChange={e => setFormData(p => ({ ...p, org: e.target.value }))}
                    className="cyber-input w-full bg-navy-800"
                    required
                  >
                    <option value="" disabled>Select Organization</option>
                    {organizations?.map(org => (
                      <option key={org.org_id} value={org.org_id}>{org.org_name}</option>
                    ))}
                  </select>
                </div>

                <div className="flex items-center justify-end gap-3 pt-2">
                  <button type="button" onClick={() => setShowModal(false)} className="btn-ghost text-xs">
                    Cancel
                  </button>
                  <button type="submit" disabled={saving} className="btn-primary text-xs">
                    {saving ? 'Saving...' : 'Save Asset'}
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
