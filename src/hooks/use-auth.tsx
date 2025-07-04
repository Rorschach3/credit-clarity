
import { useState, useEffect, createContext, useContext } from 'react';
import { supabase } from "@/integrations/supabase/client";
import type { User } from '@supabase/supabase-js';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<{ error?: Error }>;
  signup: (email: string, password: string) => Promise<{ error?: Error }>;
  logout: () => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

// Public hook
export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
};

// Provider
export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    // Check for existing session
    const getUser = async () => {
      try {
        const { data: { session }, error } = await supabase.auth.getSession();

        if (error) {
          console.error("Error getting session:", error);
          if (mounted) {
            setUser(null);
            setIsLoading(false);
          }
          return;
        }

        if (mounted) {
          setUser(session ? session.user : null);
          setIsLoading(false);
        }
      } catch (error) {
        console.error("Unexpected error:", error);
        if (mounted) {
          setUser(null);
          setIsLoading(false);
        }
      }
    };

    // Set up auth state listener
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.log('Auth state changed:', event, session?.user?.id);
        
        if (mounted) {
          setUser(session?.user || null);
          setIsLoading(false);
        }
      }
    );

    getUser();

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, []);

  const login = async (email: string, password: string) => {
    try {
      setIsLoading(true);
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        setIsLoading(false);
        return { error: error as Error };
      }

      // Auth state listener will handle setting the user
      return {};
    } catch (error) {
      console.error("Login error:", error);
      setIsLoading(false);
      return { error: error as Error };
    }
  };

  const signup = async (email: string, password: string) => {
    try {
      setIsLoading(true);
      const { error } = await supabase.auth.signUp({
        email,
        password,
      });

      if (error) {
        setIsLoading(false);
        return { error: error as Error };
      }

      setIsLoading(false);
      return {};
    } catch (error) {
      console.error("Signup error:", error);
      setIsLoading(false);
      return { error: error as Error };
    }
  };

  const logout = async () => {
    try {
      setIsLoading(true);
      await supabase.auth.signOut();
      // Auth state listener will handle clearing the user
    } catch (error) {
      console.error("Logout error:", error);
      setIsLoading(false);
    }
  };

  // Alias for logout to maintain backward compatibility
  const signOut = logout;

  const value: AuthContextType = {
    user,
    isLoading,
    login,
    signup,
    logout,
    signOut,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
