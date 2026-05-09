import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port : 3000,
    proxy: {
      '/upload': 'http://localhost:8000',
      '/match':  'http://localhost:8000',
      '/status': 'http://localhost:8000',
      '/uploads':'http://localhost:8000'
    }
  }
})
