import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const apiTarget = process.env.VITE_API_TARGET || 'http://localhost:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/benchmark': { target: apiTarget, changeOrigin: true },
      '/config': { target: apiTarget, changeOrigin: true },
      '/vision': { target: apiTarget, changeOrigin: true },
      '/models': { target: apiTarget, changeOrigin: true },
      '/health': { target: apiTarget, changeOrigin: true },
    },
  },
})
