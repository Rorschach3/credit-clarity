import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

export default defineConfig(({ mode }) => ({
  server: {
    host: "::", // Your current setting (allows both IPv4 and IPv6)
    port: 8080,
    hmr: {
      port: 8080,
    },
    watch: {
      usePolling: true, // Essential for Docker file watching
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  optimizeDeps: {
    force: true, // Force re-optimization to fix cache issues
    include: [
      "react",
      'react/jsx-dev-runtime',
      "react-dom",
      "react-dom/client", // Added for completeness
      "react-router-dom",
      "@clerk/clerk-react",
      "@vercel/analytics/react"
    ]
  },
  build: {
    outDir: 'dist',
    sourcemap: mode === "development" ? true : true, // Always true now for consistency
    target: "esnext",
  }
}))