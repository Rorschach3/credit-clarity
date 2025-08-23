
import { useState, useEffect, createContext, useContext } from 'react';
import { supabase } from "@/integrations/supabase/client";
import { useUser, useAuth as useClerkAuth } from '@clerk/clerk-react';
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
  const { user: clerkUser, isLoaded: clerkLoaded } = useUser();
  const { getToken, signOut: clerkSignOut } = useClerkAuth();

  useEffect(() => {
    let mounted = true;

    const syncClerkToSupabase = async () => {
      if (!clerkLoaded) return;
      
      try {
        if (clerkUser) {
          console.log('🔄 Syncing Clerk user to Supabase...', clerkUser.id);
          
          // Get Clerk JWT token
          const clerkToken = await getToken();
          if (!clerkToken) {
            console.error('❌ Failed to get Clerk token');
            return;
          }
          
          // Try to get existing Supabase session first
          const { data: { session: existingSession } } = await supabase.auth.getSession();
          
          // If we already have a valid session, use it
          if (existingSession?.user) {
            console.log('✅ Using existing Supabase session');
            if (mounted) {
              setUser(existingSession.user);
              setIsLoading(false);
            }
            return;
          }
          
          // Create a synthetic Supabase user based on Clerk data
          const syntheticUser = {
            id: clerkUser.id,
            email: clerkUser.emailAddresses[0]?.emailAddress || '',
            user_metadata: {
              full_name: clerkUser.fullName,
              avatar_url: clerkUser.imageUrl,
              clerk_user_id: clerkUser.id
            },
            app_metadata: {},
            aud: 'authenticated',
            created_at: clerkUser.createdAt ? new Date(clerkUser.createdAt).toISOString() : new Date().toISOString(),
            updated_at: clerkUser.updatedAt ? new Date(clerkUser.updatedAt).toISOString() : new Date().toISOString(),
            email_confirmed_at: new Date().toISOString(),
            last_sign_in_at: new Date().toISOString(),
            role: 'authenticated'
          } as User;
          
          console.log('✅ Created synthetic Supabase user from Clerk data');
          
          if (mounted) {
            setUser(syntheticUser);
            setIsLoading(false);
          }
        } else {
          // No Clerk user, clear Supabase session
          console.log('🔄 No Clerk user, clearing auth state');
          if (mounted) {
            setUser(null);
            setIsLoading(false);
          }
        }
      } catch (error) {
        console.error("❌ Error syncing Clerk to Supabase:", error);
        if (mounted) {
          setUser(null);
          setIsLoading(false);
        }
      }
    };

    syncClerkToSupabase();

    return () => {
      mounted = false;
    };
  }, [clerkUser, clerkLoaded, getToken]);

  const login = async (email: string, password: string) => {
    // Redirect to Clerk sign-in instead
    console.log('🔄 Redirecting to Clerk sign-in...');
    window.location.href = '/login'; // This will show Clerk's sign-in UI
    return {};
  };

  const signup = async (email: string, password: string) => {
    // Redirect to Clerk sign-up instead
    console.log('🔄 Redirecting to Clerk sign-up...');
    window.location.href = '/signup'; // This will show Clerk's sign-up UI
    return {};
  };

  const logout = async () => {
    try {
      setIsLoading(true);
      // Use Clerk's signOut method
      await clerkSignOut();
      // Clear local state
      setUser(null);
      setIsLoading(false);
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
