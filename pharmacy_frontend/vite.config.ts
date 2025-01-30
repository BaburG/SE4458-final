import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/prescription': {
        target: 'http://prescription_service:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
