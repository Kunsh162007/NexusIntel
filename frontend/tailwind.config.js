/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: '#0d1117',
          card: '#161b22',
          elevated: '#21262d',
          border: '#30363d',
        },
        gtm: {
          DEFAULT: '#58a6ff',
          muted: '#1f3a5a',
        },
        finance: {
          DEFAULT: '#3fb950',
          muted: '#1a3d24',
        },
        security: {
          DEFAULT: '#f85149',
          muted: '#3d1f1e',
        },
        accent: '#58a6ff',
        text: {
          primary: '#e6edf3',
          secondary: '#8b949e',
          muted: '#6e7681',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'slide-in': 'slideIn 0.3s ease-out',
        'fade-in': 'fadeIn 0.4s ease-out',
      },
      keyframes: {
        slideIn: {
          '0%': { opacity: 0, transform: 'translateY(-8px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%': { opacity: 0 },
          '100%': { opacity: 1 },
        },
      },
    },
  },
  plugins: [],
}
