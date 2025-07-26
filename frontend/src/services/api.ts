import { supabase } from '@/integrations/supabase/client';
import type { Database } from '@/integrations/supabase/types';

// Type definitions
type Tradeline = Database["public"]["Tables"]["tradelines"]["Row"];
type Dispute = Database["public"]["Tables"]["disputes"]["Row"];
type UserProfile = Database["public"]["Tables"]["user_personal_info"]["Row"];

// Error handling wrapper
const withErrorHandling = async <T>(operation: () => Promise<T>): Promise<T> => {
  try {
    return await operation();
  } catch (error) {
    console.error('API Error:', error);
    throw error instanceof Error ? error : new Error('An unexpected error occurred');
  }
};

// Tradelines API
export const tradelinesApi = {
  // Fetch all tradelines for a user
  async getByUserId(userId: string): Promise<Tradeline[]> {
    return withErrorHandling(async () => {
      const { data, error } = await supabase
        .from("tradelines")
        .select("*")
        .eq("user_id", userId)
        .order("creditor_name", { ascending: true });

      if (error) throw error;
      return data || [];
    });
  },

  // Fetch negative tradelines only
  async getNegativeByUserId(userId: string): Promise<Tradeline[]> {
    return withErrorHandling(async () => {
      const { data, error } = await supabase
        .from("tradelines")
        .select("*")
        .eq("user_id", userId)
        .eq("is_negative", true)
        .order("creditor_name", { ascending: true });

      if (error) throw error;
      return data || [];
    });
  },

  // Fetch tradelines by bureau
  async getByUserIdAndBureau(userId: string, bureau: string): Promise<Tradeline[]> {
    return withErrorHandling(async () => {
      const { data, error } = await supabase
        .from("tradelines")
        .select("*")
        .eq("user_id", userId)
        .eq("credit_bureau", bureau)
        .order("creditor_name", { ascending: true });

      if (error) throw error;
      return data || [];
    });
  },

  // Update a tradeline
  async update(tradelineId: string, updates: Partial<Tradeline>): Promise<Tradeline> {
    return withErrorHandling(async () => {
      const { data, error } = await supabase
        .from("tradelines")
        .update(updates)
        .eq("id", tradelineId)
        .select()
        .single();

      if (error) throw error;
      return data;
    });
  },

  // Delete a tradeline
  async delete(tradelineId: string): Promise<void> {
    return withErrorHandling(async () => {
      const { error } = await supabase
        .from("tradelines")
        .delete()
        .eq("id", tradelineId);

      if (error) throw error;
    });
  },

  // Batch update tradelines
  async batchUpdate(updates: Array<{ id: string; updates: Partial<Tradeline> }>): Promise<Tradeline[]> {
    return withErrorHandling(async () => {
      const promises = updates.map(({ id, updates: updateData }) =>
        supabase
          .from("tradelines")
          .update(updateData)
          .eq("id", id)
          .select()
          .single()
      );

      const results = await Promise.all(promises);
      const errors = results.filter(result => result.error);
      
      if (errors.length > 0) {
        throw new Error(`Failed to update ${errors.length} tradelines`);
      }

      return results.map(result => result.data).filter(Boolean);
    });
  }
};

// Disputes API
export const disputesApi = {
  // Fetch all disputes for a user
  async getByUserId(userId: string): Promise<Dispute[]> {
    return withErrorHandling(async () => {
      const { data, error } = await supabase
        .from("disputes")
        .select("*")
        .eq("user_id", userId)
        .order("created_at", { ascending: false });

      if (error) throw error;
      return data || [];
    });
  },

  // Create a new dispute
  async create(dispute: Omit<Dispute, 'id' | 'created_at'>): Promise<Dispute> {
    return withErrorHandling(async () => {
      const { data, error } = await supabase
        .from("disputes")
        .insert(dispute)
        .select()
        .single();

      if (error) throw error;
      return data;
    });
  }
};

// User Profile API
export const profileApi = {
  // Fetch user profile
  async getByUserId(userId: string): Promise<UserProfile | null> {
    return withErrorHandling(async () => {
      const { data, error } = await supabase
        .from("user_personal_info")
        .select("*")
        .eq("user_id", userId)
        .maybeSingle();

      if (error) throw error;
      return data;
    });
  },

  // Update user profile
  async update(userId: string, updates: Partial<UserProfile>): Promise<UserProfile> {
    return withErrorHandling(async () => {
      const { data, error } = await supabase
        .from("user_personal_info")
        .upsert({ user_id: userId, ...updates })
        .select()
        .single();

      if (error) throw error;
      return data;
    });
  }
};

// Dashboard API - Batched queries for performance
export const dashboardApi = {
  // Fetch all dashboard data in one optimized call
  async getDashboardData(userId: string) {
    return withErrorHandling(async () => {
      // Execute all queries in parallel for maximum performance
      const [tradelinesResult, disputesResult, profileResult] = await Promise.allSettled([
        tradelinesApi.getByUserId(userId),
        disputesApi.getByUserId(userId),
        profileApi.getByUserId(userId)
      ]);

      // Handle results and extract data
      const tradelines = tradelinesResult.status === 'fulfilled' ? tradelinesResult.value : [];
      const disputes = disputesResult.status === 'fulfilled' ? disputesResult.value : [];
      const profile = profileResult.status === 'fulfilled' ? profileResult.value : null;

      // Log any errors but don't fail the entire request
      if (tradelinesResult.status === 'rejected') {
        console.error('Failed to fetch tradelines:', tradelinesResult.reason);
      }
      if (disputesResult.status === 'rejected') {
        console.error('Failed to fetch disputes:', disputesResult.reason);
      }
      if (profileResult.status === 'rejected') {
        console.error('Failed to fetch profile:', profileResult.reason);
      }

      return {
        tradelines,
        disputes,
        profile,
        // Computed metrics
        metrics: {
          totalTradelines: tradelines.length,
          negativeTradelines: tradelines.filter(t => t.is_negative).length,
          positiveTradelines: tradelines.filter(t => !t.is_negative).length,
          totalDisputes: disputes.length,
          activeDisputes: disputes.filter(d => d.status !== 'completed').length,
          resolvedDisputes: disputes.filter(d => d.status === 'completed').length,
        }
      };
    });
  }
};