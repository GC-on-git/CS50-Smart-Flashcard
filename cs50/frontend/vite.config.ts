import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  // Centralize env files at repo root (so frontend reads from <repo>/.env)
  envDir: path.resolve(__dirname, '../..'),
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          http: ['axios'],
        },
      },
    },
  },
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
