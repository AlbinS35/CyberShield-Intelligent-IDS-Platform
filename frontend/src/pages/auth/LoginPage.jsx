import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { useQuery } from '@tanstack/react-query'
import { authAPI } from '../../api'
import {
  Shield, Fingerprint, SlidersHorizontal, BarChart3,
  Eye, EyeOff, Mail, Lock, ArrowRight, ChevronRight,
  AlertTriangle, Building2, KeyRound, Chrome
} from 'lucide-react'
import toast from 'react-hot-toast'

const styles = `
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');
  .auth-grid-bg {
    background-image:
      linear-gradient(to right, rgba(0,245,255,0.04) 1px, transparent 1px),
      linear-gradient(to bottom, rgba(0,245,255,0.04) 1px, transparent 1px);
    background-size: 40px 40px;
    position: fixed; inset: 0; z-index: -2; pointer-events: none;
  }
  .auth-glass {
    background: rgba(255,255,255,0.03);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.08);
  }
  .auth-input {
    width: 100%; padding: 11px 14px 11px 42px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    color: #dce4e4; font-size: 14px;
    outline: none; transition: all 0.25s ease;
    box-sizing: border-box;
    font-family: inherit;
  }
  .auth-input:focus {
    border-color: rgba(0,245,255,0.5);
    box-shadow: 0 0 0 3px rgba(0,245,255,0.08);
    background: rgba(0,245,255,0.03);
  }
  .auth-input::placeholder { color: rgba(220,228,228,0.3); }
  .auth-select {
    width: 100%; padding: 11px 14px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    color: #dce4e4; font-size: 14px;
    outline: none; transition: all 0.25s ease;
    box-sizing: border-box;
    font-family: inherit;
    cursor: pointer;
    appearance: none;
  }
  .auth-select:focus {
    border-color: rgba(0,245,255,0.5);
    box-shadow: 0 0 0 3px rgba(0,245,255,0.08);
  }
  .auth-select option { background: #0d1515; color: #dce4e4; }
  .auth-btn-primary {
    width: 100%; padding: 13px;
    background: #00F5FF; color: #001a1a;
    font-size: 15px; font-weight: 700;
    border: none; border-radius: 8px;
    cursor: pointer; transition: all 0.25s ease;
    display: flex; align-items: center; justify-content: center; gap: 8px;
    font-family: inherit;
  }
  .auth-btn-primary:hover {
    background: #63f7ff;
    box-shadow: 0 0 24px rgba(0,245,255,0.4);
    transform: translateY(-1px);
  }
  .auth-btn-primary:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
  .auth-btn-google {
    width: 100%; padding: 12px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 8px; color: rgba(220,228,228,0.85);
    font-size: 14px; font-weight: 500;
    cursor: pointer; transition: all 0.25s ease;
    font-family: inherit;
    display: flex; align-items: center; justify-content: center; gap: 10px;
  }
  .auth-btn-google:hover {
    border-color: rgba(66,133,244,0.5);
    background: rgba(66,133,244,0.08);
    color: #fff;
    box-shadow: 0 0 16px rgba(66,133,244,0.15);
  }
  .auth-btn-google:disabled { opacity: 0.6; cursor: not-allowed; }
  .auth-btn-secondary {
    transition: all 0.25s ease;
  }
  .auth-btn-secondary:hover {
    background: rgba(0,245,255,0.1) !important;
    border-color: rgba(0,245,255,0.4) !important;
    box-shadow: 0 0 16px rgba(0,245,255,0.1);
    transform: translateY(-1px);
  }
  .role-card {
    padding: 14px 16px;
    border-radius: 10px; cursor: pointer;
    transition: all 0.2s ease;
    display: flex; align-items: center; gap: 12px;
    border: 1px solid rgba(255,255,255,0.07);
    background: rgba(255,255,255,0.02);
  }
  .role-card:hover { background: rgba(255,255,255,0.05); }
  .auth-gradient-text {
    background: linear-gradient(135deg, #00F5FF 0%, #00E676 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .mono { font-family: 'JetBrains Mono', monospace; }
  .auth-left-bg {
    background: linear-gradient(160deg, rgba(0,245,255,0.06) 0%, rgba(0,230,118,0.03) 60%, transparent 100%);
  }
  @keyframes authGlow {
    0%,100% { opacity: 0.4; transform: scale(1); }
    50%      { opacity: 0.7; transform: scale(1.05); }
  }
  .auth-orb { animation: authGlow 6s ease-in-out infinite; }
`

const ROLES = [
  {
    key: 'ANALYST',
    label: 'Security Analyst',
    sub: 'SOC Tier-1 · Live Threat Triage',
    icon: Shield,
    color: '#00F5FF',
    bg: 'rgba(0,245,255,0.08)',
    border: 'rgba(0,245,255,0.35)',
    email: 'analyst@cybershield.demo',
  },
  {
    key: 'INVESTIGATOR',
    label: 'Forensic Investigator',
    sub: 'Evidence Vault · Chain of Custody',
    icon: Fingerprint,
    color: '#00E676',
    bg: 'rgba(0,230,118,0.08)',
    border: 'rgba(0,230,118,0.35)',
    email: 'investigator@cybershield.demo',
  },
  {
    key: 'SYS_ADMIN',
    label: 'System Administrator',
    sub: 'Fleet Management · Policy Control',
    icon: SlidersHorizontal,
    color: '#FFB800',
    bg: 'rgba(255,184,0,0.08)',
    border: 'rgba(255,184,0,0.35)',
    email: 'admin@cybershield.demo',
  },
  {
    key: 'ORG_MANAGER',
    label: 'Org Manager',
    sub: 'Executive Reports · Compliance Audit',
    icon: BarChart3,
    color: '#C084FC',
    bg: 'rgba(192,132,252,0.08)',
    border: 'rgba(192,132,252,0.35)',
    email: 'manager@cybershield.demo',
  },
]

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()

  const [selectedRole, setSelectedRole] = useState('ANALYST')
  const [email, setEmail] = useState('analyst@cybershield.demo')
  const [password, setPassword] = useState('CyberShield@2024')
  const [showPass, setShowPass] = useState(false)
  const [orgId, setOrgId] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const { data: tenantsData } = useQuery({
    queryKey: ['tenants'],
    queryFn: () => authAPI.tenants().then(r => r.data),
  })
  const tenants = tenantsData?.results || tenantsData || []

  const handleRoleSelect = (role) => {
    setSelectedRole(role.key)
    setEmail(role.email)
    setPassword('CyberShield@2024')
    setError('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    // — Frontend validation guard —
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!email.trim()) {
      setError('Email address is required.')
      toast.error('Email address is required.')
      return
    }
    if (!emailRegex.test(email.trim())) {
      setError('Please enter a valid email address.')
      toast.error('Please enter a valid email address.')
      return
    }
    if (!password) {
      setError('Password is required.')
      toast.error('Password is required.')
      return
    }

    setLoading(true)
    try {
      const user = await login(email, password)
      toast.success(`Welcome back, ${user?.first_name || user?.fullName || 'Agent'}!`)
      const routes = {
        ANALYST: '/analyst', INVESTIGATOR: '/forensics',
        SYS_ADMIN: '/admin', ORG_MANAGER: '/org', SUPER_ADMIN: '/analyst',
      }
      navigate(routes[user?.role] || '/analyst', { replace: true })
    } catch (err) {
      const msg = err?.response?.data?.detail 
        || (err?.response ? 'Invalid credentials. Please try again.' : 'Unable to connect to backend server (port 8000). Please ensure Django is running.')
      setError(msg)
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  const activeRole = ROLES.find(r => r.key === selectedRole)

  return (
    <>
      <style>{styles}</style>
      <div className="auth-grid-bg" />

      <div style={{ minHeight: '100vh', background: '#0B0F1A', display: 'flex', fontFamily: 'Inter, sans-serif' }}>

        {/* ── LEFT PANEL ── */}
        <div className="auth-left-bg" style={{ width: '42%', minHeight: '100vh', padding: '48px 40px', display: 'flex', flexDirection: 'column', borderRight: '1px solid rgba(255,255,255,0.06)', position: 'relative', overflowY: 'auto', flexShrink: 0 }}>

          {/* Ambient orb */}
          <div className="auth-orb" style={{ position: 'absolute', top: '30%', left: '20%', width: 280, height: 280, background: 'radial-gradient(circle, rgba(0,245,255,0.08) 0%, transparent 70%)', borderRadius: '50%', pointerEvents: 'none' }} />

          {/* Logo */}
          <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 10, marginBottom: 48 }}>
            <div style={{ background: 'rgba(0,245,255,0.1)', border: '1px solid rgba(0,245,255,0.3)', borderRadius: 8, padding: 7 }}>
              <Shield size={20} style={{ color: '#00F5FF' }} />
            </div>
            <span style={{ fontSize: 20, fontWeight: 800 }} className="auth-gradient-text">CyberShield</span>
          </Link>

          {/* Headline */}
          <div style={{ marginBottom: 32, position: 'relative' }}>
            <h1 style={{ fontSize: 28, fontWeight: 800, color: '#fff', lineHeight: 1.2, letterSpacing: '-0.02em', marginBottom: 10 }}>
              Secure Portal Access
            </h1>
            <p style={{ fontSize: 14, color: 'rgba(220,228,228,0.55)', lineHeight: 1.6 }}>
              Select your role to access your dedicated workspace. Each role has purpose-built tools and permissions tailored to your function.
            </p>
          </div>

          {/* Role Selector Cards */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, flex: 1, position: 'relative' }}>
            {ROLES.map(role => {
              const isActive = selectedRole === role.key
              return (
                <div
                  key={role.key}
                  className="role-card"
                  onClick={() => handleRoleSelect(role)}
                  style={{
                    border: isActive ? `1px solid ${role.border}` : '1px solid rgba(255,255,255,0.07)',
                    background: isActive ? role.bg : 'rgba(255,255,255,0.02)',
                    boxShadow: isActive ? `0 0 20px ${role.color}15` : 'none',
                  }}
                >
                  <div style={{ background: isActive ? `${role.color}18` : 'rgba(255,255,255,0.04)', border: `1px solid ${isActive ? role.border : 'rgba(255,255,255,0.06)'}`, borderRadius: 8, padding: 8, flexShrink: 0 }}>
                    <role.icon size={18} style={{ color: isActive ? role.color : 'rgba(220,228,228,0.5)' }} />
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 14, fontWeight: 600, color: isActive ? '#fff' : 'rgba(220,228,228,0.7)', marginBottom: 2 }}>{role.label}</div>
                    <div className="mono" style={{ fontSize: 10, color: isActive ? role.color : 'rgba(220,228,228,0.35)', letterSpacing: '0.04em' }}>{role.sub}</div>
                  </div>
                  {isActive && <ChevronRight size={14} style={{ color: role.color, flexShrink: 0 }} />}
                </div>
              )
            })}
          </div>

          {/* Bottom link */}
          <div style={{ marginTop: 32, paddingTop: 24, borderTop: '1px solid rgba(255,255,255,0.06)' }}>
            <p style={{ fontSize: 13, color: 'rgba(220,228,228,0.4)' }}>
              New organization?{' '}
              <Link to="/signup" style={{ color: '#00F5FF', textDecoration: 'none', fontWeight: 600 }}>Register here →</Link>
            </p>
            <p style={{ fontSize: 12, color: 'rgba(220,228,228,0.3)', marginTop: 8 }}>
              Security Analyst, Investigator, or Admin?{' '}
              <Link to="/signup" style={{ color: '#00E676', textDecoration: 'none', fontWeight: 500 }}>Create user account →</Link>
            </p>
          </div>
        </div>

        {/* ── RIGHT PANEL ── */}
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '48px 40px' }}>
          <div style={{ width: '100%', maxWidth: 420 }}>

            {/* Role active indicator */}
            {activeRole && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 32, background: activeRole.bg, border: `1px solid ${activeRole.border}`, borderRadius: 8, padding: '10px 14px' }}>
                <activeRole.icon size={16} style={{ color: activeRole.color }} />
                <span className="mono" style={{ fontSize: 11, color: activeRole.color, letterSpacing: '0.06em' }}>{activeRole.label.toUpperCase()} WORKSPACE</span>
              </div>
            )}

            <h2 style={{ fontSize: 32, fontWeight: 800, color: '#fff', letterSpacing: '-0.02em', marginBottom: 6 }}>Welcome Back</h2>
            <p style={{ fontSize: 15, color: 'rgba(220,228,228,0.5)', marginBottom: 32 }}>Authenticate to your CyberShield workspace</p>

            {/* Error */}
            {error && (
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, background: 'rgba(255,51,102,0.1)', border: '1px solid rgba(255,51,102,0.25)', borderRadius: 8, padding: '12px 16px', marginBottom: 20 }}>
                <AlertTriangle size={15} style={{ color: '#FF3366', flexShrink: 0, marginTop: 1 }} />
                <span style={{ fontSize: 13, color: '#FF3366', lineHeight: 1.5 }}>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>

              {/* Organization Selector */}
              {tenants.length > 0 && (
                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, color: 'rgba(220,228,228,0.55)', letterSpacing: '0.06em', textTransform: 'uppercase', display: 'block', marginBottom: 8 }}>Organization</label>
                  <div style={{ position: 'relative' }}>
                    <Building2 size={14} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'rgba(220,228,228,0.3)' }} />
                    <select className="auth-select" style={{ paddingLeft: 40 }} value={orgId} onChange={e => setOrgId(e.target.value)}>
                      <option value="">Select your organization...</option>
                      {tenants.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                    </select>
                  </div>
                </div>
              )}

              {/* Email */}
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: 'rgba(220,228,228,0.55)', letterSpacing: '0.06em', textTransform: 'uppercase', display: 'block', marginBottom: 8 }}>Work Email</label>
                <div style={{ position: 'relative' }}>
                  <Mail size={14} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'rgba(220,228,228,0.3)', pointerEvents: 'none' }} />
                  <input className="auth-input" type="email" placeholder="you@organization.com" value={email} onChange={e => setEmail(e.target.value)} required />
                </div>
              </div>

              {/* Password */}
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: 'rgba(220,228,228,0.55)', letterSpacing: '0.06em', textTransform: 'uppercase', display: 'block', marginBottom: 8 }}>Password</label>
                <div style={{ position: 'relative' }}>
                  <Lock size={14} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'rgba(220,228,228,0.3)', pointerEvents: 'none' }} />
                  <input className="auth-input" type={showPass ? 'text' : 'password'} placeholder="••••••••" value={password} onChange={e => setPassword(e.target.value)} required />
                  <button type="button" onClick={() => setShowPass(s => !s)} style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: 'rgba(220,228,228,0.35)', cursor: 'pointer', padding: 2 }}>
                    {showPass ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
                  <span style={{ fontSize: 11, color: 'rgba(220,228,228,0.45)' }}>
                    Demo password:{' '}
                    <code
                      style={{
                        color: '#00F5FF',
                        background: 'rgba(0,245,255,0.08)',
                        padding: '2px 6px',
                        borderRadius: 4,
                        cursor: 'pointer',
                        fontFamily: "'JetBrains Mono', monospace",
                      }}
                      title="Click to fill password"
                      onClick={() => setPassword('CyberShield@2024')}
                    >
                      CyberShield@2024
                    </code>
                  </span>
                  <Link to="/forgot-password" style={{ fontSize: 12, color: '#00F5FF', textDecoration: 'none', fontWeight: 500 }}>Forgot Password?</Link>
                </div>
              </div>

              {/* Submit */}
              <button className="auth-btn-primary" type="submit" disabled={loading}>
                {loading ? 'Authenticating...' : <><KeyRound size={15} /> Sign In to Workspace</>}
              </button>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '8px 0' }}>
                <div style={{ flex: 1, height: 1, background: 'rgba(255,255,255,0.07)' }} />
                <span style={{ fontSize: 10, color: 'rgba(220,228,228,0.25)', letterSpacing: '0.04em' }}>OR REGISTER</span>
                <div style={{ flex: 1, height: 1, background: 'rgba(255,255,255,0.07)' }} />
              </div>

              <Link
                to="/signup"
                className="auth-btn-google auth-btn-secondary"
                style={{
                  width: '100%',
                  padding: '12px',
                  background: 'rgba(0,245,255,0.05)',
                  border: '1px solid rgba(0,245,255,0.2)',
                  borderRadius: '8px',
                  color: '#00F5FF',
                  fontSize: '14px',
                  fontWeight: 600,
                  textDecoration: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  boxSizing: 'border-box'
                }}
              >
                Create New Account / Register Organization
              </Link>
            </form>

            {/* Security badge row */}
            <div style={{ marginTop: 32, paddingTop: 20, borderTop: '1px solid rgba(255,255,255,0.06)', display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
              {['JWT Secured', '256-bit TLS', 'Zero-Trust'].map(t => (
                <span key={t} className="mono" style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 10, color: 'rgba(220,228,228,0.3)', letterSpacing: '0.05em' }}>
                  <Lock size={10} style={{ color: '#00E676' }} /> {t}
                </span>
              ))}
            </div>

            <p style={{ textAlign: 'center', marginTop: 16, fontSize: 13, color: 'rgba(220,228,228,0.35)' }}>
              New to CyberShield?{' '}
              <Link to="/signup" style={{ color: '#00F5FF', textDecoration: 'none', fontWeight: 600 }}>Register your organization →</Link>
            </p>
          </div>
        </div>

      </div>
    </>
  )
}
