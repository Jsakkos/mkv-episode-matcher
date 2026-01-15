import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/scan': 'http://localhost:8001',
      '/match': 'http://localhost:8001',
      '/health': 'http://localhost:8001',
      '/system': 'http://localhost:8001',
      '/ws': {
        target: 'ws://localhost:8001',
        ws: true
      }
    }
  }
})
