import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/doctor/',
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://medicine_service:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/prescription': {
        target: 'http://prescription_service:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/prescription/, '')
      }
    }
  }
})
