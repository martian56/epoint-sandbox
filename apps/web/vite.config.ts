import { fileURLToPath } from 'node:url'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const API_TARGET = process.env.VITE_API_TARGET ?? 'http://localhost:8181'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    port: 5173,
    // Anchored patterns, otherwise /api-management is proxied as if it were /api.
    proxy: Object.fromEntries(
      ['^/api/', '^/_sandbox/', '^/checkout/', '^/docs$', '^/openapi.json$'].map((pattern) => [
        pattern,
        { target: API_TARGET, changeOrigin: true },
      ]),
    ),
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
  test: {
    environment: 'happy-dom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
  },
})
