/**
 * Modern TanStack Query hooks for credit data management
 * Provides optimistic updates, caching, and real-time synchronization
 */
import { useQuery, useMutation, useQueryClient, useInfiniteQuery } from '@tanstack/react-query';
import { useAuth } from '@/hooks/use-auth';
import { useRealtime } from '@/hooks/useRealtime';
import { useApiRetry } from '@/hooks/useRetry';
import { useErrorReporting } from '@/components/error/GlobalErrorHandler';
import { useMonitoring } from '@/hooks/useMonitoring';
import { toast } from 'sonner';
import { useEffect } from 'react';

// Types
export interface Tradeline {
  id: string;
  user_id: string;
  creditor_name: string;
  account_number: string;
  account_balance?: string;
  credit_limit?: string;
  monthly_payment?: string;
  date_opened?: string;
  account_type?: string;
  account_status?: string;
  credit_bureau?: string;
  is_negative?: boolean;
  dispute_count?: number;
  created_at: string;
  updated_at: string;
}

export interface JobStatus {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  message?: string;
  result?: any;
  error?: string;
  created_at: string;
  updated_at?: string;
  processing_time?: any;
}

export interface CreditScore {
  id: string;
  user_id: string;
  bureau: 'experian' | 'equifax' | 'transunion';
  score: number;
  date_recorded: string;
  factors?: string[];
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  pagination?: {
    page: number;
    limit: number;
    total: number;
    has_more: boolean;
  };
}

// Query Keys Factory
export const creditQueryKeys = {
  all: ['credit'] as const,
  tradelines: () => [...creditQueryKeys.all, 'tradelines'] as const,
  tradelinesInfinite: (filters?: any) => [...creditQueryKeys.tradelines(), 'infinite', filters] as const,
  tradelinesPaginated: (page: number, limit: number, filters?: any) => 
    [...creditQueryKeys.tradelines(), 'paginated', { page, limit, filters }] as const,
  tradeline: (id: string) => [...creditQueryKeys.tradelines(), id] as const,
  
  jobs: () => [...creditQueryKeys.all, 'jobs'] as const,
  job: (id: string) => [...creditQueryKeys.jobs(), id] as const,
  userJobs: (status?: string) => [...creditQueryKeys.jobs(), 'user', status] as const,
  
  scores: () => [...creditQueryKeys.all, 'scores'] as const,
  score: (bureau: string) => [...creditQueryKeys.scores(), bureau] as const,
  
  analytics: () => [...creditQueryKeys.all, 'analytics'] as const,
  summary: () => [...creditQueryKeys.analytics(), 'summary'] as const,
};

// API Client Factory
function createApiClient() {
  const baseUrl = import.meta.env.VITE_API_URL || 
    `${window.location.protocol}//${window.location.hostname}:8000`;

  return {
    get: async <T>(endpoint: string, token?: string): Promise<ApiResponse<T>> => {
      const response = await fetch(`${baseUrl}/api/v1${endpoint}`, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      return response.json();
    },

    post: async <T>(endpoint: string, data: any, token?: string): Promise<ApiResponse<T>> => {
      const response = await fetch(`${baseUrl}/api/v1${endpoint}`, {
        method: 'POST',
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      return response.json();
    },

    put: async <T>(endpoint: string, data: any, token?: string): Promise<ApiResponse<T>> => {
      const response = await fetch(`${baseUrl}/api/v1${endpoint}`, {
        method: 'PUT',
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      return response.json();
    },

    delete: async <T>(endpoint: string, token?: string): Promise<ApiResponse<T>> => {
      const response = await fetch(`${baseUrl}/api/v1${endpoint}`, {
        method: 'DELETE',
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      return response.json();
    },
  };
}

// Tradelines Queries
export function useTradelines(filters?: any) {
  const { getToken } = useAuth();
  const { lastEvent } = useRealtime();
  const queryClient = useQueryClient();
  const { executeWithRetry } = useApiRetry();
  const { reportAsyncError } = useErrorReporting();
  const { trackApiCall, trackEvent } = useMonitoring();

  const query = useQuery({
    queryKey: creditQueryKeys.tradelinesPaginated(1, 50, filters),
    queryFn: async () => {
      return reportAsyncError(async () => {
        return executeWithRetry(async () => {
          const startTime = Date.now();
          const token = await getToken();
          const api = createApiClient();
          
          const params = new URLSearchParams({
            page: '1',
            limit: '50',
            ...(filters && Object.fromEntries(
              Object.entries(filters).filter(([_, v]) => v !== undefined && v !== null)
            )),
          });

          const result = await api.get<Tradeline[]>(`/tradelines?${params}`, token);
          
          const duration = Date.now() - startTime;
          trackApiCall('/tradelines', 'GET', duration, 200);
          trackEvent('tradelines_loaded', {
            count: result.data?.length || 0,
            filters,
            duration
          });
          
          return result;
        });
      }, {
        component: 'useTradelines',
        action: 'fetch_tradelines',
        filters
      });
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (was cacheTime)
  });

  // Real-time updates
  useEffect(() => {
    if (lastEvent?.event_type === 'tradelines:updated') {
      queryClient.invalidateQueries({ queryKey: creditQueryKeys.tradelines() });
    }
  }, [lastEvent, queryClient]);

  return query;
}

export function useInfiniteTradelines(filters?: any) {
  const { getToken } = useAuth();
  const { lastEvent } = useRealtime();
  const queryClient = useQueryClient();

  const query = useInfiniteQuery({
    queryKey: creditQueryKeys.tradelinesInfinite(filters),
    queryFn: async ({ pageParam = 1 }) => {
      const token = await getToken();
      const api = createApiClient();
      
      const params = new URLSearchParams({
        page: pageParam.toString(),
        limit: '20',
        ...(filters && Object.fromEntries(
          Object.entries(filters).filter(([_, v]) => v !== undefined && v !== null)
        )),
      });

      return api.get<Tradeline[]>(`/tradelines?${params}`, token);
    },
    getNextPageParam: (lastPage) => {
      return lastPage.pagination?.has_more 
        ? (lastPage.pagination.page + 1) 
        : undefined;
    },
    initialPageParam: 1,
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  });

  // Real-time updates
  useEffect(() => {
    if (lastEvent?.event_type === 'tradelines:updated') {
      queryClient.invalidateQueries({ queryKey: creditQueryKeys.tradelinesInfinite(filters) });
    }
  }, [lastEvent, queryClient, filters]);

  return query;
}

export function useTradeline(id: string) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: creditQueryKeys.tradeline(id),
    queryFn: async () => {
      const token = await getToken();
      const api = createApiClient();
      return api.get<Tradeline>(`/tradelines/${id}`, token);
    },
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  });
}

// Job Status Queries
export function useJobStatus(jobId?: string) {
  const { getToken } = useAuth();
  const { lastEvent } = useRealtime();
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: creditQueryKeys.job(jobId || ''),
    queryFn: async () => {
      if (!jobId) throw new Error('Job ID required');
      
      const token = await getToken();
      const api = createApiClient();
      return api.get<JobStatus>(`/processing/job/${jobId}`, token);
    },
    enabled: !!jobId,
    refetchInterval: (data) => {
      // Stop polling if job is complete or if we have real-time updates
      const status = data?.data?.status;
      return status === 'running' || status === 'pending' ? 5000 : false;
    },
    staleTime: 1000, // 1 second for jobs
  });

  // Real-time updates for job progress
  useEffect(() => {
    if (lastEvent?.event_type === 'job:progress' && lastEvent.data.job_id === jobId) {
      queryClient.invalidateQueries({ queryKey: creditQueryKeys.job(jobId || '') });
    }
    if (lastEvent?.event_type === 'job:completed' && lastEvent.data.job_id === jobId) {
      queryClient.invalidateQueries({ queryKey: creditQueryKeys.job(jobId || '') });
      // Also invalidate tradelines since they might have been updated
      queryClient.invalidateQueries({ queryKey: creditQueryKeys.tradelines() });
    }
  }, [lastEvent, queryClient, jobId]);

  return query;
}

export function useUserJobs(status?: string) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: creditQueryKeys.userJobs(status),
    queryFn: async () => {
      const token = await getToken();
      const api = createApiClient();
      
      const params = new URLSearchParams({
        limit: '20',
        ...(status && { status_filter: status }),
      });

      return api.get<JobStatus[]>(`/processing/jobs?${params}`, token);
    },
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 30 * 1000, // Refresh every 30 seconds
  });
}

// Credit Score Queries
export function useCreditScores() {
  const { getToken } = useAuth();
  const { lastEvent } = useRealtime();
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: creditQueryKeys.scores(),
    queryFn: async () => {
      const token = await getToken();
      const api = createApiClient();
      return api.get<CreditScore[]>('/credit-scores', token);
    },
    staleTime: 15 * 60 * 1000, // 15 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
  });

  // Real-time updates for credit scores
  useEffect(() => {
    if (lastEvent?.event_type === 'credit:score_updated') {
      queryClient.invalidateQueries({ queryKey: creditQueryKeys.scores() });
      
      // Show toast notification
      const scoreData = lastEvent.data;
      const changeText = scoreData.change > 0 ? 'increased' : 'decreased';
      toast.info(`Credit score ${changeText}!`, {
        description: `${scoreData.bureau} score: ${scoreData.old_score} → ${scoreData.new_score}`,
      });
    }
  }, [lastEvent, queryClient]);

  return query;
}

// Mutations
export function useUpdateTradeline() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Tradeline> }) => {
      const token = await getToken();
      const api = createApiClient();
      return api.put<Tradeline>(`/tradelines/${id}`, data, token);
    },
    onMutate: async ({ id, data }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: creditQueryKeys.tradeline(id) });

      // Snapshot previous value
      const previousTradeline = queryClient.getQueryData(creditQueryKeys.tradeline(id));

      // Optimistically update
      queryClient.setQueryData(creditQueryKeys.tradeline(id), (old: any) => ({
        ...old,
        data: { ...old?.data, ...data },
      }));

      return { previousTradeline };
    },
    onError: (err, variables, context) => {
      // Rollback on error
      if (context?.previousTradeline) {
        queryClient.setQueryData(creditQueryKeys.tradeline(variables.id), context.previousTradeline);
      }
      toast.error('Failed to update tradeline');
    },
    onSuccess: () => {
      toast.success('Tradeline updated successfully');
    },
    onSettled: (data, error, variables) => {
      // Always refetch after mutation
      queryClient.invalidateQueries({ queryKey: creditQueryKeys.tradeline(variables.id) });
      queryClient.invalidateQueries({ queryKey: creditQueryKeys.tradelines() });
    },
  });
}

export function useDeleteTradeline() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const token = await getToken();
      const api = createApiClient();
      return api.delete(`/tradelines/${id}`, token);
    },
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: creditQueryKeys.tradelines() });

      // Remove from cache optimistically
      queryClient.setQueryData(creditQueryKeys.tradelines(), (old: any) => ({
        ...old,
        data: old?.data?.filter((t: Tradeline) => t.id !== id) || [],
      }));
    },
    onError: () => {
      toast.error('Failed to delete tradeline');
      // Refetch on error
      queryClient.invalidateQueries({ queryKey: creditQueryKeys.tradelines() });
    },
    onSuccess: () => {
      toast.success('Tradeline deleted successfully');
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: creditQueryKeys.tradelines() });
    },
  });
}

// Analytics and Summary
export function useCreditSummary() {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: creditQueryKeys.summary(),
    queryFn: async () => {
      const token = await getToken();
      const api = createApiClient();
      return api.get('/analytics/credit-summary', token);
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 20 * 60 * 1000, // 20 minutes
  });
}