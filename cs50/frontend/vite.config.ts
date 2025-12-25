import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => {
          // Preserve /api/v1 for versioned API endpoints
          if (path.startsWith('/api/v1')) {
            return path; // Forward /api/v1/* as-is to backend
          }
          // For non-versioned /api routes, remove /api prefix
          return path.replace(/^\/api/, '');
        }
      }
    }
  }
})
