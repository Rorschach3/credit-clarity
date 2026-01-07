import * as Sentry from "@sentry/react";

// Initialize Sentry as early as possible
Sentry.init({
  dsn: "https://85f44a3497d6408a4623779a142e1f50@o4510235564441600.ingest.us.sentry.io/4510616720769024",
  // Setting this option to true will send default PII data to Sentry.
  // For example, automatic IP address collection on events
  sendDefaultPii: true,
});

// Patch Date.prototype.toISOString to handle invalid dates gracefully
const originalToISOString = Date.prototype.toISOString;
Date.prototype.toISOString = function() {
  try {
    if (isNaN(this.getTime())) {
      console.error('Attempted to call toISOString on invalid date:', this);
      // Return current date as fallback
      return new Date().toISOString();
    }
    return originalToISOString.call(this);
  } catch (error) {
    console.error('Error in toISOString:', error);
    return new Date().toISOString();
  }
};

import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";
import "./styles/globals.css";
import { ThemeProvider } from "./components/theme-provider";
import { AuthProvider } from "./hooks/use-auth";
import { inject } from "@vercel/analytics";
import { HelmetProvider } from "react-helmet-async";

// Initialize Vercel Analytics once (not inside JSX)
inject({ mode: "auto" });

const container = document.getElementById("root");
if (!container) {
  throw new Error("Root element not found");
}

const root = createRoot(container);

root.render(
  <React.StrictMode>
    <HelmetProvider>
      <AuthProvider>
        <ThemeProvider defaultTheme="system" storageKey="vite-ui-theme">
          <App />
        </ThemeProvider>
      </AuthProvider>
    </HelmetProvider>
  </React.StrictMode>
);
