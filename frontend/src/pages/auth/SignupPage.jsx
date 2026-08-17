import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { useQuery } from '@tanstack/react-query'
import { useGoogleLogin } from '@react-oauth/google'
import { authAPI } from '../../api'
import {
  Shield, Fingerprint, SlidersHorizontal, BarChart3,
  Eye, EyeOff, Mail, Lock, Phone, User, Building2,
  CheckCircle2, AlertTriangle, Briefcase, KeyRound, Info
} from 'lucide-react'
import toast from 'react-hot-toast'

const styles = `
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');
  .su-grid-bg {
    background-image:
      linear-gradient(to right, rgba(0,245,255,0.04) 1px, transparent 1px),
      linear-gradient(to bottom, rgba(0,245,255,0.04) 1px, transparent 1px);
    background-size: 40px 40px;
    position: fixed; inset: 0; z-index: -2; pointer-events: none;
  }
  .su-input {
    width: 100%; padding: 11px 14px 11px 42px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    color: #dce4e4; font-size: 14px;
    outline: none; transition: all 0.25s ease;
    box-sizing: border-box;
    font-family: inherit;
  }
  .su-input:focus {
    border-color: rgba(0,245,255,0.5);
    box-shadow: 0 0 0 3px rgba(0,245,255,0.08);
    background: rgba(0,245,255,0.02);
  }
  .su-input::placeholder { color: rgba(220,228,228,0.3); }
  .su-input-noicon {
    width: 100%; padding: 11px 14px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    color: #dce4e4; font-size: 14px;
    outline: none; transition: all 0.25s ease;
    box-sizing: border-box;
    font-family: inherit;
  }
  .su-input-noicon:focus {
    border-color: rgba(0,245,255,0.5);
    box-shadow: 0 0 0 3px rgba(0,245,255,0.08);
  }
  .su-input-noicon::placeholder { color: rgba(220,228,228,0.3); }
  .su-select {
    width: 100%; padding: 11px 14px 11px 42px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    color: #dce4e4; font-size: 14px;
    outline: none; transition: all 0.25s ease;
    box-sizing: border-box; cursor: pointer;
    font-family: inherit; appearance: none;
  }
  .su-select:focus { border-color: rgba(0,245,255,0.5); box-shadow: 0 0 0 3px rgba(0,245,255,0.08); }
  .su-select option { background: #0d1515; color: #dce4e4; }
  .su-btn {
    width: 100%; padding: 13px;
    background: #00F5FF; color: #001a1a;
    font-size: 15px; font-weight: 700;
    border: none; border-radius: 8px;
    cursor: pointer; transition: all 0.25s ease;
    font-family: inherit;
    display: flex; align-items: center; justify-content: center; gap: 8px;
  }
  .su-btn:hover {
    background: #63f7ff;
    box-shadow: 0 0 24px rgba(0,245,255,0.4);
    transform: translateY(-1px);
  }
  .su-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
  .su-btn-google {
    width: 100%; padding: 12px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 8px; color: rgba(220,228,228,0.85);
    font-size: 14px; font-weight: 500;
    cursor: pointer; transition: all 0.25s ease;
    font-family: inherit;
    display: flex; align-items: center; justify-content: center; gap: 10px;
  }
  .su-btn-google:hover {
    border-color: rgba(66,133,244,0.5);
    background: rgba(66,133,244,0.08);
    color: #fff;
    box-shadow: 0 0 16px rgba(66,133,244,0.15);
  }
  .su-btn-google:disabled { opacity: 0.6; cursor: not-allowed; }
  .su-tab {
    flex: 1; padding: 10px 16px; text-align: center;
    font-size: 13px; font-weight: 600; cursor: pointer;
    border: none; background: transparent;
    transition: all 0.2s ease; border-radius: 8px;
    font-family: inherit;
  }
  .su-tab-active {
    background: rgba(0,245,255,0.1);
    color: #00F5FF;
    box-shadow: 0 0 16px rgba(0,245,255,0.1);
  }
  .su-tab-inactive { color: rgba(220,228,228,0.45); }
  .su-tab-inactive:hover { color: rgba(220,228,228,0.7); background: rgba(255,255,255,0.03); }
  .su-role-card {
    padding: 12px 14px; border-radius: 10px;
    cursor: pointer; transition: all 0.2s ease;
    display: flex; align-items: center; gap: 10px;
    border: 1px solid rgba(255,255,255,0.07);
    background: rgba(255,255,255,0.02);
  }
  .su-role-card:hover { background: rgba(255,255,255,0.05); }
  .su-gradient-text {
    background: linear-gradient(135deg, #00F5FF 0%, #00E676 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  }
  .mono { font-family: 'JetBrains Mono', monospace; }
  @keyframes suGlow { 0%,100% { opacity:0.4; } 50% { opacity:0.65; } }
  .su-orb { animation: suGlow 6s ease-in-out infinite; }
`

const ROLES = [
  { key: 'ANALYST',      label: 'Security Analyst',      icon: Shield,            color: '#00F5FF', bg: 'rgba(0,245,255,0.08)',   border: 'rgba(0,245,255,0.35)',   desc: 'Live threat monitoring & triage' },
  { key: 'INVESTIGATOR', label: 'Forensic Investigator',  icon: Fingerprint,       color: '#00E676', bg: 'rgba(0,230,118,0.08)',  border: 'rgba(0,230,118,0.35)',   desc: 'Evidence vault & chain of custody' },
  { key: 'SYS_ADMIN',   label: 'System Admin',           icon: SlidersHorizontal, color: '#FFB800', bg: 'rgba(255,184,0,0.08)',  border: 'rgba(255,184,0,0.35)',   desc: 'Fleet management & playbooks' },
  { key: 'ORG_MANAGER',  label: 'Org Manager',            icon: BarChart3,         color: '#C084FC', bg: 'rgba(192,132,252,0.08)', border: 'rgba(192,132,252,0.35)', desc: 'Executive oversight & compliance' },
]

const INDUSTRIES = ['Banking & Finance', 'Healthcare', 'Information Technology', 'Auditing & Accounting', 'Legal & Compliance', 'Government & Defense', 'Education', 'Retail & E-commerce', 'Manufacturing', 'Other']

// Google logo SVG
function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
    </svg>
  )
}

function InputField({ icon: Icon, label, type = 'text', placeholder, value, onChange, required = false, error, children }) {
  return (
    <div>
      {label && <label style={{ fontSize: 11, fontWeight: 600, color: 'rgba(220,228,228,0.45)', letterSpacing: '0.07em', textTransform: 'uppercase', display: 'block', marginBottom: 7 }}>{label}</label>}
      <div style={{ position: 'relative' }}>
        {Icon && <Icon size={13} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'rgba(220,228,228,0.3)', pointerEvents: 'none' }} />}
        {children || (
          <input
            className={Icon ? 'su-input' : 'su-input-noicon'}
            type={type}
            placeholder={placeholder}
            value={value}
            onChange={onChange}
            required={required}
            style={error ? { borderColor: '#FF3366', boxShadow: '0 0 0 2px rgba(255,51,102,0.15)' } : {}}
          />
        )}
      </div>
      {error && <span style={{ fontSize: 10, color: '#FF3366', marginTop: 4, display: 'block', fontWeight: 500 }}>{error}</span>}
    </div>
  )
}

export default function SignupPage() {
  const navigate = useNavigate()
  const { login, loginWithGoogle } = useAuth()

  const [tab, setTab] = useState('org') // 'org' | 'user'
  const [loading, setLoading] = useState(false)
  const [googleLoading, setGoogleLoading] = useState(false)
  const [error, setError] = useState('')
  const [validationErrors, setValidationErrors] = useState({})

  // Org Registration fields
  const [orgName, setOrgName] = useState('')
  const [industry, setIndustry] = useState('')
  const [contactEmail, setContactEmail] = useState('')
  const [adminName, setAdminName] = useState('')
  const [phone, setPhone] = useState('')
  const [orgPassword, setOrgPassword] = useState('')
  const [orgConfirmPass, setOrgConfirmPass] = useState('')
  const [showOrgPass, setShowOrgPass] = useState(false)
  const [acceptTerms, setAcceptTerms] = useState(false)

  // User Registration fields
  const [fullName, setFullName] = useState('')
  const [userEmail, setUserEmail] = useState('')
  const [userPhone, setUserPhone] = useState('')
  const [selectedRole, setSelectedRole] = useState('ANALYST')
  const [orgId, setOrgId] = useState('')
  const [clearanceCode, setClearanceCode] = useState('')
  const [userPassword, setUserPassword] = useState('')
  const [userConfirmPass, setUserConfirmPass] = useState('')
  const [showUserPass, setShowUserPass] = useState(false)

  const { data: tenantsData } = useQuery({
    queryKey: ['tenants'],
    queryFn: () => authAPI.tenants().then(r => r.data),
  })
  const tenants = tenantsData?.results || tenantsData || []

  const handleOrgSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setValidationErrors({})
    const errors = {}

    if (!orgName.trim()) {
      errors.orgName = 'Organization Name is required.'
    }
    if (!industry) {
      errors.industry = 'Industry/Sector is required.'
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!contactEmail.trim()) {
      errors.contactEmail = 'Primary contact email is required.'
    } else if (!emailRegex.test(contactEmail)) {
      errors.contactEmail = 'Please provide a valid work email address.'
    }

    if (!adminName.trim()) {
      errors.adminName = 'Administrator name is required.'
    } else {
      const parts = adminName.trim().split(" ")
      if (parts.length < 2) {
        errors.adminName = 'Please provide both first and last name.'
      }
    }

    const phoneClean = phone.replace(/[\s()-]/g, '')
    const phoneRegex = /^\+?[0-9]{10,15}$/
    if (phone && !phoneRegex.test(phoneClean)) {
      errors.phone = 'Please enter a valid phone number (10-15 digits).'
    }

    if (!orgPassword) {
      errors.orgPassword = 'Password is required.'
    } else {
      if (orgPassword.length < 8) {
        errors.orgPassword = 'Password must be at least 8 characters.'
      } else if (!/[A-Z]/.test(orgPassword)) {
        errors.orgPassword = 'Password must contain at least one uppercase letter.'
      } else if (!/[a-z]/.test(orgPassword)) {
        errors.orgPassword = 'Password must contain at least one lowercase letter.'
      } else if (!/[0-9]/.test(orgPassword)) {
        errors.orgPassword = 'Password must contain at least one number.'
      } else if (!/[^A-Za-z0-9]/.test(orgPassword)) {
        errors.orgPassword = 'Password must contain at least one special character.'
      }
    }

    if (orgPassword !== orgConfirmPass) {
      errors.orgConfirmPass = 'Passwords do not match.'
    }

    if (!acceptTerms) {
      setError('Please accept the Terms of Service.')
      return
    }

    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors)
      toast.error('Please correct the validation errors below.')
      return
    }

    setLoading(true)
    try {
      await authAPI.register({
        email: contactEmail,
        password: orgPassword,
        full_name: adminName,
        phone_no: phone,
        role: 'ORG_MANAGER',
      })
      const user = await login(contactEmail, orgPassword)
      toast.success(`Organization registered! Welcome, ${adminName}.`)
      navigate('/org')
    } catch (err) {
      const msg = err?.response?.data?.email?.[0] || err?.response?.data?.detail || 'Registration failed. Please try again.'
      setError(msg)
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  const handleUserSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setValidationErrors({})
    const errors = {}

    if (!fullName.trim()) {
      errors.fullName = 'Full Name is required.'
    } else {
      const parts = fullName.trim().split(" ")
      if (parts.length < 2) {
        errors.fullName = 'Please provide both first and last name.'
      }
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!userEmail.trim()) {
      errors.userEmail = 'Work email is required.'
    } else if (!emailRegex.test(userEmail)) {
      errors.userEmail = 'Please provide a valid work email address.'
    }

    const phoneClean = userPhone.replace(/[\s()-]/g, '')
    const phoneRegex = /^\+?[0-9]{10,15}$/
    if (userPhone && !phoneRegex.test(phoneClean)) {
      errors.userPhone = 'Please enter a valid phone number (10-15 digits).'
    }

    if (!orgId) {
      errors.orgId = 'Please select your organization.'
    }

    if (!clearanceCode.trim()) {
      errors.clearanceCode = 'Clearance code is required. Obtain it from your System Administrator.'
    }

    if (!userPassword) {
      errors.userPassword = 'Password is required.'
    } else {
      if (userPassword.length < 8) {
        errors.userPassword = 'Password must be at least 8 characters.'
      } else if (!/[A-Z]/.test(userPassword)) {
        errors.userPassword = 'Password must contain at least one uppercase letter.'
      } else if (!/[a-z]/.test(userPassword)) {
        errors.userPassword = 'Password must contain at least one lowercase letter.'
      } else if (!/[0-9]/.test(userPassword)) {
        errors.userPassword = 'Password must contain at least one number.'
      } else if (!/[^A-Za-z0-9]/.test(userPassword)) {
        errors.userPassword = 'Password must contain at least one special character.'
      }
    }

    if (userPassword !== userConfirmPass) {
      errors.userConfirmPass = 'Passwords do not match.'
    }

    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors)
      toast.error('Please correct the validation errors below.')
      return
    }

    setLoading(true)
    try {
      await authAPI.register({
        email: userEmail,
        password: userPassword,
        full_name: fullName,
        phone_no: userPhone,
        role: selectedRole,
        org_id: orgId || '',
        clearance_code: clearanceCode,
      })
      const user = await login(userEmail, userPassword)
      toast.success(`Account created! Welcome, ${fullName}.`)
      const routes = { ANALYST: '/analyst', INVESTIGATOR: '/forensics', SYS_ADMIN: '/admin', ORG_MANAGER: '/org' }
      navigate(routes[selectedRole] || '/analyst')
    } catch (err) {
      const msg = err?.response?.data?.email?.[0] || err?.response?.data?.detail || 'Registration failed.'
      setError(msg)
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  // Google sign-up/sign-in via popup
  const handleGoogleSignup = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      setGoogleLoading(true)
      setError('')
      try {
        const user = await loginWithGoogle(tokenResponse.access_token)
        toast.success(`Welcome, ${user?.fullName || 'Agent'}!`)
        const routes = { ANALYST: '/analyst', INVESTIGATOR: '/forensics', SYS_ADMIN: '/admin', ORG_MANAGER: '/org', SUPER_ADMIN: '/analyst' }
        navigate(routes[user?.role] || '/analyst')
      } catch (err) {
        const msg = err?.response?.data?.detail ||
          'Google sign-up received. To fully enable Google OAuth, configure the /auth/google/ backend endpoint.'
        toast.error(msg, { duration: 5000 })
        setError(msg)
      } finally {
        setGoogleLoading(false)
      }
    },
    onError: () => toast.error('Google sign-up was cancelled or failed.'),
  })

  return (
    <>
      <style>{styles}</style>
      <div className="su-grid-bg" />

      <div style={{ minHeight: '100vh', background: '#0B0F1A', display: 'flex', fontFamily: 'Inter, sans-serif' }}>

        {/* ── LEFT PANEL ── */}
        <div style={{ width: '38%', minHeight: '100vh', padding: '48px 36px', display: 'flex', flexDirection: 'column', borderRight: '1px solid rgba(255,255,255,0.06)', background: 'linear-gradient(160deg, rgba(0,245,255,0.05) 0%, rgba(0,230,118,0.03) 50%, transparent 100%)', position: 'relative', overflow: 'hidden', flexShrink: 0 }}>

          {/* Ambient orb */}
          <div className="su-orb" style={{ position: 'absolute', bottom: '20%', left: '10%', width: 260, height: 260, background: 'radial-gradient(circle, rgba(0,230,118,0.07) 0%, transparent 70%)', borderRadius: '50%', pointerEvents: 'none' }} />

          {/* Logo */}
          <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 10, marginBottom: 40 }}>
            <div style={{ background: 'rgba(0,245,255,0.1)', border: '1px solid rgba(0,245,255,0.3)', borderRadius: 8, padding: 7 }}>
              <Shield size={20} style={{ color: '#00F5FF' }} />
            </div>
            <span style={{ fontSize: 20, fontWeight: 800 }} className="su-gradient-text">CyberShield</span>
          </Link>

          <div style={{ position: 'relative' }}>
            <h1 style={{ fontSize: 28, fontWeight: 900, color: '#fff', lineHeight: 1.15, letterSpacing: '-0.02em', marginBottom: 10 }}>
              Join CyberShield
            </h1>
            <p style={{ fontSize: 14, color: 'rgba(220,228,228,0.55)', lineHeight: 1.65, marginBottom: 32 }}>
              Protect your organization with AI-powered intrusion detection and legally-resilient digital forensics.
            </p>

            {/* ── WHO SHOULD USE WHICH TAB — clear guidance ── */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 32 }}>

              {/* Org tab guidance */}
              <div style={{ background: 'rgba(0,245,255,0.05)', border: '1px solid rgba(0,245,255,0.2)', borderRadius: 10, padding: '14px 16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                  <Building2 size={14} style={{ color: '#00F5FF' }} />
                  <span style={{ fontSize: 12, fontWeight: 700, color: '#00F5FF' }}>Register Organization tab</span>
                </div>
                <p style={{ fontSize: 12, color: 'rgba(220,228,228,0.5)', lineHeight: 1.5 }}>
                  Use this if you are <strong style={{ color: '#dce4e4' }}>setting up CyberShield for your company</strong> for the first time. You become the Org Manager (owner/admin of your tenant).
                </p>
              </div>

              {/* User tab guidance */}
              <div style={{ background: 'rgba(0,230,118,0.05)', border: '1px solid rgba(0,230,118,0.2)', borderRadius: 10, padding: '14px 16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                  <User size={14} style={{ color: '#00E676' }} />
                  <span style={{ fontSize: 12, fontWeight: 700, color: '#00E676' }}>Create User Account tab</span>
                </div>
                <p style={{ fontSize: 12, color: 'rgba(220,228,228,0.5)', lineHeight: 1.5 }}>
                  Use this if you are a <strong style={{ color: '#dce4e4' }}>Security Analyst, Forensic Investigator, or System Admin</strong> joining an existing organization. Your System Administrator will give you the clearance code.
                </p>
              </div>
            </div>

            {/* Feature Bullets */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {[
                { icon: Shield,      color: '#00F5FF', title: 'AI/ML Threat Detection',   desc: 'Random Forest classifier with >90% accuracy' },
                { icon: Fingerprint, color: '#00E676', title: 'Digital Forensics Vault',   desc: 'SHA-256 sealed evidence with legal chain-of-custody' },
                { icon: Lock,        color: '#C084FC', title: 'Multi-Tenant RBAC',         desc: 'Role-gated workspaces with JWT zero-trust access' },
              ].map(({ icon: Icon, color, title, desc }) => (
                <div key={title} style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                  <div style={{ background: `${color}14`, border: `1px solid ${color}30`, borderRadius: 8, padding: 7, flexShrink: 0, marginTop: 1 }}>
                    <Icon size={14} style={{ color }} />
                  </div>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#dce4e4', marginBottom: 2 }}>{title}</div>
                    <div style={{ fontSize: 11, color: 'rgba(220,228,228,0.45)', lineHeight: 1.5 }}>{desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Bottom link */}
          <div style={{ marginTop: 'auto', paddingTop: 32, borderTop: '1px solid rgba(255,255,255,0.06)' }}>
            <p style={{ fontSize: 13, color: 'rgba(220,228,228,0.4)' }}>
              Already registered?{' '}
              <Link to="/login" style={{ color: '#00F5FF', textDecoration: 'none', fontWeight: 600 }}>Sign In →</Link>
            </p>
          </div>
        </div>

        {/* ── RIGHT PANEL ── */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '48px 40px', display: 'flex', justifyContent: 'center' }}>
          <div style={{ width: '100%', maxWidth: 520 }}>

            {/* Tab Switcher */}
            <div style={{ display: 'flex', gap: 4, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 10, padding: 4, marginBottom: 24 }}>
              <button className={`su-tab ${tab === 'org' ? 'su-tab-active' : 'su-tab-inactive'}`} onClick={() => { setTab('org'); setError('') }}>
                <Building2 size={13} style={{ display: 'inline', marginRight: 6, verticalAlign: 'middle' }} />
                Register Organization
              </button>
              <button className={`su-tab ${tab === 'user' ? 'su-tab-active' : 'su-tab-inactive'}`} onClick={() => { setTab('user'); setError('') }}>
                <User size={13} style={{ display: 'inline', marginRight: 6, verticalAlign: 'middle' }} />
                Create User Account
              </button>
            </div>

            {/* Context hint banner */}
            {tab === 'user' && (
              <div style={{ background: 'rgba(0,230,118,0.06)', border: '1px solid rgba(0,230,118,0.2)', borderRadius: 8, padding: '10px 14px', marginBottom: 20, display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                <CheckCircle2 size={14} style={{ color: '#00E676', flexShrink: 0, marginTop: 1 }} />
                <p style={{ fontSize: 12, color: 'rgba(220,228,228,0.6)', lineHeight: 1.5, margin: 0 }}>
                  <strong style={{ color: '#00E676' }}>Security Analyst / Forensic Investigator / System Admin:</strong> Use this tab. Your organization's System Administrator will provide your clearance code and organization ID.
                </p>
              </div>
            )}
            {tab === 'org' && (
              <div style={{ background: 'rgba(0,245,255,0.06)', border: '1px solid rgba(0,245,255,0.2)', borderRadius: 8, padding: '10px 14px', marginBottom: 20, display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                <Building2 size={14} style={{ color: '#00F5FF', flexShrink: 0, marginTop: 1 }} />
                <p style={{ fontSize: 12, color: 'rgba(220,228,228,0.6)', lineHeight: 1.5, margin: 0 }}>
                  <strong style={{ color: '#00F5FF' }}>Organization Owner:</strong> Register your company here. After registration, you can onboard your team members and generate clearance codes from your admin dashboard.
                </p>
              </div>
            )}

            {/* Google Sign-Up */}
            <button
              className="su-btn-google"
              onClick={() => handleGoogleSignup()}
              disabled={googleLoading || loading}
              style={{ marginBottom: 16 }}
            >
              <GoogleIcon />
              {googleLoading ? 'Signing up with Google...' : 'Continue with Google'}
            </button>

            {/* OR Divider */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
              <div style={{ flex: 1, height: 1, background: 'rgba(255,255,255,0.07)' }} />
              <span className="mono" style={{ fontSize: 11, color: 'rgba(220,228,228,0.3)', letterSpacing: '0.06em' }}>OR USE EMAIL</span>
              <div style={{ flex: 1, height: 1, background: 'rgba(255,255,255,0.07)' }} />
            </div>

            {/* Error */}
            {error && (
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, background: 'rgba(255,51,102,0.1)', border: '1px solid rgba(255,51,102,0.25)', borderRadius: 8, padding: '12px 16px', marginBottom: 20 }}>
                <AlertTriangle size={15} style={{ color: '#FF3366', flexShrink: 0, marginTop: 1 }} />
                <span style={{ fontSize: 13, color: '#FF3366', lineHeight: 1.5 }}>{error}</span>
              </div>
            )}

            {/* ── ORGANIZATION REGISTRATION TAB ── */}
            {tab === 'org' && (
              <form onSubmit={handleOrgSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
                <div>
                  <h2 style={{ fontSize: 22, fontWeight: 800, color: '#fff', letterSpacing: '-0.02em', marginBottom: 4 }}>Organization Registration</h2>
                  <p style={{ fontSize: 13, color: 'rgba(220,228,228,0.45)' }}>Set up your tenant and onboard your security team</p>
                </div>

                <InputField icon={Building2} label="Organization Name" placeholder="e.g. DataSafe Financial Solutions" value={orgName} onChange={e => setOrgName(e.target.value)} required error={validationErrors.orgName} />

                <div>
                  <label style={{ fontSize: 11, fontWeight: 600, color: 'rgba(220,228,228,0.45)', letterSpacing: '0.07em', textTransform: 'uppercase', display: 'block', marginBottom: 7 }}>Industry / Sector</label>
                  <div style={{ position: 'relative' }}>
                    <Briefcase size={13} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'rgba(220,228,228,0.3)', pointerEvents: 'none' }} />
                    <select className="su-select" value={industry} onChange={e => setIndustry(e.target.value)} required style={validationErrors.industry ? { borderColor: '#FF3366', boxShadow: '0 0 0 2px rgba(255,51,102,0.15)' } : {}}>
                      <option value="">Select your industry...</option>
                      {INDUSTRIES.map(i => <option key={i} value={i}>{i}</option>)}
                    </select>
                  </div>
                  {validationErrors.industry && <span style={{ fontSize: 10, color: '#FF3366', marginTop: 4, display: 'block', fontWeight: 500 }}>{validationErrors.industry}</span>}
                </div>

                <InputField icon={Mail} label="Primary Contact Email" type="email" placeholder="contact@yourorganization.com" value={contactEmail} onChange={e => setContactEmail(e.target.value)} required error={validationErrors.contactEmail} />

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                  <InputField icon={User} label="Your Full Name (Admin)" placeholder="Full name" value={adminName} onChange={e => setAdminName(e.target.value)} required error={validationErrors.adminName} />
                  <InputField icon={Phone} label="Phone Number" type="tel" placeholder="+91 98765 43210" value={phone} onChange={e => setPhone(e.target.value)} error={validationErrors.phone} />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                  <div>
                    <label style={{ fontSize: 11, fontWeight: 600, color: 'rgba(220,228,228,0.45)', letterSpacing: '0.07em', textTransform: 'uppercase', display: 'block', marginBottom: 7 }}>Password</label>
                    <div style={{ position: 'relative' }}>
                      <Lock size={13} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'rgba(220,228,228,0.3)', pointerEvents: 'none' }} />
                      <input className="su-input" type={showOrgPass ? 'text' : 'password'} placeholder="Min. 8 characters" value={orgPassword} onChange={e => setOrgPassword(e.target.value)} required style={validationErrors.orgPassword ? { borderColor: '#FF3366', boxShadow: '0 0 0 2px rgba(255,51,102,0.15)' } : {}} />
                      <button type="button" onClick={() => setShowOrgPass(s => !s)} style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'rgba(220,228,228,0.35)', padding: 2 }}>
                        {showOrgPass ? <EyeOff size={13} /> : <Eye size={13} />}
                      </button>
                    </div>
                    {validationErrors.orgPassword && <span style={{ fontSize: 10, color: '#FF3366', marginTop: 4, display: 'block', fontWeight: 500 }}>{validationErrors.orgPassword}</span>}
                  </div>
                  <div>
                    <label style={{ fontSize: 11, fontWeight: 600, color: 'rgba(220,228,228,0.45)', letterSpacing: '0.07em', textTransform: 'uppercase', display: 'block', marginBottom: 7 }}>Confirm Password</label>
                    <div style={{ position: 'relative' }}>
                      <Lock size={13} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'rgba(220,228,228,0.3)', pointerEvents: 'none' }} />
                      <input className="su-input" type="password" placeholder="Repeat password" value={orgConfirmPass} onChange={e => setOrgConfirmPass(e.target.value)} required style={validationErrors.orgConfirmPass ? { borderColor: '#FF3366', boxShadow: '0 0 0 2px rgba(255,51,102,0.15)' } : {}} />
                    </div>
                    {validationErrors.orgConfirmPass && <span style={{ fontSize: 10, color: '#FF3366', marginTop: 4, display: 'block', fontWeight: 500 }}>{validationErrors.orgConfirmPass}</span>}
                  </div>
                </div>

                <label style={{ display: 'flex', gap: 12, alignItems: 'flex-start', cursor: 'pointer' }}>
                  <div style={{ position: 'relative', marginTop: 1, flexShrink: 0 }}>
                    <div onClick={() => setAcceptTerms(a => !a)} style={{ width: 16, height: 16, borderRadius: 4, border: `1px solid ${acceptTerms ? '#00F5FF' : 'rgba(255,255,255,0.15)'}`, background: acceptTerms ? 'rgba(0,245,255,0.15)' : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', transition: 'all 0.2s' }}>
                      {acceptTerms && <CheckCircle2 size={10} style={{ color: '#00F5FF' }} />}
                    </div>
                  </div>
                  <span style={{ fontSize: 13, color: 'rgba(220,228,228,0.55)', lineHeight: 1.5 }}>
                    I agree to CyberShield's{' '}
                    <a href="#" style={{ color: '#00F5FF', textDecoration: 'none' }}>Terms of Service</a>
                    {' '}and{' '}
                    <a href="#" style={{ color: '#00F5FF', textDecoration: 'none' }}>Security Protocols</a>
                  </span>
                </label>

                <button className="su-btn" type="submit" disabled={loading || googleLoading}>
                  {loading ? 'Registering...' : <><Building2 size={15} /> Register Organization</>}
                </button>

                <p className="mono" style={{ textAlign: 'center', fontSize: 11, color: 'rgba(220,228,228,0.3)', lineHeight: 1.6 }}>
                  After registration, share your Organization ID with team members so they can join via "Create User Account".
                </p>
              </form>
            )}

            {/* ── USER ACCOUNT TAB ── */}
            {tab === 'user' && (
              <form onSubmit={handleUserSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
                <div>
                  <h2 style={{ fontSize: 22, fontWeight: 800, color: '#fff', letterSpacing: '-0.02em', marginBottom: 4 }}>Create User Account</h2>
                  <p style={{ fontSize: 13, color: 'rgba(220,228,228,0.45)' }}>Join your organization's security team with your assigned role</p>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                  <InputField icon={User} label="Full Name" placeholder="Your full name" value={fullName} onChange={e => setFullName(e.target.value)} required error={validationErrors.fullName} />
                  <InputField icon={Phone} label="Phone" type="tel" placeholder="+91 98765 43210" value={userPhone} onChange={e => setUserPhone(e.target.value)} error={validationErrors.userPhone} />
                </div>

                <InputField icon={Mail} label="Work Email" type="email" placeholder="you@organization.com" value={userEmail} onChange={e => setUserEmail(e.target.value)} required error={validationErrors.userEmail} />

                {/* Role Selector */}
                <div>
                  <label style={{ fontSize: 11, fontWeight: 600, color: 'rgba(220,228,228,0.45)', letterSpacing: '0.07em', textTransform: 'uppercase', display: 'block', marginBottom: 10 }}>
                    Select Your Role <span style={{ color: '#00F5FF', fontSize: 10 }}>— Choose the role your admin assigned you</span>
                  </label>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                    {ROLES.map(role => {
                      const isActive = selectedRole === role.key
                      return (
                        <div key={role.key} className="su-role-card" onClick={() => setSelectedRole(role.key)}
                          style={{ border: isActive ? `1px solid ${role.border}` : '1px solid rgba(255,255,255,0.07)', background: isActive ? role.bg : 'rgba(255,255,255,0.02)', boxShadow: isActive ? `0 0 16px ${role.color}15` : 'none' }}>
                          <div style={{ background: isActive ? `${role.color}18` : 'rgba(255,255,255,0.04)', border: `1px solid ${isActive ? role.border : 'rgba(255,255,255,0.06)'}`, borderRadius: 6, padding: 6, flexShrink: 0 }}>
                            <role.icon size={14} style={{ color: isActive ? role.color : 'rgba(220,228,228,0.4)' }} />
                          </div>
                          <div>
                            <div style={{ fontSize: 12, fontWeight: 600, color: isActive ? '#fff' : 'rgba(220,228,228,0.6)' }}>{role.label}</div>
                            <div className="mono" style={{ fontSize: 9, color: isActive ? role.color : 'rgba(220,228,228,0.3)', marginTop: 2 }}>{role.desc}</div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>

                {/* Org Selector */}
                {tenants.length > 0 ? (
                  <div>
                    <label style={{ fontSize: 11, fontWeight: 600, color: 'rgba(220,228,228,0.45)', letterSpacing: '0.07em', textTransform: 'uppercase', display: 'block', marginBottom: 7 }}>Organization</label>
                    <div style={{ position: 'relative' }}>
                      <Building2 size={13} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'rgba(220,228,228,0.3)', pointerEvents: 'none' }} />
                      <select className="su-select" value={orgId} onChange={e => setOrgId(e.target.value)} style={validationErrors.orgId ? { borderColor: '#FF3366', boxShadow: '0 0 0 2px rgba(255,51,102,0.15)' } : {}}>
                        <option value="">Select organization...</option>
                        {tenants.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                      </select>
                    </div>
                    {validationErrors.orgId && <span style={{ fontSize: 10, color: '#FF3366', marginTop: 4, display: 'block', fontWeight: 500 }}>{validationErrors.orgId}</span>}
                  </div>
                ) : (
                  <InputField icon={Building2} label="Organization ID" placeholder="Enter your Organization ID (from your admin)" value={orgId} onChange={e => setOrgId(e.target.value)} error={validationErrors.orgId} />
                )}

                {/* Clearance Code */}
                <div style={{ background: 'rgba(255,184,0,0.04)', border: '1px solid rgba(255,184,0,0.2)', borderRadius: 10, padding: '14px 16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                    <KeyRound size={13} style={{ color: '#FFB800' }} />
                    <span style={{ fontSize: 11, fontWeight: 700, color: '#FFB800', letterSpacing: '0.07em', textTransform: 'uppercase' }}>Security Clearance Code</span>
                    <div title="This passcode is set by your System Administrator to prevent unauthorized public registrations. Ask your org admin for this code." style={{ cursor: 'help' }}>
                      <Info size={12} style={{ color: 'rgba(220,228,228,0.35)' }} />
                    </div>
                  </div>
                  <div style={{ position: 'relative' }}>
                    <KeyRound size={13} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'rgba(220,228,228,0.3)', pointerEvents: 'none' }} />
                    <input
                      className="su-input"
                      type="password"
                      placeholder="Enter org clearance / security passcode"
                      value={clearanceCode}
                      onChange={e => setClearanceCode(e.target.value)}
                      required
                      style={validationErrors.clearanceCode ? { borderColor: '#FF3366', boxShadow: '0 0 0 2px rgba(255,51,102,0.15)' } : {}}
                    />
                  </div>
                  {validationErrors.clearanceCode && <span style={{ fontSize: 10, color: '#FF3366', marginTop: 4, display: 'block', fontWeight: 500 }}>{validationErrors.clearanceCode}</span>}
                  <p className="mono" style={{ fontSize: 10, color: 'rgba(220,228,228,0.35)', marginTop: 8, lineHeight: 1.5 }}>
                    Ask your System Administrator for this passcode. It prevents unauthorized public signups.
                  </p>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                  <div>
                    <label style={{ fontSize: 11, fontWeight: 600, color: 'rgba(220,228,228,0.45)', letterSpacing: '0.07em', textTransform: 'uppercase', display: 'block', marginBottom: 7 }}>Password</label>
                    <div style={{ position: 'relative' }}>
                      <Lock size={13} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'rgba(220,228,228,0.3)', pointerEvents: 'none' }} />
                      <input className="su-input" type={showUserPass ? 'text' : 'password'} placeholder="Min. 8 characters" value={userPassword} onChange={e => setUserPassword(e.target.value)} required style={validationErrors.userPassword ? { borderColor: '#FF3366', boxShadow: '0 0 0 2px rgba(255,51,102,0.15)' } : {}} />
                      <button type="button" onClick={() => setShowUserPass(s => !s)} style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'rgba(220,228,228,0.35)', padding: 2 }}>
                        {showUserPass ? <EyeOff size={13} /> : <Eye size={13} />}
                      </button>
                    </div>
                    {validationErrors.userPassword && <span style={{ fontSize: 10, color: '#FF3366', marginTop: 4, display: 'block', fontWeight: 500 }}>{validationErrors.userPassword}</span>}
                  </div>
                  <div>
                    <label style={{ fontSize: 11, fontWeight: 600, color: 'rgba(220,228,228,0.45)', letterSpacing: '0.07em', textTransform: 'uppercase', display: 'block', marginBottom: 7 }}>Confirm Password</label>
                    <div style={{ position: 'relative' }}>
                      <Lock size={13} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'rgba(220,228,228,0.3)', pointerEvents: 'none' }} />
                      <input className="su-input" type="password" placeholder="Repeat password" value={userConfirmPass} onChange={e => setUserConfirmPass(e.target.value)} required style={validationErrors.userConfirmPass ? { borderColor: '#FF3366', boxShadow: '0 0 0 2px rgba(255,51,102,0.15)' } : {}} />
                    </div>
                    {validationErrors.userConfirmPass && <span style={{ fontSize: 10, color: '#FF3366', marginTop: 4, display: 'block', fontWeight: 500 }}>{validationErrors.userConfirmPass}</span>}
                  </div>
                </div>

                <button className="su-btn" type="submit" disabled={loading || googleLoading}>
                  {loading ? 'Creating Account...' : <><Shield size={15} /> Create Account</>}
                </button>
              </form>
            )}

            <p style={{ textAlign: 'center', marginTop: 24, fontSize: 13, color: 'rgba(220,228,228,0.35)' }}>
              Already have an account?{' '}
              <Link to="/login" style={{ color: '#00F5FF', textDecoration: 'none', fontWeight: 600 }}>Sign In →</Link>
            </p>
          </div>
        </div>

      </div>
    </>
  )
}
