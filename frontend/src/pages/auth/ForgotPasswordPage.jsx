import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Shield, Mail, ArrowLeft, CheckCircle2, AlertTriangle } from 'lucide-react'
import { authAPI } from '../../api'

const styles = `
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');
  .fp-grid-bg {
    background-image:
      linear-gradient(to right, rgba(0,245,255,0.04) 1px, transparent 1px),
      linear-gradient(to bottom, rgba(0,245,255,0.04) 1px, transparent 1px);
    background-size: 40px 40px;
    position: fixed; inset: 0; z-index: -2; pointer-events: none;
  }
  .fp-input {
    width: 100%; padding: 12px 14px 12px 44px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px; color: #dce4e4; font-size: 14px;
    outline: none; transition: all 0.25s ease;
    box-sizing: border-box; font-family: inherit;
  }
  .fp-input:focus {
    border-color: rgba(0,245,255,0.5);
    box-shadow: 0 0 0 3px rgba(0,245,255,0.08);
    background: rgba(0,245,255,0.02);
  }
  .fp-input::placeholder { color: rgba(220,228,228,0.3); }
  .fp-btn {
    width: 100%; padding: 13px;
    background: #00F5FF; color: #001a1a;
    font-size: 15px; font-weight: 700;
    border: none; border-radius: 8px; cursor: pointer;
    transition: all 0.25s ease; font-family: inherit;
  }
  .fp-btn:hover { background: #63f7ff; box-shadow: 0 0 24px rgba(0,245,255,0.4); transform: translateY(-1px); }
  .fp-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
  .fp-gradient-text {
    background: linear-gradient(135deg, #00F5FF 0%, #00E676 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  }
  .mono { font-family: 'JetBrains Mono', monospace; }
  @keyframes fpPulse { 0%,100%{ box-shadow: 0 0 8px #00E676; opacity:1; } 50%{ box-shadow: 0 0 2px #00E676; opacity:0.5; } }
  .fp-pulse { animation: fpPulse 2s ease-in-out infinite; }
`

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await authAPI.requestPasswordReset(email)
      setSent(true)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send reset email. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <style>{styles}</style>
      <div className="fp-grid-bg" />
      <div style={{ minHeight: '100vh', background: '#0B0F1A', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24, fontFamily: 'Inter, sans-serif' }}>
        {/* Ambient glow */}
        <div style={{ position: 'fixed', top: '30%', left: '50%', transform: 'translateX(-50%)', width: 400, height: 300, background: 'radial-gradient(circle, rgba(0,245,255,0.05) 0%, transparent 70%)', borderRadius: '50%', pointerEvents: 'none' }} />

        <div style={{ width: '100%', maxWidth: 420, position: 'relative' }}>
          {/* Logo */}
          <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 10, marginBottom: 48, justifyContent: 'center' }}>
            <div style={{ background: 'rgba(0,245,255,0.1)', border: '1px solid rgba(0,245,255,0.3)', borderRadius: 8, padding: 7 }}>
              <Shield size={20} style={{ color: '#00F5FF' }} />
            </div>
            <span style={{ fontSize: 20, fontWeight: 800 }} className="fp-gradient-text">CyberShield</span>
          </Link>

          <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.07)', backdropFilter: 'blur(16px)', borderRadius: 16, padding: 40 }}>
            {!sent ? (
              <>
                {/* Lock icon */}
                <div style={{ textAlign: 'center', marginBottom: 28 }}>
                  <div style={{ display: 'inline-flex', width: 64, height: 64, borderRadius: '50%', background: 'rgba(0,245,255,0.08)', border: '1px solid rgba(0,245,255,0.2)', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>
                    <Mail size={26} style={{ color: '#00F5FF' }} />
                  </div>
                  <h1 style={{ fontSize: 26, fontWeight: 800, color: '#fff', letterSpacing: '-0.02em', marginBottom: 8 }}>Forgot Password?</h1>
                  <p style={{ fontSize: 14, color: 'rgba(220,228,228,0.5)', lineHeight: 1.6 }}>
                    Enter your registered work email and we'll send you a secure link to reset your password.
                  </p>
                </div>

                {error && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, background: 'rgba(255,51,102,0.1)', border: '1px solid rgba(255,51,102,0.25)', borderRadius: 8, padding: '12px 16px', marginBottom: 20 }}>
                    <AlertTriangle size={15} style={{ color: '#FF3366', flexShrink: 0 }} />
                    <span style={{ fontSize: 13, color: '#FF3366' }}>{error}</span>
                  </div>
                )}

                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <div>
                    <label style={{ fontSize: 11, fontWeight: 600, color: 'rgba(220,228,228,0.45)', letterSpacing: '0.07em', textTransform: 'uppercase', display: 'block', marginBottom: 8 }}>Work Email</label>
                    <div style={{ position: 'relative' }}>
                      <Mail size={14} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'rgba(220,228,228,0.3)', pointerEvents: 'none' }} />
                      <input className="fp-input" type="email" placeholder="you@organization.com" value={email} onChange={e => setEmail(e.target.value)} required />
                    </div>
                  </div>
                  <button className="fp-btn" type="submit" disabled={loading}>
                    {loading ? 'Sending Reset Link...' : 'Send Reset Link'}
                  </button>
                </form>
              </>
            ) : (
              /* Success State */
              <div style={{ textAlign: 'center' }}>
                <div style={{ display: 'inline-flex', width: 72, height: 72, borderRadius: '50%', background: 'rgba(0,230,118,0.1)', border: '1px solid rgba(0,230,118,0.3)', alignItems: 'center', justifyContent: 'center', marginBottom: 20 }}>
                  <CheckCircle2 size={32} style={{ color: '#00E676' }} />
                </div>
                <h2 style={{ fontSize: 24, fontWeight: 800, color: '#fff', marginBottom: 12, letterSpacing: '-0.02em' }}>Reset Link Sent!</h2>
                <p style={{ fontSize: 14, color: 'rgba(220,228,228,0.55)', lineHeight: 1.7, marginBottom: 28 }}>
                  A password reset link has been sent to <br />
                  <strong style={{ color: '#00F5FF' }}>{email}</strong>.<br /><br />
                  Check your inbox and follow the instructions. The link expires in 30 minutes.
                </p>
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#00E676' }} className="fp-pulse" />
                  <span className="mono" style={{ color: '#00E676', fontSize: 11, letterSpacing: '0.06em' }}>SECURE LINK DISPATCHED</span>
                </div>
              </div>
            )}

            {/* Back to login */}
            <div style={{ marginTop: 28, paddingTop: 20, borderTop: '1px solid rgba(255,255,255,0.06)', textAlign: 'center' }}>
              <Link to="/login" style={{ color: 'rgba(220,228,228,0.5)', fontSize: 13, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 6, transition: 'color 0.2s' }}
                onMouseEnter={e => e.currentTarget.style.color = '#00F5FF'}
                onMouseLeave={e => e.currentTarget.style.color = 'rgba(220,228,228,0.5)'}
              >
                <ArrowLeft size={13} /> Back to Sign In
              </Link>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
