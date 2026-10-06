import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    watch: {
      // En Docker Desktop (Windows/Mac) los eventos de filesystem del host
      // no llegan al contenedor; el polling garantiza hot-reload y la
      // detección de archivos nuevos (p. ej. features del menú lateral).
      usePolling: true,
      interval: 500,
    },
  },
})
