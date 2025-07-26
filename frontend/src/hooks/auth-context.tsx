import { createContext, useContext, ReactNode, useEffect } from 'react';
import { createClient } from '@/integrations/supabase/client';
import { useState } from 'react';

interface User {
  id: string;
  email: string;
  name?: string;
  dateOfBirth?: string;
  created_at: string;
}

type Session = {
  user?: {
    id: string;
    email: string;
    name?: string;
    dateOfBirth?: string;
    created_at: string;
  };
};

type UserContextType = {
  user: User | null;
  loading: boolean;
  signIn: () => Promise<void>;
  signOut: () => Promise<void>;
};

const UserContext = createContext<UserContextType>({} as UserContextType);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const supabase = createClient();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event: 'signed_in' | 'signed_out', session: Session) => {
        if (event === 'signed_in') {
          const { data: user } = supabase.auth.getUser(session?.user?.id);
          setUser(user?.user ?? null);
        } else if (event === 'signed_out') {
          setUser(null);
        }
      }
    );

    subscription?.unsubscribe();
    setLoading(false);
  }, []);

  const signIn = async () => {
    const { data: { error } } = await supabase.auth.signInWithRedirect();
    if (error) throw error;
  };

  const signOut = async () => {
    const { data: { error } } = await supabase.auth.signOut();
    if (error) throw error;
  };

  return (
    <UserContext.Provider value={{ user, loading, signIn, signOut }}>
      {children}
    </UserContext.Provider>
  );
};

export const useAuth = () => useContext(UserContext);