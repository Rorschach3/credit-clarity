// Supabase client configuration with JWKS support
import { createClient } from '@supabase/supabase-js';
import type { Database } from './types';

// Use environment variables for configuration
const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || "https://gywohmbqohytziwsjrps.supabase.co";
const SUPABASE_PUBLISHABLE_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd5d29obWJxb2h5dHppd3NqcnBzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU4NjYzNDQsImV4cCI6MjA2MTQ0MjM0NH0.F1Y8K6wmkqTInHvI1j9Pbog782i3VSVpIbgYqakyPwo";

// Import the supabase client like this:
// import { supabase } from "@/integrations/supabase/client";

export const supabase = createClient<Database>(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, {
  auth: {
    storage: localStorage,
    persistSession: true,
    autoRefreshToken: true,
    // JWKS configuration - Supabase handles this automatically
    detectSessionInUrl: true,
    flowType: 'pkce',
  },
  global: {
    headers: {
      'X-Client-Info': 'supabase-js-web',
    },
  },
});

// JWKS endpoint URL for external validation (if needed)
export const JWKS_URL = `${SUPABASE_URL}/auth/v1/.well-known/jwks.json`;

// Helper function to get JWT token from current session
export const getSessionToken = async (): Promise<string | null> => {
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token || null;
};

// Helper function to validate JWT token (for debugging)
export const validateToken = async (token: string): Promise<any> => {
  try {
    const response = await fetch(JWKS_URL);
    const jwks = await response.json();
    
    // In a real implementation, you would use a library like jose
    // to verify the token against the JWKS
    console.log('JWKS data:', jwks);
    console.log('Token to validate:', token);
    
    return { valid: true, jwks };
  } catch (error) {
    console.error('Token validation error:', error);
    return { valid: false, error };
  }
};