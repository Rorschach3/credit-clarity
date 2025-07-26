import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/hooks/use-auth';
import { tradelinesApi } from '@/services/api';
import { queryKeys } from '@/lib/react-query';
import type { Database } from '@/integrations/supabase/types';

type Tradeline = Database["public"]["Tables"]["tradelines"]["Row"];

// Hook to fetch all tradelines for the current user
export const useTradelines = () => {
  const { user } = useAuth();
  
  return useQuery({
    queryKey: queryKeys.tradelines(user?.id || ''),
    queryFn: () => tradelinesApi.getByUserId(user!.id),
    enabled: !!user?.id,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  });
};

// Hook to fetch negative tradelines only
export const useNegativeTradelines = () => {
  const { user } = useAuth();
  
  return useQuery({
    queryKey: queryKeys.negativeTradelines(user?.id || ''),
    queryFn: () => tradelinesApi.getNegativeByUserId(user!.id),
    enabled: !!user?.id,
    staleTime: 3 * 60 * 1000, // 3 minutes for more critical data
  });
};

// Hook to fetch tradelines by bureau
export const useTradelinesByBureau = (bureau?: string) => {
  const { user } = useAuth();
  
  return useQuery({
    queryKey: queryKeys.tradelinesByBureau(user?.id || '', bureau),
    queryFn: () => bureau ? tradelinesApi.getByUserIdAndBureau(user!.id, bureau) : tradelinesApi.getByUserId(user!.id),
    enabled: !!user?.id,
    staleTime: 5 * 60 * 1000,
  });
};

// Hook to update a tradeline
export const useUpdateTradeline = () => {
  const queryClient = useQueryClient();
  const { user } = useAuth();

  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<Tradeline> }) =>
      tradelinesApi.update(id, updates),
    onSuccess: (updatedTradeline) => {
      if (!user?.id) return;

      // Update the tradelines cache with the new data
      queryClient.setQueryData(
        queryKeys.tradelines(user.id),
        (oldTradelines: Tradeline[] | undefined) => {
          if (!oldTradelines) return [updatedTradeline];
          return oldTradelines.map(tradeline => 
            tradeline.id === updatedTradeline.id ? updatedTradeline : tradeline
          );
        }
      );

      // Update negative tradelines cache if applicable
      if (updatedTradeline.is_negative) {
        queryClient.setQueryData(
          queryKeys.negativeTradelines(user.id),
          (oldTradelines: Tradeline[] | undefined) => {
            if (!oldTradelines) return [updatedTradeline];
            return oldTradelines.map(tradeline => 
              tradeline.id === updatedTradeline.id ? updatedTradeline : tradeline
            );
          }
        );
      } else {
        // Remove from negative tradelines if it's no longer negative
        queryClient.setQueryData(
          queryKeys.negativeTradelines(user.id),
          (oldTradelines: Tradeline[] | undefined) => {
            if (!oldTradelines) return [];
            return oldTradelines.filter(tradeline => tradeline.id !== updatedTradeline.id);
          }
        );
      }

      // Invalidate bureau-specific queries
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.tradelinesByBureau(user.id)
      });
    },
    onError: (error) => {
      console.error('Error updating tradeline:', error);
    },
  });
};

// Hook to delete a tradeline
export const useDeleteTradeline = () => {
  const queryClient = useQueryClient();
  const { user } = useAuth();

  return useMutation({
    mutationFn: (tradelineId: string) => tradelinesApi.delete(tradelineId),
    onSuccess: (_, deletedId) => {
      if (!user?.id) return;

      // Remove from all relevant caches
      const queriesToUpdate = [
        queryKeys.tradelines(user.id),
        queryKeys.negativeTradelines(user.id),
      ];

      queriesToUpdate.forEach(queryKey => {
        queryClient.setQueryData(
          queryKey,
          (oldTradelines: Tradeline[] | undefined) => {
            if (!oldTradelines) return [];
            return oldTradelines.filter(tradeline => tradeline.id !== deletedId);
          }
        );
      });

      // Invalidate bureau-specific queries
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.tradelinesByBureau(user.id)
      });

      // Invalidate dashboard data since metrics will change
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.dashboard(user.id)
      });
    },
    onError: (error) => {
      console.error('Error deleting tradeline:', error);
    },
  });
};

// Hook for batch operations
export const useBatchUpdateTradelines = () => {
  const queryClient = useQueryClient();
  const { user } = useAuth();

  return useMutation({
    mutationFn: (updates: Array<{ id: string; updates: Partial<Tradeline> }>) =>
      tradelinesApi.batchUpdate(updates),
    onSuccess: () => {
      if (!user?.id) return;

      // Invalidate all tradeline-related queries to refetch fresh data
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.tradelines(user.id)
      });
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.negativeTradelines(user.id)
      });
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.tradelinesByBureau(user.id)
      });
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.dashboard(user.id)
      });
    },
    onError: (error) => {
      console.error('Error batch updating tradelines:', error);
    },
  });
};

// Utility hook to get tradeline statistics
export const useTradelineStats = () => {
  const { data: tradelines, isLoading } = useTradelines();

  const stats = {
    total: tradelines?.length || 0,
    negative: tradelines?.filter(t => t.is_negative).length || 0,
    positive: tradelines?.filter(t => !t.is_negative).length || 0,
    byBureau: {
      Experian: tradelines?.filter(t => t.credit_bureau === 'Experian').length || 0,
      Equifax: tradelines?.filter(t => t.credit_bureau === 'Equifax').length || 0,
      TransUnion: tradelines?.filter(t => t.credit_bureau === 'TransUnion').length || 0,
    },
  };

  return { stats, isLoading };
};