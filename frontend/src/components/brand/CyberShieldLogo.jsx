const markSizes = {
  sm: 'w-9 h-9',
  md: 'w-14 h-14',
  lg: 'w-16 h-16',
}

const textSizes = {
  sm: { name: 'text-sm', tag: 'text-[10px]' },
  md: { name: 'text-lg', tag: 'text-[10px]' },
  lg: { name: 'text-xl', tag: 'text-xs' },
}

export function CyberShieldMark({ size = 'md', className = '' }) {
  return (
    <div
      className={`${markSizes[size] || markSizes.md} ${className} relative shrink-0 rounded-2xl border border-cyber-cyan/35 bg-navy-950/80 shadow-cyber overflow-hidden`}
      aria-hidden="true"
    >
      <img
        src="/cybershield_logo.png"
        alt=""
        className="absolute left-1/2 top-1/2 h-[168%] w-[168%] max-w-none -translate-x-1/2 -translate-y-[58%] object-cover"
      />
      <div className="absolute inset-0 rounded-2xl ring-1 ring-inset ring-white/10" />
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
          <div className={`${text.name} font-extrabold tracking-wide text-white leading-tight`}>
            Cyber<span className="text-cyber-cyan">Shield</span>
          </div>
          <div className={`${text.tag} font-mono uppercase tracking-widest text-cyber-cyan/65 leading-tight`}>
            {tagline}
          </div>
        </div>
      )}
    </div>
  )
}
