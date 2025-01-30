import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/pharmacy/',
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    proxy: {
      '/prescription': {
        target: 'http://prescription_service:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
