/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        base: '#0a0a0f',
        panel: '#111119',
        card: '#1a1a25',
        elevated: '#22222f',
        border: '#2a2a3a',
        'border-subtle': '#1f1f2e',
        'text-primary': '#e8e8f0',
        'text-secondary': '#9090a8',
        'text-muted': '#606075',
        accent: {
          blue: '#3b82f6',
          green: '#10b981',
          red: '#ef4444',
          amber: '#f59e0b',
          purple: '#8b5cf6',
          cyan: '#06b6d4',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        pulse: 'pulse 1.5s ease-in-out infinite',
        spin: 'spin 1s linear infinite',
        'blink-cursor': 'blink 1s step-end infinite',
      },
      keyframes: {
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
      },
    },
  },
  plugins: [],
}
