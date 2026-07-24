import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api/cloud': {
        target: 'http://localhost:8000', // Đảm bảo trỏ đúng port BE của bạn
        changeOrigin: true,
        secure: false,
      }
    }
  }
})