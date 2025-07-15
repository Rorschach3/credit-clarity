import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/hooks/use-auth';
import type { Database } from '@/integrations/supabase/types';

type Profile = Database['public']['Tables']['profiles']['Row'];

// Extended interface for dispute letter generation
export interface DisputeProfile {
  id: string;
  firstName: string;
  lastName: string;
  address1: string;
  address2?: string;
  city: string;
  state: string;
  zipCode: string;
  phoneNumber?: string;
  email?: string;
  dateOfBirth?: string;
  lastFourSSN?: string;
  fullAddress: string; // Computed field
}

interface UsePersistentProfileReturn {
  profile: Profile | null;
  disputeProfile: DisputeProfile | null;
  loading: boolean;
  error: string | null;
  refreshProfile: () => Promise<void>;
  updateProfile: (updates: Partial<Profile>) => Promise<void>;
  isProfileComplete: boolean;
  missingFields: string[];
}

// Cache for profile data to avoid excessive database calls
let profileCache: {
  userId: string;
  profile: Profile;
  timestamp: number;
} | null = null;

const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

const getCachedProfile = (userId: string): Profile | null => {
  if (!profileCache || profileCache.userId !== userId) {
    return null;
  }
  
  const now = Date.now();
  if (now - profileCache.timestamp > CACHE_DURATION) {
    profileCache = null;
    return null;
  }
  
  return profileCache.profile;
};

const setCachedProfile = (userId: string, profile: Profile): void => {
  profileCache = {
    userId,
    profile,
    timestamp: Date.now()
  };
};

const clearProfileCache = (): void => {
  profileCache = null;
};

export const usePersistentProfile = (): UsePersistentProfileReturn => {
  const { user } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshProfile = useCallback(async () => {
    if (!user?.id) {
      setProfile(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('[DEBUG] Refreshing profile from database for user:', user.id);
      
      // Check cache first
      const cached = getCachedProfile(user.id);
      if (cached) {
        console.log('[DEBUG] Using cached profile');
        setProfile(cached);
        setLoading(false);
        return;
      }

      // Load from database
      const { data, error: fetchError } = await supabase
        .from('profiles')
        .select('*')
        .eq('user_id', user.id)
        .single();

      if (fetchError) {
        if (fetchError.code === 'PGRST116') {
          // No profile found - this is okay, user hasn't created one yet
          console.log('[INFO] No profile found for user');
          setProfile(null);
        } else {
          throw fetchError;
        }
      } else if (data) {
        console.log('[SUCCESS] ✅ Profile loaded successfully');
        setProfile(data);
        setCachedProfile(user.id, data);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load profile';
      console.error('[ERROR] Failed to load profile:', err);
      setError(errorMessage);
      toast.error('Failed to load profile', {
        description: errorMessage
      });
    } finally {
      setLoading(false);
    }
  }, [user?.id]);

  const updateProfile = useCallback(async (updates: Partial<Profile>) => {
    if (!user?.id) {
      throw new Error('User not authenticated');
    }

    setLoading(true);
    setError(null);

    try {
      const { data, error: updateError } = await supabase
        .from('profiles')
        .upsert({
          user_id: user.id,
          ...updates,
          updated_at: new Date().toISOString()
        }, {
          onConflict: 'user_id'
        })
        .select()
        .single();

      if (updateError) throw updateError;

      if (data) {
        setProfile(data);
        setCachedProfile(user.id, data);
        toast.success('Profile updated successfully');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update profile';
      console.error('[ERROR] Failed to update profile:', err);
      setError(errorMessage);
      toast.error('Failed to update profile', {
        description: errorMessage
      });
      throw err;
    } finally {
      setLoading(false);
    }
  }, [user?.id]);

  // Load profile on mount and when user changes
  useEffect(() => {
    refreshProfile();
  }, [refreshProfile]);

  // Convert profile to dispute-ready format
  const disputeProfile: DisputeProfile | null = profile ? {
    id: profile.id,
    firstName: profile.first_name || '',
    lastName: profile.last_name || '',
    address1: profile.address1 || '',
    address2: profile.address2 || undefined,
    city: profile.city || '',
    state: profile.state || '',
    zipCode: profile.zip_code || '',
    phoneNumber: profile.phone_number || undefined,
    email: user?.email || undefined,
    dateOfBirth: profile.dob || undefined,
    lastFourSSN: profile.last_four_of_ssn || undefined,
    fullAddress: [
      profile.address1,
      profile.address2,
      `${profile.city}, ${profile.state} ${profile.zip_code}`
    ].filter(Boolean).join('\n')
  } : null;

  // Check if profile is complete for dispute letter generation
  const requiredFields = ['first_name', 'last_name', 'address1', 'city', 'state', 'zip_code'];
  const missingFields = requiredFields.filter(field => !profile?.[field as keyof Profile]);
  const isProfileComplete = missingFields.length === 0;

  return {
    profile,
    disputeProfile,
    loading,
    error,
    refreshProfile,
    updateProfile,
    isProfileComplete,
    missingFields
  };
};

export { clearProfileCache };