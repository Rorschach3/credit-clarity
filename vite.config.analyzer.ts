import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { visualizer } from 'rollup-plugin-visualizer';


export default defineConfig({
  plugins: [
    visualizer({ open: true, gzipSize: true, brotliSize: true }),
    react(),
    {
      name: 'bundle-analyzer',
      configResolved() {
        console.log('Bundle analyzer will run after build...');
      },
      writeBundle() {
        import('webpack-bundle-analyzer').then(({ BundleAnalyzerPlugin }) => {
          console.log('Use "npm run analyze" to analyze the bundle');
        });
      }
    }
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('react-router-dom')) return 'router';
            if (id.includes('@tanstack/react-query')) return 'tanstack';
            if (id.includes('@supabase/supabase-js')) return 'supabase';
            if (id.includes('recharts')) return 'charts';
            if (id.includes('jspdf') || id.includes('pdf-')) return 'pdf';
            if (id.includes('@google')) return 'ai';
            if (
              id.includes('clsx') ||
              id.includes('lucide-react') ||
              id.includes('date-fns') ||
              id.includes('framer-motion')
            )
              return 'utils';
            return 'vendor';
          }
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      '@tanstack/react-query',
      '@supabase/supabase-js',
      'recharts',
    ],
  },
});
