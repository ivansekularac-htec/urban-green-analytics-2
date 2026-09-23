import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
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
