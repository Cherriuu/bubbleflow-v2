import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Send API requests to Django in development, so the frontend and API share an origin like they do on Vercel
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        // Keep the browser's Host header so Django's CSRF origin check sees the same origin
        changeOrigin: false,
      },
    },
  },
})
