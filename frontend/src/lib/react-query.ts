import { QueryClient } from '@tanstack/react-query';

// Configure React Query with optimized defaults
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Cache data for 5 minutes by default
      staleTime: 5 * 60 * 1000,
      // Keep data in cache for 10 minutes
      gcTime: 10 * 60 * 1000,
      // Retry failed requests 2 times
      retry: 2,
      // Don't refetch on window focus by default (can be overridden per query)
      refetchOnWindowFocus: false,
      // Enable background refetching
      refetchOnReconnect: true,
    },
    mutations: {
      // Retry failed mutations once
      retry: 1,
    },
  },
});

// Query keys factory for consistent key management
export const queryKeys = {
  // User-related queries
  user: (userId: string) => ['user', userId],
  profile: (userId: string) => ['profile', userId],
  
  // Tradelines queries
  tradelines: (userId: string) => ['tradelines', userId],
  negativeTradelines: (userId: string) => ['tradelines', userId, 'negative'],
  tradelinesByBureau: (userId: string, bureau?: string) => 
    bureau ? ['tradelines', userId, 'bureau', bureau] : ['tradelines', userId, 'bureau'],
  
  // Disputes queries
  disputes: (userId: string) => ['disputes', userId],
  disputePackets: (userId: string) => ['dispute-packets', userId],
  
  // Dashboard queries
  dashboard: (userId: string) => ['dashboard', userId],
  dashboardMetrics: (userId: string) => ['dashboard', userId, 'metrics'],
  
  // Credit reports
  creditReports: (userId: string) => ['credit-reports', userId],
} as const;

// Helper function to invalidate related queries
export const invalidateUserQueries = (userId: string) => {
  queryClient.invalidateQueries({ queryKey: ['user', userId] });
  queryClient.invalidateQueries({ queryKey: ['tradelines', userId] });
  queryClient.invalidateQueries({ queryKey: ['disputes', userId] });
  queryClient.invalidateQueries({ queryKey: ['dashboard', userId] });
};

// Background sync helper
export const prefetchUserData = async (userId: string) => {
  await Promise.allSettled([
    queryClient.prefetchQuery({
      queryKey: queryKeys.profile(userId),
      staleTime: 10 * 60 * 1000, // 10 minutes for profile data
    }),
    queryClient.prefetchQuery({
      queryKey: queryKeys.tradelines(userId),
      staleTime: 5 * 60 * 1000, // 5 minutes for tradelines
    }),
  ]);
};