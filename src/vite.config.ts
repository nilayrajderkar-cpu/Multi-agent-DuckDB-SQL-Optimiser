import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: process.env.NODE_ENV === 'production' ? '/Multi-agent-DuckDB-SQL-Optimiser/' : '/',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: undefined,
      },
    },
  },
  server: {
    port: 3000,
    host: true,
  },
  define: {
    'process.env.REACT_APP_API_URL': JSON.stringify(
      process.env.NODE_ENV === 'production' 
        ? '/api/optimize-sql'  // Vercel serverless function
        : 'http://localhost:8000'
    )
  }
})
