import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import {
  AlertTriangle, Activity, Search, FileText,
  Server, BookOpen, BarChart3, ClipboardList, LogOut,
  Zap, Lock, Database, Shield
} from 'lucide-react'
import { clsx } from 'clsx'
import CyberShieldLogo from '../brand/CyberShieldLogo'

const NAV_CONFIG = {
  ANALYST: [
    { to: '/analyst',                icon: Activity,      label: 'Live Dashboard' },
    { to: '/analyst/alerts',         icon: AlertTriangle, label: 'Alert Feed' },
    { to: '/analyst/network-events', icon: Database,      label: 'Network Events' },
    { to: '/analyst/incidents',      icon: Shield,        label: 'Incidents' },
  ],
  INVESTIGATOR: [
    { to: '/forensics',            icon: FileText,     label: 'Case Vault' },
    { to: '/forensics/evidence',   icon: Lock,         label: 'Evidence' },
  ],
  SYS_ADMIN: [
    { to: '/admin',                icon: Server,       label: 'Asset Registry' },
    { to: '/admin/playbooks',      icon: BookOpen,     label: 'Playbooks' },
    { to: '/admin/health',         icon: Activity,     label: 'System Health' },
  ],
  ORG_MANAGER: [
    { to: '/org',                  icon: BarChart3,    label: 'Security Metrics' },
    { to: '/org/audit',            icon: ClipboardList, label: 'Audit Trail' },
    { to: '/org/reports',          icon: FileText,     label: 'Compliance Reports' },
  ],
  SUPER_ADMIN: [
    { to: '/analyst',              icon: Activity,     label: 'Live Dashboard' },
    { to: '/analyst/network-events', icon: Search,     label: 'Network Events' },
    { to: '/forensics',            icon: FileText,     label: 'Case Vault' },
    { to: '/admin',                icon: Server,       label: 'Asset Registry' },
    { to: '/org',                  icon: BarChart3,    label: 'Security Metrics' },
  ],
}

const ROLE_LABELS = {
  ANALYST:      'Security Analyst',
  INVESTIGATOR: 'Forensic Investigator',
  SYS_ADMIN:    'System Administrator',
  ORG_MANAGER:  'Org Manager',
  SUPER_ADMIN:  'Super Admin',
}

export default function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const navItems = NAV_CONFIG[user?.role] || []

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <aside className="w-60 shrink-0 flex flex-col bg-navy-950 border-r border-cyber-cyan/10">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-cyber-cyan/10">
        <CyberShieldLogo size="sm" />
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        <div className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest px-3 mb-2">
          {ROLE_LABELS[user?.role] || 'Dashboard'}
        </div>
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end
            className={({ isActive }) =>
              clsx('nav-item', isActive && 'nav-item-active')
            }
          >
            <Icon className="w-4 h-4 shrink-0" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* User Footer */}
      <div className="px-3 py-4 border-t border-cyber-cyan/10">
        <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-navy-800/60 mb-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyber-cyan/20 to-blue-500/20 border border-cyber-cyan/20 flex items-center justify-center text-xs font-bold text-cyber-cyan">
            {user?.fullName?.[0] || user?.first_name?.[0] || '?'}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs font-medium text-gray-200 truncate">{user?.fullName || user?.email}</div>
            <div className="text-[10px] text-gray-500 truncate">{user?.tenantName}</div>
          </div>
        </div>
        <button onClick={handleLogout} className="nav-item w-full text-red-400 hover:text-red-300 hover:bg-red-500/10">
          <LogOut className="w-4 h-4" />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  )
}
