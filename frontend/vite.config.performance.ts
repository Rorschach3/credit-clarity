import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { visualizer } from "rollup-plugin-visualizer";
import { Plugin } from "vite";

// Performance-optimized Vite configuration
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
      react({
        // Enable React Fast Refresh optimizations
        jsxImportSource: '@emotion/react',
      }),
      
      // Bundle analyzer (only in production)
      isProduction && visualizer({
        filename: "./dist/bundle-analysis.html",
        open: false,
        gzipSize: true,
        brotliSize: true,
        template: 'treemap' // Use treemap for better visualization
      }),
      
      // Custom performance monitoring plugin
      {
        name: 'performance-monitor',
        buildStart() {
          if (isProduction) {
            console.log('🚀 Starting performance-optimized build...');
          }
        },
        generateBundle(options, bundle) {
          if (isProduction) {
            const chunks = Object.values(bundle).filter(chunk => chunk.type === 'chunk');
            const totalSize = chunks.reduce((sum, chunk) => sum + chunk.code.length, 0);
            console.log(`📊 Generated ${chunks.length} chunks, total size: ${(totalSize / 1024).toFixed(2)}KB`);
          }
        }
      } as Plugin
    ].filter(Boolean),
    
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
        // Performance aliases for common imports
        "react": path.resolve(__dirname, "node_modules/react"),
        "react-dom": path.resolve(__dirname, "node_modules/react-dom"),
      },
    },
    
    build: {
      sourcemap: isDevelopment ? true : 'hidden', // Hidden sourcemaps in production
      minify: isProduction ? 'esbuild' : false, // Use esbuild for faster minification
      target: 'es2020', // Modern target for better optimization
      chunkSizeWarningLimit: 500, // Stricter chunk size limits
      
      // CSS optimization
      cssCodeSplit: true,
      cssMinify: isProduction,
      
      // Advanced build optimizations
      commonjsOptions: {
        include: [/pako/, /node_modules/],
        transformMixedEsModules: true,
      },
      
      rollupOptions: {
        // Performance-focused external dependencies
        external: (id) => {
          if (id.includes('node:')) return true;
          return false;
        },
        
        output: {
          // Aggressive code splitting for optimal caching
          manualChunks: {
            // Core React chunks
            'react-core': ['react', 'react-dom'],
            'react-router': ['react-router-dom', 'framer-motion'],
            
            // State management and data fetching
            'react-query': ['@tanstack/react-query', '@tanstack/react-query-devtools'],
            
            // Backend integration
            'supabase': ['@supabase/supabase-js'],
            
            // UI framework chunks
            'radix-core': ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu', '@radix-ui/react-popover'],
            'radix-form': ['@radix-ui/react-form', '@radix-ui/react-checkbox', '@radix-ui/react-radio-group'],
            'radix-navigation': ['@radix-ui/react-navigation-menu', '@radix-ui/react-tabs'],
            
            // Charts and visualization
            'charts': ['recharts', 'victory'],
            
            // PDF processing (heavy libraries)
            'pdf-core': ['jspdf', 'pdf-lib'],
            'pdf-processing': ['pdf-parse'],
            
            // AI and ML libraries
            'ai-google': [
              '@google/generative-ai',
              '@google-cloud/aiplatform',
              '@google-cloud/vertexai'
            ],
            
            // Form handling
            'forms': [
              'react-hook-form',
              '@hookform/resolvers',
              'zod'
            ],
            
            // Utility libraries
            'date-utils': ['date-fns'],
            'crypto-utils': ['uuid', 'crypto-js'],
            'ui-utils': [
              'clsx',
              'tailwind-merge',
              'class-variance-authority'
            ],
            
            // Icon libraries
            'icons': ['lucide-react', 'react-icons'],
            
            // Miscellaneous utilities
            'utils': [
              'qrcode.react',
              'fuzzball',
              'lodash-es'
            ]
          },
          
          // Optimized file naming for better caching
          chunkFileNames: (chunkInfo) => {
            // Use content hash for better caching
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
    
    // Dependency pre-bundling optimization
    optimizeDeps: {
      // Include frequently used dependencies
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
      ],
      
      // Exclude heavy or problematic dependencies
      exclude: [
        "@google-cloud/aiplatform",
        "@google-cloud/vertexai",
        "@google/generative-ai",
        "pdf-parse",
        "jspdf",
        "pdf-lib",
        "crypto-js", // Use native crypto when possible
      ],
      
      // ESBuild options for dependency optimization
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
      // Fix for various library issues
      global: 'globalThis',
      'process.env.NODE_ENV': JSON.stringify(mode),
      
      // Performance flags
      '__DEV__': JSON.stringify(isDevelopment),
      '__PROD__': JSON.stringify(isProduction),
    },
    
    // CSS optimization
    css: {
      modules: {
        localsConvention: 'camelCase',
      },
      preprocessorOptions: {
        scss: {
          additionalData: `@import "@/styles/variables.scss";`,
        },
      },
      // PostCSS optimizations
      postcss: {
        plugins: isProduction ? [
          // Add autoprefixer and cssnano for production
        ] : [],
      },
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
    
    // Preview server configuration
    preview: {
      port: 3000,
      strictPort: true,
      headers: {
        // Security headers for preview
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
      },
    },
  };
});