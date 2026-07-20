/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // CyberShield Brand Palette
        navy: {
          950: '#050811',
          900: '#0B0F1A',
          800: '#111827',
          700: '#1a2234',
          600: '#243047',
        },
        cyber: {
          cyan:    '#00F5FF',
          green:   '#00E676',
          amber:   '#FFB800',
          red:     '#FF3366',
          purple:  '#8B5CF6',
          blue:    '#3B82F6',
        },
        threat: {
          critical: '#FF3366',
          high:     '#FF6B35',
          medium:   '#FFB800',
          low:      '#3B82F6',
          info:     '#6B7280',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      backgroundImage: {
        'cyber-grid': "linear-gradient(rgba(0,245,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,245,255,0.03) 1px, transparent 1px)",
        'glow-cyan': 'radial-gradient(ellipse at center, rgba(0,245,255,0.15) 0%, transparent 70%)',
        'glow-red':  'radial-gradient(ellipse at center, rgba(255,51,102,0.15) 0%, transparent 70%)',
      },
      backgroundSize: {
        'grid': '40px 40px',
      },
      boxShadow: {
        'cyber':    '0 0 20px rgba(0,245,255,0.3)',
        'cyber-lg': '0 0 40px rgba(0,245,255,0.2)',
        'threat':   '0 0 20px rgba(255,51,102,0.3)',
        'glass':    '0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05)',
      },
      animation: {
        'pulse-slow':   'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow':         'glow 2s ease-in-out infinite alternate',
        'scan-line':    'scanLine 2s linear infinite',
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'fade-in':      'fadeIn 0.4s ease-out',
      },
      keyframes: {
        glow: {
          '0%':   { boxShadow: '0 0 5px rgba(0,245,255,0.5)' },
          '100%': { boxShadow: '0 0 20px rgba(0,245,255,0.9), 0 0 40px rgba(0,245,255,0.3)' },
        },
        scanLine: {
          '0%':   { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        slideInRight: {
          '0%':   { transform: 'translateX(100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        fadeIn: {
          '0%':   { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
