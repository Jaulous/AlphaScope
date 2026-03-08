import type { Config } from 'tailwindcss'
import animate from 'tailwindcss-animate'

const config: Config = {
  darkMode: ['class'],
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
    '../../packages/ui/src/**/*.{ts,tsx}'
  ],
  theme: {
    extend: {
      colors: {
        background: 'var(--background)',
        card: 'var(--card)',
        border: 'var(--border)',
        green: 'var(--accent-green)',
        red: 'var(--accent-red)'
      },
      boxShadow: {
        glass: '0 0 0 1px rgba(255, 255, 255, 0.08)'
      },
      backgroundImage: {
        vignette:
          'radial-gradient(circle at top, rgba(255,255,255,0.05), transparent 45%), radial-gradient(circle at bottom, rgba(34,197,94,0.05), transparent 35%)'
      }
    }
  },
  plugins: [animate]
}

export default config
