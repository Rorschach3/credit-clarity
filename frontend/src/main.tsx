<<<<<<< Updated upstream:src/main.tsx

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import * as pdfjsLib from 'pdfjs-dist'

pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.js',
  import.meta.url
).toString()


ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
=======
import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import './styles/globals.css';
import { ThemeProvider } from './components/theme-provider.tsx';
import { AuthProvider } from './hooks/use-auth.tsx';
import { Analytics } from "@vercel/analytics/next"

const container = document.getElementById('root');
if (!container) {
  throw new Error('Root element not found');
}

const root = createRoot(container);

root.render(
  <React.StrictMode>
    <AuthProvider>
      <ThemeProvider defaultTheme="system" storageKey="vite-ui-theme">
        <Analytics />
        <App />
      </ThemeProvider>
    </AuthProvider>
  </React.StrictMode>
);
>>>>>>> Stashed changes:frontend/src/main.tsx
