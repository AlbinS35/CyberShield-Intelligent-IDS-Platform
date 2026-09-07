import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Shield, Eye, Lock, Fingerprint, SlidersHorizontal, BarChart3,
  CheckCircle2, ArrowRight, Zap, Activity, Radio, FileCheck,
  AlertTriangle, ChevronRight, Server, Globe, Users, Database,
  Play, Building2, KeyRound, Cpu, Search, X, PlayCircle,
  Award, Target, BookOpen, HeartHandshake
} from 'lucide-react'

/* ─── Inline CSS for animations not in Tailwind ─── */
const styles = `
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');

  .lp-grid-bg {
    background-image:
      linear-gradient(to right, rgba(0,245,255,0.04) 1px, transparent 1px),
      linear-gradient(to bottom, rgba(0,245,255,0.04) 1px, transparent 1px);
    background-size: 40px 40px;
    position: fixed; top:0; left:0; right:0; bottom:0;
    z-index: -2; pointer-events: none;
  }
  .lp-scan-line {
    width: 100%; height: 2px;
    background: linear-gradient(to right, transparent, rgba(0,245,255,0.25), transparent);
    position: fixed; top: 0; left: 0; z-index: -1; pointer-events: none;
    animation: lpScan 8s linear infinite;
  }
  @keyframes lpScan {
    0%   { transform: translateY(-10px); }
    100% { transform: translateY(100vh); }
  }
  .lp-glass {
    background: rgba(255,255,255,0.03);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.08);
    transition: all 0.3s ease;
  }
  .lp-glass:hover {
    background: rgba(0,245,255,0.04);
    border-color: rgba(0,245,255,0.2);
    box-shadow: 0 0 20px rgba(0,245,255,0.06);
  }
  .lp-pulse-green {
    animation: lpPulseGreen 2s ease-in-out infinite;
  }
  @keyframes lpPulseGreen {
    0%,100% { box-shadow: 0 0 6px #00E676; opacity:1; }
    50%      { box-shadow: 0 0 2px #00E676; opacity:0.5; }
  }
  .lp-pulse-red {
    animation: lpPulseRed 2s ease-in-out infinite;
  }
  @keyframes lpPulseRed {
    0%,100% { box-shadow: 0 0 10px rgba(255,51,102,0.7); }
    50%      { box-shadow: 0 0 3px rgba(255,51,102,0.3); }
  }
  .lp-glow-btn {
    background: #00F5FF;
    color: #001a1a;
    font-weight: 700;
    transition: all 0.25s ease;
  }
  .lp-glow-btn:hover {
    background: #63f7ff;
    box-shadow: 0 0 24px rgba(0,245,255,0.5);
    transform: translateY(-1px);
  }
  .lp-outline-btn {
    border: 1px solid rgba(0,245,255,0.5);
    color: #00F5FF;
    background: transparent;
    font-weight: 600;
    transition: all 0.25s ease;
  }
  .lp-outline-btn:hover {
    background: rgba(0,245,255,0.08);
    border-color: #00F5FF;
    box-shadow: 0 0 16px rgba(0,245,255,0.2);
  }
  .lp-gradient-text {
    background: linear-gradient(135deg, #00F5FF 0%, #00E676 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .lp-threat-ticker {
    animation: lpSlideIn 0.45s cubic-bezier(0.16,1,0.3,1);
  }
  @keyframes lpSlideIn {
    from { opacity:0; transform: translateY(-12px); }
    to   { opacity:1; transform: translateY(0); }
  }
  .mono { font-family: 'JetBrains Mono', monospace; }
  .lp-popular-badge {
    background: linear-gradient(135deg, #00F5FF, #00E676);
    color: #001a1a;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.1em;
    padding: 2px 10px;
    border-radius: 999px;
  }
  .lp-step-connector {
    flex: 1; height: 1px;
    background: linear-gradient(to right, rgba(0,245,255,0.4), rgba(0,245,255,0.1));
    position: relative;
  }
  .lp-step-connector::after {
    content: '';
    position: absolute; right: 0; top: -4px;
    border-left: 8px solid rgba(0,245,255,0.4);
    border-top: 4px solid transparent;
    border-bottom: 4px solid transparent;
  }
  .lp-tenant-border {
    border: 1px solid rgba(0,245,255,0.25);
    background: linear-gradient(135deg, rgba(0,245,255,0.04), rgba(0,230,118,0.04));
  }
  @keyframes lpFloat {
    0%,100% { transform: translateY(0px); }
    50%      { transform: translateY(-8px); }
  }
  .lp-float { animation: lpFloat 5s ease-in-out infinite; }

  /* ── Smooth scroll for the whole page ── */
  html { scroll-behavior: smooth; }

  /* ── Demo Modal ── */
  .lp-modal-overlay {
    position: fixed; inset: 0; z-index: 1000;
    background: rgba(0,0,0,0.85); backdrop-filter: blur(12px);
    display: flex; align-items: center; justify-content: center;
    animation: lpFadeIn 0.2s ease;
  }
  @keyframes lpFadeIn { from{opacity:0} to{opacity:1} }
  .lp-modal-box {
    background: #0d1515;
    border: 1px solid rgba(0,245,255,0.2);
    border-radius: 16px; padding: 0;
    width: 90%; max-width: 800px;
    box-shadow: 0 0 60px rgba(0,245,255,0.12);
    animation: lpModalUp 0.3s cubic-bezier(0.16,1,0.3,1);
    overflow: hidden;
  }
  @keyframes lpModalUp { from{transform:translateY(24px);opacity:0} to{transform:translateY(0);opacity:1} }
`

/* ─── Data ─── */
// Full rotating pool of realistic events — each 3s a new one prepends
const EVENT_POOL = [
  { severity: 'CRITICAL', color: '#FF3366', bg: 'rgba(255,51,102,0.1)',  event: 'DoS Attack — SQL Server',      src: '185.220.101.44', conf: '99.4%' },
  { severity: 'HIGH',     color: '#FF8C42', bg: 'rgba(255,140,66,0.1)',  event: 'Brute Force Login Attempt',    src: '45.33.32.156',   conf: '97.1%' },
  { severity: 'MEDIUM',   color: '#FFB800', bg: 'rgba(255,184,0,0.1)',   event: 'Port Scan Detected',           src: '192.0.2.88',     conf: '91.8%' },
  { severity: 'CRITICAL', color: '#FF3366', bg: 'rgba(255,51,102,0.1)',  event: 'Credential Stuffing Attack',   src: '103.21.244.0',   conf: '98.7%' },
  { severity: 'HIGH',     color: '#FF8C42', bg: 'rgba(255,140,66,0.1)',  event: 'Suspicious Lateral Movement',  src: '10.0.0.55',      conf: '94.2%' },
  { severity: 'LOW',      color: '#3B82F6', bg: 'rgba(59,130,246,0.1)',  event: 'Config Policy Violation',      src: 'admin@corp.com', conf: '88.0%' },
  { severity: 'CRITICAL', color: '#FF3366', bg: 'rgba(255,51,102,0.1)',  event: 'SQL Injection Payload Blocked', src: '198.51.100.9',   conf: '99.9%' },
  { severity: 'MEDIUM',   color: '#FFB800', bg: 'rgba(255,184,0,0.1)',   event: 'Unauthorized API Access',      src: '172.16.0.33',    conf: '90.5%' },
]
let _evtCounter = 1000
function makeEvent() {
  _evtCounter++
  const base = EVENT_POOL[_evtCounter % EVENT_POOL.length]
  return { ...base, id: `EVT-${_evtCounter}`, ts: new Date().toLocaleTimeString('en-IN', { hour12: false }) }
}

const WORKSPACES = [
  {
    role: 'Security Analyst',
    badge: 'SOC Tier-1',
    icon: Shield,
    color: '#00F5FF',
    borderColor: 'rgba(0,245,255,0.25)',
    glowColor: 'rgba(0,245,255,0.08)',
    features: [
      'Real-time WebSocket threat telemetry',
      'AI/ML attack classification (DoS, Probe, R2L, U2R)',
      'Instant severity alerts & incident escalation',
      'One-click automated IP containment triggers',
    ],
  },
  {
    role: 'Forensic Investigator',
    badge: 'Evidence Vault',
    icon: Fingerprint,
    color: '#00E676',
    borderColor: 'rgba(0,230,118,0.25)',
    glowColor: 'rgba(0,230,118,0.08)',
    features: [
      'SHA-256 cryptographic tamper-evident evidence sealing',
      'Chronological attack timeline reconstruction',
      'Immutable chain-of-custody tracking',
      'Court-admissible forensic case exports',
    ],
  },
  {
    role: 'System Administrator',
    badge: 'Fleet & Policies',
    icon: SlidersHorizontal,
    color: '#FFB800',
    borderColor: 'rgba(255,184,0,0.25)',
    glowColor: 'rgba(255,184,0,0.08)',
    features: [
      'Network asset registry & health monitoring',
      'Automated response playbook configuration',
      'Wazuh agent fleet synchronization',
      'IP blocklist management & rule governance',
    ],
  },
  {
    role: 'Org Manager',
    badge: 'Executive Oversight',
    icon: BarChart3,
    color: '#C084FC',
    borderColor: 'rgba(192,132,252,0.25)',
    glowColor: 'rgba(192,132,252,0.08)',
    features: [
      'Security metrics & risk posture dashboards',
      'Compliance report generation & download',
      'Audit trail & executive summaries',
      'Multi-tenant organization management',
    ],
  },
]

const CAPABILITIES = [
  { icon: Radio,         label: 'Real-time WebSocket Alerts' },
  { icon: Cpu,          label: 'Random Forest ML Classification' },
  { icon: Lock,         label: 'SHA-256 Tamper Sealing' },
  { icon: Shield,       label: 'Automated IP Blocking' },
  { icon: Users,        label: 'Multi-Tenant RBAC' },
  { icon: Fingerprint,  label: 'Chain of Custody Tracking' },
  { icon: FileCheck,    label: 'Compliance Report Export' },
  { icon: Server,       label: 'Wazuh API Bridge' },
]

const PLANS = [
  {
    name: 'Starter',
    price: '₹4,999',
    period: '/month',
    tag: null,
    desc: 'For small security teams getting started',
    features: ['Up to 5 users', '10 monitored assets', 'Basic ML detection', 'Alert management', 'Email support'],
    cta: 'Get Started',
    highlight: false,
  },
  {
    name: 'Professional',
    price: '₹14,999',
    period: '/month',
    tag: 'MOST POPULAR',
    desc: 'For growing security operations centers',
    features: ['Up to 25 users', '100 monitored assets', 'Full ML + forensics vault', 'Wazuh API integration', 'Playbook automation', 'Priority support'],
    cta: 'Start Free Trial',
    highlight: true,
  },
  {
    name: 'Enterprise',
    price: '₹39,999',
    period: '/month',
    tag: null,
    desc: 'For enterprise-grade security infrastructure',
    features: ['Unlimited users', 'Custom asset limit', 'All Pro features + SLA', 'Custom playbook rules', 'Dedicated support', 'On-prem deployment option'],
    cta: 'Contact Sales',
    highlight: false,
  },
]

const STEPS = [
  {
    number: '01',
    title: 'Detect',
    icon: Eye,
    color: '#00F5FF',
    desc: 'AI/ML engine continuously analyzes incoming network telemetry from Wazuh agents, classifying each event in real-time using our Random Forest classifier trained on the NSL-KDD dataset.',
  },
  {
    number: '02',
    title: 'Prevent',
    icon: Zap,
    color: '#FFB800',
    desc: 'Automated playbooks execute sub-second responses — IP blocks, device quarantine, network isolation — with full audit trail logging for every containment action.',
  },
  {
    number: '03',
    title: 'Investigate',
    icon: Search,
    color: '#00E676',
    desc: 'Cryptographic SHA-256 sealing on every log record ensures a legally admissible, tamper-proof chain of custody for full post-incident forensic investigation.',
  },
]

/* ─── Component ─── */
function scrollTo(id) {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

export default function LandingPage() {
  const navigate = useNavigate()
  const [isScrolled, setIsScrolled] = useState(false)
  const [showDemo, setShowDemo] = useState(false)

  // Live feed: keep a rolling list of max 4 events
  const [liveLog, setLiveLog] = useState(() => [makeEvent(), makeEvent(), makeEvent()])
  const [newEventKey, setNewEventKey] = useState(0)

  useEffect(() => {
    const iv = setInterval(() => {
      setLiveLog(prev => [makeEvent(), ...prev].slice(0, 4))
      setNewEventKey(k => k + 1)
    }, 2800)
    const onScroll = () => setIsScrolled(window.scrollY > 50)
    window.addEventListener('scroll', onScroll)
    return () => { clearInterval(iv); window.removeEventListener('scroll', onScroll) }
  }, [])

  return (
    <>
      <style>{styles}</style>
      <div className="lp-grid-bg" />
      <div className="lp-scan-line" />

      <div style={{ background: '#0B0F1A', minHeight: '100vh', color: '#dce4e4' }}>

        {/* ── DEMO MODAL ── */}
        {showDemo && (
          <div className="lp-modal-overlay" onClick={() => setShowDemo(false)}>
            <div className="lp-modal-box" onClick={e => e.stopPropagation()}>
              {/* Modal Header */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '18px 24px', borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div style={{ background: 'rgba(0,245,255,0.1)', border: '1px solid rgba(0,245,255,0.2)', borderRadius: 6, padding: 6 }}>
                    <PlayCircle size={16} style={{ color: '#00F5FF' }} />
                  </div>
                  <span style={{ fontSize: 15, fontWeight: 700, color: '#fff' }}>CyberShield Platform Demo</span>
                </div>
                <button onClick={() => setShowDemo(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'rgba(220,228,228,0.5)', padding: 4 }}>
                  <X size={18} />
                </button>
              </div>
              {/* Demo Content — workflow walkthrough */}
              <div style={{ padding: '28px 28px 24px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 24 }}>
                  {[
                    { step: '01', title: 'Org Registration', desc: 'DataSafe Financial registers as a tenant. All data is fully isolated by Tenant ID.', color: '#00F5FF' },
                    { step: '02', title: 'Analyst Onboarding', desc: 'Security Analyst joins with work email, selects role, and enters clearance code.', color: '#00E676' },
                    { step: '03', title: 'Attack Detected', desc: 'DoS on SQL server. ML classifies with 98% confidence → CRITICAL alert fired.', color: '#FF3366' },
                    { step: '04', title: 'Playbook Fires', desc: 'IP auto-blocked in <1s. Analyst escalates to the Forensic Investigator.', color: '#FFB800' },
                    { step: '05', title: 'Evidence Sealed', desc: 'SHA-256 hash seals all logs. Chain of custody preserved legally and immutably.', color: '#C084FC' },
                    { step: '06', title: 'Executive Report', desc: 'Org Manager downloads compliance report proving mitigation. Audit complete.', color: '#00E676' },
                  ].map(({ step, title, desc, color }) => (
                    <div key={step} style={{ background: 'rgba(255,255,255,0.02)', border: `1px solid ${color}22`, borderRadius: 10, padding: '14px 16px', display: 'flex', gap: 12 }}>
                      <span className="mono" style={{ fontSize: 11, color, fontWeight: 700, flexShrink: 0, marginTop: 2 }}>{step}</span>
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 700, color: '#fff', marginBottom: 4 }}>{title}</div>
                        <div style={{ fontSize: 12, color: 'rgba(220,228,228,0.5)', lineHeight: 1.5 }}>{desc}</div>
                      </div>
                    </div>
                  ))}
                </div>
                <div style={{ textAlign: 'center', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 20 }}>
                  <p className="mono" style={{ color: 'rgba(220,228,228,0.4)', fontSize: 11, marginBottom: 14 }}>Full video demo available upon request · CyberShield Enterprise Platform Demo</p>
                  <Link to="/signup" onClick={() => setShowDemo(false)}>
                    <button className="lp-glow-btn" style={{ padding: '11px 32px', borderRadius: 8, fontSize: 14, display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                      <Building2 size={14} /> Start Free Trial
                    </button>
                  </Link>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── NAVBAR ── */}
        <nav style={{
          position: 'fixed', top: 0, width: '100%', zIndex: 50,
          background: isScrolled ? 'rgba(11,15,26,0.92)' : 'rgba(11,15,26,0.7)',
          backdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(255,255,255,0.06)',
          boxShadow: isScrolled ? '0 0 30px rgba(0,245,255,0.08)' : 'none',
          transition: 'all 0.3s ease',
        }}>
          <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 32px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 72 }}>
            {/* Logo */}
            <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ background: 'rgba(0,245,255,0.1)', border: '1px solid rgba(0,245,255,0.3)', borderRadius: 8, padding: 6 }}>
                <Shield size={20} style={{ color: '#00F5FF' }} />
              </div>
              <span style={{ fontSize: 20, fontWeight: 800, letterSpacing: '-0.02em' }} className="lp-gradient-text">CyberShield</span>
            </Link>

            {/* Nav Links — smooth scroll via JS */}
            <div style={{ display: 'flex', gap: 36, alignItems: 'center' }}>
              {[['Features','features'],['How It Works','how-it-works'],['Pricing','pricing'],['About','about']].map(([label, id]) => (
                <button key={id} onClick={() => scrollTo(id)}
                  style={{ color: 'rgba(220,228,228,0.65)', fontSize: 14, fontWeight: 500, background: 'none', border: 'none', cursor: 'pointer', padding: 0, transition: 'color 0.2s' }}
                  onMouseEnter={e => e.currentTarget.style.color = '#00F5FF'}
                  onMouseLeave={e => e.currentTarget.style.color = 'rgba(220,228,228,0.65)'}
                >{label}</button>
              ))}
            </div>

            {/* CTA Buttons */}
            <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
              <Link to="/signup">
                <button className="lp-outline-btn" style={{ padding: '8px 20px', borderRadius: 6, fontSize: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Building2 size={14} /> Tenant Portal
                </button>
              </Link>
              <Link to="/login">
                <button className="lp-glow-btn" style={{ padding: '8px 22px', borderRadius: 6, fontSize: 14 }}>
                  Sign In
                </button>
              </Link>
            </div>
          </div>
        </nav>

        {/* ── HERO ── */}
        <section style={{ maxWidth: 1200, margin: '0 auto', padding: '140px 32px 80px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 64, alignItems: 'center' }}>

            {/* Left: Headlines */}
            <div>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: 'rgba(0,245,255,0.08)', border: '1px solid rgba(0,245,255,0.2)', borderRadius: 999, padding: '4px 14px', marginBottom: 24 }}>
                <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#00E676' }} className="lp-pulse-green" />
                <span className="mono" style={{ color: '#00F5FF', fontSize: 11, letterSpacing: '0.08em' }}>SYSTEM ONLINE · ALL AGENTS ACTIVE</span>
              </div>

              <h1 style={{ fontSize: 52, fontWeight: 900, lineHeight: 1.1, letterSpacing: '-0.03em', color: '#fff', marginBottom: 20 }}>
                Stop Threats.<br />
                Secure Evidence.<br />
                <span className="lp-gradient-text">Command Your Defense.</span>
              </h1>

              <p style={{ fontSize: 18, lineHeight: 1.7, color: 'rgba(220,228,228,0.7)', marginBottom: 36, maxWidth: 480 }}>
                AI-powered intrusion detection, automated threat prevention, and legally-resilient digital forensics — unified in one intelligent SaaS platform.
              </p>

              <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                <Link to="/signup">
                  <button className="lp-glow-btn" style={{ padding: '14px 32px', borderRadius: 8, fontSize: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                    Start Free Trial <ArrowRight size={16} />
                  </button>
                </Link>
                <button className="lp-outline-btn" onClick={() => setShowDemo(true)} style={{ padding: '14px 28px', borderRadius: 8, fontSize: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Play size={16} /> Watch Demo
                </button>
              </div>

              <div style={{ marginTop: 32, display: 'flex', gap: 24 }}>
                {['No credit card required', '14-day free trial', 'GDPR compliant'].map(t => (
                  <span key={t} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: 'rgba(220,228,228,0.5)' }}>
                    <CheckCircle2 size={13} style={{ color: '#00E676' }} /> {t}
                  </span>
                ))}
              </div>
            </div>

            {/* Right: Live Threat Dashboard Preview — real-time animated feed */}
            <div className="lp-float">
              <div style={{ borderRadius: 16, overflow: 'hidden', position: 'relative', border: '1px solid rgba(0,245,255,0.15)', boxShadow: '0 0 60px rgba(0,245,255,0.08)', background: 'rgba(11,15,26,0.8)', backdropFilter: 'blur(12px)' }}>
                {/* Dashboard Header */}
                <div style={{ background: 'rgba(0,245,255,0.04)', borderBottom: '1px solid rgba(255,255,255,0.06)', padding: '14px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#00E676' }} className="lp-pulse-green" />
                    <span className="mono" style={{ color: '#00E676', fontSize: 11, letterSpacing: '0.08em' }}>LIVE THREAT FEED · DATASAFE FINANCIAL</span>
                  </div>
                  <span className="mono" style={{ color: '#00F5FF', fontSize: 11, background: 'rgba(0,245,255,0.1)', border: '1px solid rgba(0,245,255,0.2)', padding: '3px 10px', borderRadius: 4 }}>
                    ≥98% ML Confidence
                  </span>
                </div>

                {/* Events — new ones animate from top */}
                <div style={{ padding: '4px 0', minHeight: 160 }}>
                  {liveLog.map((ev, i) => (
                    <div
                      key={`${ev.id}-${newEventKey}`}
                      className={i === 0 ? 'lp-threat-ticker' : ''}
                      style={{
                        padding: '11px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                        borderBottom: i < liveLog.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none',
                        background: i === 0 ? `${ev.color}08` : 'transparent',
                        transition: 'background 0.5s ease',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <AlertTriangle size={13} style={{ color: ev.color, flexShrink: 0 }} />
                        <div>
                          <div className="mono" style={{ fontSize: 12, color: '#dce4e4', fontWeight: 500 }}>{ev.event}</div>
                          <div className="mono" style={{ fontSize: 10, color: 'rgba(220,228,228,0.4)', marginTop: 2 }}>src: {ev.src} · {ev.ts} · conf: {ev.conf}</div>
                        </div>
                      </div>
                      <span className="mono" style={{
                        fontSize: 10, fontWeight: 700, padding: '3px 8px', borderRadius: 4,
                        color: ev.color, background: ev.bg, border: `1px solid ${ev.color}33`,
                        letterSpacing: '0.06em', flexShrink: 0,
                      }}>{ev.severity}</span>
                    </div>
                  ))}
                </div>

                {/* Stats footer */}
                <div style={{ background: 'rgba(0,0,0,0.25)', borderTop: '1px solid rgba(255,255,255,0.04)', padding: '10px 20px', display: 'flex', gap: 24 }}>
                  {[['CRITICAL', 'Active Threat'], ['<1s', 'Response Time'], ['99.7%', 'ML Accuracy']].map(([val, lbl]) => (
                    <div key={lbl}>
                      <div className="mono" style={{ color: '#00F5FF', fontSize: 13, fontWeight: 700 }}>{val}</div>
                      <div className="mono" style={{ color: 'rgba(220,228,228,0.35)', fontSize: 10 }}>{lbl}</div>
                    </div>
                  ))}
                </div>

                {/* Ambient glow */}
                <div style={{ position: 'absolute', top: -40, right: -40, width: 120, height: 120, background: 'rgba(0,245,255,0.12)', borderRadius: '50%', filter: 'blur(50px)', pointerEvents: 'none' }} />
              </div>
            </div>
          </div>
        </section>

        {/* ── LIVE STATS BAR ── */}
        <section style={{ maxWidth: 1200, margin: '0 auto', padding: '0 32px 80px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 20 }}>
            {[
              { val: '2.4M+', lbl: 'Threats Blocked', icon: Shield },
              { val: '99.7%', lbl: 'ML Accuracy', icon: Cpu },
              { val: '<50ms', lbl: 'Detection Latency', icon: Activity },
              { val: '150+', lbl: 'Enterprises Protected', icon: Globe },
            ].map(({ val, lbl, icon: Icon }) => (
              <div key={lbl} className="lp-glass" style={{ borderRadius: 12, padding: '24px', textAlign: 'center' }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#00E676', margin: '0 auto 12px' }} className="lp-pulse-green" />
                <div style={{ fontSize: 32, fontWeight: 800, color: '#00F5FF', letterSpacing: '-0.02em', lineHeight: 1 }}>{val}</div>
                <div className="mono" style={{ color: 'rgba(220,228,228,0.5)', fontSize: 11, marginTop: 8, letterSpacing: '0.04em', textTransform: 'uppercase' }}>{lbl}</div>
              </div>
            ))}
          </div>
        </section>

        {/* ── FEATURES / WORKSPACES ── */}
        <section id="features" style={{ maxWidth: 1200, margin: '0 auto', padding: '80px 32px' }}>
          <div style={{ textAlign: 'center', marginBottom: 56 }}>
            <span className="mono" style={{ color: '#00F5FF', fontSize: 11, letterSpacing: '0.12em', textTransform: 'uppercase' }}>Role-Based Access</span>
            <h2 style={{ fontSize: 40, fontWeight: 800, color: '#fff', marginTop: 8, letterSpacing: '-0.02em' }}>Four Specialized Security Workspaces</h2>
            <p style={{ color: 'rgba(220,228,228,0.55)', fontSize: 17, marginTop: 12, maxWidth: 600, margin: '12px auto 0' }}>
              Every role gets a purpose-built dashboard with the exact tools they need — no noise, no distractions.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 24 }}>
            {WORKSPACES.map(({ role, badge, icon: Icon, color, borderColor, glowColor, features }) => (
              <div key={role} className="lp-glass" style={{ borderRadius: 16, padding: 28, border: `1px solid ${borderColor}`, position: 'relative', overflow: 'hidden' }}>
                <div style={{ position: 'absolute', top: -30, right: -30, width: 100, height: 100, background: glowColor, borderRadius: '50%', filter: 'blur(40px)', pointerEvents: 'none' }} />
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14, marginBottom: 16 }}>
                  <div style={{ background: glowColor, border: `1px solid ${borderColor}`, borderRadius: 10, padding: 10, flexShrink: 0 }}>
                    <Icon size={22} style={{ color }} />
                  </div>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <h3 style={{ fontSize: 18, fontWeight: 700, color: '#fff' }}>{role}</h3>
                      <span className="mono" style={{ fontSize: 10, color, background: `${color}18`, border: `1px solid ${color}33`, padding: '2px 8px', borderRadius: 4, letterSpacing: '0.06em' }}>{badge}</span>
                    </div>
                  </div>
                </div>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {features.map(f => (
                    <li key={f} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 14, color: 'rgba(220,228,228,0.7)' }}>
                      <CheckCircle2 size={14} style={{ color, flexShrink: 0, marginTop: 2 }} />{f}
                    </li>
                  ))}
                </ul>
                <div style={{ marginTop: 20, borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 16 }}>
                  <Link to="/login" style={{ color, fontSize: 13, fontWeight: 600, textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 6 }}>
                    Access Workspace <ChevronRight size={14} />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── HOW IT WORKS ── */}
        <section id="how-it-works" style={{ maxWidth: 1200, margin: '0 auto', padding: '80px 32px' }}>
          <div style={{ textAlign: 'center', marginBottom: 56 }}>
            <span className="mono" style={{ color: '#00F5FF', fontSize: 11, letterSpacing: '0.12em', textTransform: 'uppercase' }}>The Platform Pipeline</span>
            <h2 style={{ fontSize: 40, fontWeight: 800, color: '#fff', marginTop: 8, letterSpacing: '-0.02em' }}>How CyberShield Works</h2>
          </div>

          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 0 }}>
            {STEPS.map((step, i) => (
              <div key={step.title} style={{ display: 'flex', flex: 1, alignItems: 'flex-start' }}>
                <div style={{ flex: 1, padding: '0 20px' }}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ position: 'relative', display: 'inline-block', marginBottom: 20 }}>
                      <div style={{ width: 72, height: 72, borderRadius: '50%', background: `${step.color}14`, border: `2px solid ${step.color}44`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <step.icon size={28} style={{ color: step.color }} />
                      </div>
                      <div className="mono" style={{ position: 'absolute', top: -8, right: -8, width: 24, height: 24, borderRadius: '50%', background: step.color, color: '#001a1a', fontSize: 10, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        {step.number.slice(-1)}
                      </div>
                    </div>
                    <h3 style={{ fontSize: 22, fontWeight: 700, color: '#fff', marginBottom: 12 }}>{step.title}</h3>
                    <p style={{ fontSize: 14, lineHeight: 1.7, color: 'rgba(220,228,228,0.6)', maxWidth: 280, margin: '0 auto' }}>{step.desc}</p>
                  </div>
                </div>
                {i < STEPS.length - 1 && (
                  <div style={{ display: 'flex', alignItems: 'center', paddingTop: 36, width: 60, flexShrink: 0 }}>
                    <div className="lp-step-connector" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* ── CAPABILITIES ── */}
        <section style={{ maxWidth: 1200, margin: '0 auto', padding: '80px 32px' }}>
          <div style={{ textAlign: 'center', marginBottom: 48 }}>
            <span className="mono" style={{ color: '#00F5FF', fontSize: 11, letterSpacing: '0.12em', textTransform: 'uppercase' }}>Core Capabilities</span>
            <h2 style={{ fontSize: 40, fontWeight: 800, color: '#fff', marginTop: 8, letterSpacing: '-0.02em' }}>Built for Modern Security Operations</h2>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 16 }}>
            {CAPABILITIES.map(({ icon: Icon, label }) => (
              <div key={label} className="lp-glass" style={{ borderRadius: 12, padding: '20px 18px', display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ background: 'rgba(0,245,255,0.08)', border: '1px solid rgba(0,245,255,0.15)', borderRadius: 8, padding: 8, flexShrink: 0 }}>
                  <Icon size={16} style={{ color: '#00F5FF' }} />
                </div>
                <span style={{ fontSize: 13, fontWeight: 500, color: 'rgba(220,228,228,0.8)' }}>{label}</span>
              </div>
            ))}
          </div>
        </section>

        {/* ── PRICING ── */}
        <section id="pricing" style={{ maxWidth: 1200, margin: '0 auto', padding: '80px 32px' }}>
          <div style={{ textAlign: 'center', marginBottom: 56 }}>
            <span className="mono" style={{ color: '#00F5FF', fontSize: 11, letterSpacing: '0.12em', textTransform: 'uppercase' }}>Transparent Pricing</span>
            <h2 style={{ fontSize: 40, fontWeight: 800, color: '#fff', marginTop: 8, letterSpacing: '-0.02em' }}>Simple Plans in ₹ Indian Rupees</h2>
            <p style={{ color: 'rgba(220,228,228,0.5)', fontSize: 16, marginTop: 10 }}>No hidden fees. Cancel anytime.</p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 24 }}>
            {PLANS.map(({ name, price, period, tag, desc, features, cta, highlight }) => (
              <div key={name} style={{
                borderRadius: 16, padding: 32,
                background: highlight ? 'rgba(0,245,255,0.05)' : 'rgba(255,255,255,0.02)',
                border: highlight ? '1px solid rgba(0,245,255,0.35)' : '1px solid rgba(255,255,255,0.08)',
                backdropFilter: 'blur(12px)',
                position: 'relative', overflow: 'hidden',
                boxShadow: highlight ? '0 0 40px rgba(0,245,255,0.1)' : 'none',
              }}>
                {tag && (
                  <div style={{ position: 'absolute', top: 20, right: 20 }}>
                    <span className="lp-popular-badge">{tag}</span>
                  </div>
                )}
                <h3 style={{ fontSize: 20, fontWeight: 700, color: highlight ? '#00F5FF' : '#dce4e4', marginBottom: 4 }}>{name}</h3>
                <p style={{ fontSize: 13, color: 'rgba(220,228,228,0.5)', marginBottom: 20 }}>{desc}</p>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 4, marginBottom: 28 }}>
                  <span style={{ fontSize: 40, fontWeight: 900, color: '#fff', letterSpacing: '-0.03em' }}>{price}</span>
                  <span className="mono" style={{ fontSize: 12, color: 'rgba(220,228,228,0.4)' }}>{period}</span>
                </div>
                <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 28px', display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {features.map(f => (
                    <li key={f} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 14, color: 'rgba(220,228,228,0.75)' }}>
                      <CheckCircle2 size={14} style={{ color: highlight ? '#00F5FF' : '#00E676', flexShrink: 0 }} />{f}
                    </li>
                  ))}
                </ul>
                <Link to="/signup">
                  <button
                    className={highlight ? 'lp-glow-btn' : 'lp-outline-btn'}
                    style={{ width: '100%', padding: '12px', borderRadius: 8, fontSize: 14, cursor: 'pointer' }}
                  >{cta}</button>
                </Link>
              </div>
            ))}
          </div>
        </section>

        {/* ── TENANT REGISTRATION CTA ── */}
        <section style={{ maxWidth: 1200, margin: '0 auto', padding: '80px 32px' }}>
          <div className="lp-tenant-border" style={{ borderRadius: 20, padding: '60px 48px', textAlign: 'center', position: 'relative', overflow: 'hidden' }}>
            <div style={{ position: 'absolute', top: -60, left: '50%', transform: 'translateX(-50%)', width: 300, height: 200, background: 'rgba(0,245,255,0.06)', borderRadius: '50%', filter: 'blur(60px)', pointerEvents: 'none' }} />
            <div style={{ position: 'relative' }}>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: 'rgba(0,230,118,0.1)', border: '1px solid rgba(0,230,118,0.25)', borderRadius: 999, padding: '4px 14px', marginBottom: 20 }}>
                <Building2 size={12} style={{ color: '#00E676' }} />
                <span className="mono" style={{ color: '#00E676', fontSize: 11, letterSpacing: '0.08em' }}>FOR ORGANIZATIONS</span>
              </div>
              <h2 style={{ fontSize: 40, fontWeight: 800, color: '#fff', marginBottom: 16, letterSpacing: '-0.02em' }}>Register Your Organization</h2>
              <p style={{ fontSize: 17, color: 'rgba(220,228,228,0.65)', maxWidth: 540, margin: '0 auto 36px', lineHeight: 1.7 }}>
                Set up CyberShield for your company in minutes. Create your tenant portal, onboard your security team, and start protecting your infrastructure today.
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
                <Link to="/signup">
                  <button className="lp-glow-btn" style={{ padding: '16px 48px', borderRadius: 10, fontSize: 16, display: 'flex', alignItems: 'center', gap: 10 }}>
                    <Building2 size={18} /> Register as Organization / Tenant
                  </button>
                </Link>
                <Link to="/login" style={{ color: 'rgba(0,245,255,0.7)', fontSize: 14, textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 6 }}>
                  Already have a tenant? Sign in to your portal <ArrowRight size={13} />
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* ── ABOUT SECTION ── */}
        <section id="about" style={{ maxWidth: 1200, margin: '0 auto', padding: '80px 32px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 64, alignItems: 'center' }}>
            {/* Left */}
            <div>
              <span className="mono" style={{ color: '#00F5FF', fontSize: 11, letterSpacing: '0.12em', textTransform: 'uppercase' }}>About CyberShield</span>
              <h2 style={{ fontSize: 40, fontWeight: 800, color: '#fff', marginTop: 10, marginBottom: 18, letterSpacing: '-0.02em', lineHeight: 1.15 }}>
                Built for the Real World of Cybersecurity
              </h2>
              <p style={{ fontSize: 16, color: 'rgba(220,228,228,0.6)', lineHeight: 1.75, marginBottom: 24 }}>
                CyberShield was designed for organizations handling highly confidential records, financial data, and client information — organizations that need <strong style={{ color: '#dce4e4' }}>enterprise-grade security without enterprise-scale complexity.</strong>
              </p>
              <p style={{ fontSize: 16, color: 'rgba(220,228,228,0.6)', lineHeight: 1.75, marginBottom: 32 }}>
                Every feature — from the Random Forest ML classifier to the SHA-256 forensic vault — was built to solve the specific challenges faced by small-to-medium organizations with limited security budgets but zero tolerance for data breaches.
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                {[
                  { icon: Target,         color: '#00F5FF', title: 'Precision Detection', desc: 'NSL-KDD trained ML with >90% accuracy' },
                  { icon: Award,          color: '#00E676', title: 'Court-Admissible', desc: 'Legally resilient SHA-256 evidence' },
                  { icon: BookOpen,       color: '#FFB800', title: 'Compliance Ready', desc: 'GDPR & IT Act 2000 aligned exports' },
                  { icon: HeartHandshake, color: '#C084FC', title: 'Multi-Tenant SaaS', desc: 'Fully isolated per-org data model' },
                ].map(({ icon: Icon, color, title, desc }) => (
                  <div key={title} style={{ display: 'flex', gap: 12, alignItems: 'flex-start', background: 'rgba(255,255,255,0.02)', border: `1px solid ${color}22`, borderRadius: 10, padding: '14px 16px' }}>
                    <div style={{ background: `${color}14`, border: `1px solid ${color}28`, borderRadius: 7, padding: 7, flexShrink: 0 }}>
                      <Icon size={15} style={{ color }} />
                    </div>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 700, color: '#dce4e4', marginBottom: 3 }}>{title}</div>
                      <div style={{ fontSize: 12, color: 'rgba(220,228,228,0.45)' }}>{desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            {/* Right — Use case scenario card */}
            <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(0,245,255,0.12)', borderRadius: 16, padding: 28, position: 'relative', overflow: 'hidden' }}>
              <div style={{ position: 'absolute', top: -40, right: -40, width: 160, height: 160, background: 'rgba(0,245,255,0.06)', borderRadius: '50%', filter: 'blur(50px)', pointerEvents: 'none' }} />
              <div className="mono" style={{ color: '#00F5FF', fontSize: 10, letterSpacing: '0.1em', marginBottom: 18, textTransform: 'uppercase' }}>Real-World Use Case</div>
              <h3 style={{ fontSize: 18, fontWeight: 700, color: '#fff', marginBottom: 6 }}>DataSafe Financial Solutions</h3>
              <p className="mono" style={{ fontSize: 11, color: 'rgba(220,228,228,0.4)', marginBottom: 20 }}>Banking & Finance · Enterprise Security Operations · 80 employees</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {[
                  { actor: 'System Admin', action: 'Registers database servers as monitored assets, configures CRITICAL-level response playbooks', color: '#FFB800' },
                  { actor: 'Security Analyst', action: 'Receives live DoS attack alert → verifies auto-blocked IP via ML classification → escalates to Investigator', color: '#00F5FF' },
                  { actor: 'Forensic Investigator', action: 'Opens forensic case, uploads PCAP evidence, all logs are SHA-256 hash-sealed by the platform', color: '#00E676' },
                  { actor: 'Org Manager', action: 'Downloads compliance report with tamper-proof evidence integrity for regulatory submission', color: '#C084FC' },
                ].map(({ actor, action, color }) => (
                  <div key={actor} style={{ display: 'flex', gap: 12, alignItems: 'flex-start', paddingBottom: 12, borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: color, flexShrink: 0, marginTop: 5 }} />
                    <div>
                      <span style={{ fontSize: 12, fontWeight: 700, color: '#dce4e4' }}>{actor}</span>
                      <span style={{ fontSize: 12, color: 'rgba(220,228,228,0.5)', display: 'block', marginTop: 2, lineHeight: 1.5 }}>{action}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* ── FOOTER ── */}
        <footer style={{ borderTop: '1px solid rgba(255,255,255,0.05)', padding: '48px 32px', background: 'rgba(0,0,0,0.2)' }}>
          <div style={{ maxWidth: 1200, margin: '0 auto', display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr', gap: 40 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
                <div style={{ background: 'rgba(0,245,255,0.1)', border: '1px solid rgba(0,245,255,0.3)', borderRadius: 6, padding: 5 }}>
                  <Shield size={16} style={{ color: '#00F5FF' }} />
                </div>
                <span style={{ fontSize: 17, fontWeight: 800 }} className="lp-gradient-text">CyberShield</span>
              </div>
              <p className="mono" style={{ color: 'rgba(220,228,228,0.35)', fontSize: 12, lineHeight: 1.7 }}>
                Vigilant Technical Excellence.<br />
                AI-powered IDS/IPS & Digital Forensics Platform.
              </p>
              <p className="mono" style={{ color: 'rgba(220,228,228,0.25)', fontSize: 11, marginTop: 14 }}>
                © 2026 CyberShield. All rights reserved.
              </p>
            </div>
            {[
              { title: 'Platform', links: ['Features', 'Pricing', 'Documentation', 'API Reference'] },
              { title: 'Security', links: ['Privacy Policy', 'Security Disclosure', 'Terms of Service', 'Compliance'] },
              { title: 'Support', links: ['Contact Us', 'Status Page', 'Community', 'Careers'] },
            ].map(({ title, links }) => (
              <div key={title}>
                <h4 className="mono" style={{ color: 'rgba(220,228,228,0.5)', fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 16 }}>{title}</h4>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {links.map(l => (
                    <li key={l}><a href="#" style={{ color: 'rgba(220,228,228,0.5)', fontSize: 14, textDecoration: 'none', transition: 'color 0.2s' }}
                      onMouseEnter={e => e.target.style.color = '#00F5FF'}
                      onMouseLeave={e => e.target.style.color = 'rgba(220,228,228,0.5)'}
                    >{l}</a></li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </footer>

      </div>
    </>
  )
}
