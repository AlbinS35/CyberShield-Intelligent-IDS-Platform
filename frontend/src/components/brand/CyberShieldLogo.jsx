import { Shield } from 'lucide-react'

const shieldSizes = {
  sm: 16,
  md: 20,
  lg: 24,
}

const textSizes = {
  sm: { name: 'text-base', tag: 'text-[10px]' },
  md: { name: 'text-xl', tag: 'text-[10px]' },
  lg: { name: 'text-2xl', tag: 'text-xs' },
}

export function CyberShieldMark({ size = 'md', className = '' }) {
  const shieldSize = shieldSizes[size] || shieldSizes.md;
  
  return (
    <div 
      className={`shrink-0 flex items-center justify-center rounded-lg border border-cyber-cyan/30 bg-cyber-cyan/10 ${className}`} 
      style={{ padding: shieldSize * 0.35 }}
      aria-hidden="true"
    >
      <Shield size={shieldSize} style={{ color: '#00F5FF' }} />
    </div>
  )
}

export default function CyberShieldLogo({
  size = 'md',
  showText = true,
  tagline = 'IDS Platform',
  className = '',
}) {
  const text = textSizes[size] || textSizes.md

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <CyberShieldMark size={size} />
      {showText && (
        <div className="min-w-0">
          <div className={`${text.name} font-extrabold auth-gradient-text`} style={{ letterSpacing: '-0.02em' }}>
            CyberShield
          </div>
          {tagline && (
            <div className={`${text.tag} font-mono uppercase tracking-widest text-cyber-cyan/65 leading-tight`}>
              {tagline}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
