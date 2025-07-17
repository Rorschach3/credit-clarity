import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
// import { visualizer } from "rollup-plugin-visualizer";


export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8080,
    hmr: {
      port: 8080,
    },
    watch: {
      ignored: ['**/.venv/**'],
    },
  },
  plugins: [react()], // visualizer({ filename: "./dist/bundle-analysis.html", open: true, gzipSize: true, brotliSize: true })],
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
    rollupOptions: {
      output: {
        manualChunks(id) {
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
        chunkFileNames: (chunkInfo) => {
          const name = chunkInfo.facadeModuleId?.split("/").pop() ?? "chunk";
          return `js/[name]-[hash].js`;
        },
        entryFileNames: "js/[name]-[hash].js",
        assetFileNames: (assetInfo) => {
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
    include: [
      "react",
      "react-dom",
      "react-router-dom",
      "@tanstack/react-query",
      "@supabase/supabase-js",
      "lucide-react",
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
}));
