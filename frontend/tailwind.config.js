/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        bg: '#0b1220',
        panel: '#111a2e',
        'panel-border': '#1e293b',
        'text-main': '#e6edf7',
        'text-muted': '#94a3b8',
        accent: '#38bdf8',
        risk: {
          low: '#22c55e',
          moderate: '#eab308',
          high: '#f97316',
          severe: '#ef4444',
        },
        hazard: {
          manhole: '#f43f5e',
          drain: '#a855f7',
          pothole: '#facc15',
        }
      },
    },
  },
  plugins: [],
}
