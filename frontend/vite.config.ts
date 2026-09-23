/// <reference types="vitest/config" />
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  envDir: '../',
  plugins: [react(), tailwindcss()],
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    env: {
      VITE_SUPERSET_URL: 'http://localhost:8088',
      VITE_GRAFANA_URL: 'http://localhost:3000',
    },
  },
  server: {
    proxy: {
      '/api/health': {
        target: `http://${process.env.API_HOST ?? 'urbangreen-api'}:${process.env.API_PORT ?? '8000'}`,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/api': {
        target: `http://${process.env.API_HOST ?? 'urbangreen-api'}:${process.env.API_PORT ?? '8000'}`,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api/v1'),
      },
    },
  },
})
