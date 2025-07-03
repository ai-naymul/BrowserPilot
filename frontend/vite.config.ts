import { defineConfig } from 'vite'

export default defineConfig({
  root: '.',
  publicDir: 'public',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    port: 3000,
    proxy: {
      '/job': 'http://localhost:8000',
      '/download': 'http://localhost:8000',
      '/streaming': 'http://localhost:8000',
      '/proxy': 'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
      '/stream': {
        target: 'ws://localhost:8000',
        ws: true,
      }
    }
  }
})
