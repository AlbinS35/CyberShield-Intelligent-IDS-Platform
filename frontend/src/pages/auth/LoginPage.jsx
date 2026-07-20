import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { useQuery } from '@tanstack/react-query'
import { authAPI } from '../../api'
import { Shield, Eye, EyeOff, AlertTriangle } from 'lucide-react'
import { getRoleDefaultPath } from '../../components/layout/ProtectedRoute'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate  = useNavigate()

  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState('')

  const { data: tenantsData } = useQuery({
    queryKey: ['tenants'],
    queryFn: () => authAPI.tenants().then(r => r.data),
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const user = await login(email, password)
      toast.success(`Welcome back, ${user.fullName || user.first_name}!`)
      navigate(getRoleDefaultPath(user.role))
    } catch (err) {
      const msg = err.response?.data?.detail || 'Invalid credentials. Please try again.'
      setError(msg)
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-navy-900 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background Cyber Grid */}
      <div className="absolute inset-0 bg-cyber-grid bg-grid opacity-30" />
      {/* Glow accents */}
      <div className="absolute top-1/4 left-1/3 w-96 h-96 bg-cyber-cyan/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/3 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="relative w-full max-w-sm animate-fade-in">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 rounded-2xl bg-cyber-cyan/10 border border-cyber-cyan/30 flex items-center justify-center shadow-cyber">
              <Shield className="w-9 h-9 text-cyber-cyan" />
            </div>
          </div>
          <h1 className="text-2xl font-bold text-white mb-1">CyberShield</h1>
          <p className="text-sm text-gray-400">Intelligent IDS Platform</p>
          <div className="mt-2 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-cyber-green/10 border border-cyber-green/20">
            <span className="status-dot-online" />
            <span className="text-[10px] text-cyber-green font-mono font-semibold">SYSTEM OPERATIONAL</span>
          </div>
        </div>

        {/* Login Form */}
        <div className="glass-card p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-1.5 uppercase tracking-wider">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="cyber-input"
                placeholder="analyst@cybershield.io"
                required
                autoComplete="email"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-1.5 uppercase tracking-wider">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPass ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="cyber-input pr-10"
                  placeholder="••••••••"
                  required
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPass(v => !v)}
                  className="absolute inset-y-0 right-0 flex items-center px-3 text-gray-500 hover:text-gray-300"
                >
                  {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
                <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg font-semibold text-sm transition-all duration-200
                         bg-cyber-cyan/15 text-cyber-cyan border border-cyber-cyan/30
                         hover:bg-cyber-cyan/25 hover:border-cyber-cyan/60 hover:shadow-cyber
                         disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-cyber-cyan/30 border-t-cyber-cyan rounded-full animate-spin" />
                  Authenticating...
                </span>
              ) : 'Secure Sign In'}
            </button>
          </form>
        </div>

        {/* Available tenants hint */}
        {tenantsData?.length > 0 && (
          <div className="mt-4 text-center">
            <p className="text-[11px] text-gray-600">
              {tenantsData.length} organization{tenantsData.length !== 1 ? 's' : ''} registered
            </p>
          </div>
        )}

        <p className="text-center text-[11px] text-gray-600 mt-4">
          Amal Jyothi College of Engineering · MCA Research Project
        </p>
      </div>
    </div>
  )
}
