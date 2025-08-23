import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import type { ConfigEnv, UserConfig } from "vite";
// import { visualizer } from "rollup-plugin-visualizer";

export default defineConfig(({ mode }: ConfigEnv): UserConfig => ({
  server: {
    host: "0.0.0.0", // Keep your existing setting
    port: 3100, // Changed to match docker-compose port
    hmr: {
      port: 3100, // Match the port
    },
    watch: {
      ignored: ['**/.venv/**'],
      usePolling: true, // Keep this for Docker
    },
    proxy: {
      '/api': {
        target: 'http://backend:8000', // Use Docker service name instead of localhost
        changeOrigin: true,
        rewrite: (path: string) => path.replace(/^\/api/, ''),
      },
    },
  },
  plugins: [react()],
  // visualizer({ filename: "./dist/bundle-analysis.html", open: true, gzipSize: true, brotliSize: true })],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    sourcemap: mode === "development",
    minify: mode === "production",
    target: "esnext",
    chunkSizeWarningLimit: 1000,
    commonjsOptions: {
      include: [/pako/, /node_modules/],
      transformMixedEsModules: true,
    },
    rollupOptions: {
      external: (id: string) => {
        // Handle external dependencies that cause issues
        if (id.includes('node:')) return true;
        return false;
      },
      output: {
        manualChunks(id: string) {
          if (!id.includes("node_modules")) return;

          if (id.includes("react-router-dom")) return "router";
          if (id.includes("framer-motion")) return "router";
          if (id.includes("@tanstack/react-query")) return "tanstack";
          if (id.includes("@tanstack/react-query-devtools")) return "tanstack";
          if (id.includes("@supabase")) return "supabase";
          if (id.includes("@radix-ui")) return "radix";
          if (id.includes("recharts")) return "charts";
          if (id.includes("jspdf") || id.includes("pdf-lib")) return "pdf-core";
          if (id.includes("pdf-parse")) return "pdf-processing";
          if (id.includes("@google") || id.includes("@google-cloud")) return "ai-google";
          if (
            id.includes("react-hook-form") ||
            id.includes("@hookform/resolvers") ||
            id.includes("zod")
          )
            return "form-utils";
          if (id.includes("date-fns")) return "date-utils";
          if (
            id.includes("clsx") ||
            id.includes("tailwind-merge") ||
            id.includes("class-variance-authority")
          )
            return "ui-utils";
          if (id.includes("lucide-react") || id.includes("react-icons")) return "icons";
          if (
            id.includes("qrcode.react") ||
            id.includes("fuzzball") ||
            id.includes("uuid")
          )
            return "misc-utils";

          return "vendor";
        },
        chunkFileNames: (chunkInfo: any) => {
          const name = chunkInfo.name || 'chunk';
          return `js/${name}-[hash].js`;
        },
        entryFileNames: "js/[name]-[hash].js",
        assetFileNames: (assetInfo: any) => {
          const ext = assetInfo.name?.split(".").pop() ?? "";
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
            return `img/[name]-[hash][extname]`;
          }
          if (/css/i.test(ext)) {
            return `css/[name]-[hash][extname]`;
          }
          return `assets/[name]-[hash][extname]`;
        },
      },
    },
  },
  optimizeDeps: {
    force: true, // Added to fix cache issues
    include: [
      "react",
      "react/jsx-dev-runtime", // Added for Docker compatibility
      "react-dom",
      "react-dom/client", // Added for Docker compatibility
      "react-router-dom",
      "@tanstack/react-query",
      "@supabase/supabase-js",
      "lucide-react",
      "pako", // Include pako for proper CommonJS to ES module conversion
      "@clerk/clerk-react",
      "swr",
      "use-sync-external-store",
    ],
    exclude: [
      "@google-cloud/aiplatform",
      "@google-cloud/vertexai",
      "@google/genai",
      "@google/generative-ai",
      "pdf-parse",
      "jspdf",
      "pdf-lib",
    ],
  },
  define: {
    // Fix for pako default export issue
    global: 'globalThis',
  },
}));