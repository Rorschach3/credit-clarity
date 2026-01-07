import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import sitemap from "vite-plugin-sitemap";
// import { visualizer } from "rollup-plugin-visualizer";


export default defineConfig(({ mode }) => {
  const isProduction = mode === "production";
  const isDevelopment = mode === "development";

  return {
    server: {
      host: "::",
      port: 8080,
      hmr: {
        port: 8080,
      },
      watch: {
        ignored: ['**/.venv/**', '**/node_modules/**', '**/dist/**'],
      },
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },
    plugins: [
      react(),
      // Sitemap generation for SEO
      sitemap({
        hostname: 'https://creditclarity.ai',
        dynamicRoutes: [
          '/',
          '/about',
          '/pricing',
          '/contact',
          '/faq',
          '/dashboard',
          '/credit-report-upload',
          '/tradelines',
          '/dispute-wizard',
          '/profile',
        ],
        changefreq: 'weekly',
        priority: 0.7,
        lastmod: new Date(),
      }),
      // Uncomment for bundle analysis: visualizer({ filename: "./dist/bundle-analysis.html", open: true, gzipSize: true, brotliSize: true })
    ],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    build: {
      sourcemap: isDevelopment ? true : 'hidden', // Hidden sourcemaps in production for security
      minify: isProduction ? 'esbuild' : false, // Use esbuild for faster minification
      target: "es2020", // Modern target for better optimization
      chunkSizeWarningLimit: 500, // Stricter chunk size limits
      cssCodeSplit: true, // CSS code splitting for better caching
      cssMinify: isProduction, // Minify CSS in production
    commonjsOptions: {
      include: [/pako/, /node_modules/],
      transformMixedEsModules: true,
    },
    rollupOptions: {
      external: (id) => {
        // Handle external dependencies that cause issues
        if (id.includes('node:')) return true;
        return false;
      },
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) return;

          // Separate framer-motion from router for better caching (as recommended)
          if (id.includes("react-router-dom")) return "router";
          if (id.includes("framer-motion")) return "animations";
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

          // Organize assets by type for better CDN caching
          if (/png|jpe?g|svg|gif|tiff|bmp|ico|webp/i.test(ext)) {
            return `img/[name]-[hash][extname]`;
          }
          if (/css/i.test(ext)) {
            return `css/[name]-[hash][extname]`;
          }
          if (/woff2?|ttf|otf|eot/i.test(ext)) {
            return `fonts/[name]-[hash][extname]`;
          }
          if (/json/i.test(ext)) {
            return `data/[name]-[hash][extname]`;
          }

          return `assets/[name]-[hash][extname]`;
        },

        // Optimize for HTTP/2 and modern browsers
        format: 'es',
        generatedCode: 'es2015',
      },

      // Tree shaking optimizations
      treeshake: {
        preset: 'recommended',
        manualPureFunctions: [
          'console.log',
          'console.info',
          'console.debug',
        ],
      },
    },
  },
  optimizeDeps: {
    include: [
      "react",
      "react-dom",
      "react-dom/client",
      "react-router-dom",
      "@tanstack/react-query",
      "@supabase/supabase-js",
      "lucide-react",
      "clsx",
      "tailwind-merge",
      "date-fns",
      "uuid",
      "pako", // Include pako for proper CommonJS to ES module conversion
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
    esbuildOptions: {
      target: 'es2020',
      format: 'esm',
      platform: 'browser',
      define: {
        global: 'globalThis',
      },
    },
  },

  // Environment variables
  define: {
    // Fix for pako default export issue
    global: 'globalThis',
    'process.env.NODE_ENV': JSON.stringify(mode),

    // Performance flags
    '__DEV__': JSON.stringify(isDevelopment),
    '__PROD__': JSON.stringify(isProduction),
  },

  // Performance-focused esbuild configuration
  esbuild: {
    target: 'es2020',
    logOverride: {
      'this-is-undefined-in-esm': 'silent',
    },
    // Production optimizations
    ...(isProduction && {
      drop: ['console', 'debugger'],
      minifyIdentifiers: true,
      minifySyntax: true,
      minifyWhitespace: true,
    }),
  },

  // Worker optimization
  worker: {
    format: 'es',
    rollupOptions: {
      output: {
        chunkFileNames: 'workers/[name]-[hash].js',
      },
    },
  },
};
});
