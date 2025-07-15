import { useState, useEffect, useCallback, useRef } from 'react';
import { 
  loadTradelinesFromDatabase, 
  PaginationOptions, 
  PaginatedTradelinesResponse,
  ParsedTradeline 
} from '@/utils/tradelineParser';

interface UsePaginatedTradelinesProps {
  userId: string;
  initialOptions?: PaginationOptions;
  autoLoad?: boolean;
}

interface UsePaginatedTradelinesReturn {
  tradelines: ParsedTradeline[];
  pagination: PaginatedTradelinesResponse['pagination'];
  loading: boolean;
  error: string | null;
  
  // Actions
  loadPage: (page: number) => Promise<void>;
  refresh: () => Promise<void>;
  setPageSize: (size: number) => void;
  setSorting: (sortBy: PaginationOptions['sortBy'], sortOrder: PaginationOptions['sortOrder']) => void;
  
  // Helpers
  goToNextPage: () => Promise<void>;
  goToPreviousPage: () => Promise<void>;
  goToFirstPage: () => Promise<void>;
  goToLastPage: () => Promise<void>;
}

export const usePaginatedTradelines = ({
  userId,
  initialOptions = {},
  autoLoad = true
}: UsePaginatedTradelinesProps): UsePaginatedTradelinesReturn => {
  const [tradelines, setTradelines] = useState<ParsedTradeline[]>([]);
  const [pagination, setPagination] = useState<PaginatedTradelinesResponse['pagination']>({
    page: 1,
    pageSize: 20,
    totalCount: 0,
    totalPages: 0,
    hasNext: false,
    hasPrevious: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [options, setOptions] = useState<Required<PaginationOptions>>({
    page: 1,
    pageSize: 20,
    sortBy: 'created_at',
    sortOrder: 'desc',
    ...initialOptions
  });
  const loadingRef = useRef(false);
  const hookIdRef = useRef(Math.random().toString(36).substr(2, 9));
  
  // Debug hook initialization
  console.log(`[DEBUG] usePaginatedTradelines hook initialized: ${hookIdRef.current} for user: ${userId}`);

  const loadTradelines = useCallback(async (loadOptions?: Partial<PaginationOptions>) => {
    console.log(`[DEBUG] loadTradelines called in hook ${hookIdRef.current} with options:`, loadOptions);
    
    if (!userId || loadingRef.current) {
      console.log(`[DEBUG] loadTradelines early return - userId: ${!!userId}, loading: ${loadingRef.current}`);
      return;
    }

    loadingRef.current = true;
    setLoading(true);
    setError(null);

    try {
      // Use functional state update to get current options without dependency
      let finalOptions: Required<PaginationOptions>;
      
      if (loadOptions) {
        setOptions(prev => {
          finalOptions = { ...prev, ...loadOptions };
          return finalOptions;
        });
      } else {
        setOptions(prev => {
          finalOptions = prev;
          return prev;
        });
      }
      
      const response = await loadTradelinesFromDatabase(userId, finalOptions!);
      
      setTradelines(response.data);
      setPagination(response.pagination);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load tradelines';
      setError(errorMessage);
      console.error('[ERROR] Failed to load paginated tradelines:', err);
    } finally {
      setLoading(false);
      loadingRef.current = false;
    }
  }, [userId]);

  const loadPage = useCallback(async (page: number) => {
    await loadTradelines({ page });
  }, [loadTradelines]);

  const refresh = useCallback(async () => {
    await loadTradelines();
  }, [loadTradelines]);

  const setPageSize = useCallback((pageSize: number) => {
    // Reset to first page when changing page size
    loadTradelines({ pageSize, page: 1 });
  }, [loadTradelines]);

  const setSorting = useCallback((
    sortBy: PaginationOptions['sortBy'], 
    sortOrder: PaginationOptions['sortOrder']
  ) => {
    // Reset to first page when changing sort
    loadTradelines({ sortBy, sortOrder, page: 1 });
  }, [loadTradelines]);

  const goToNextPage = useCallback(async () => {
    if (pagination.hasNext) {
      await loadPage(pagination.page + 1);
    }
  }, [pagination.hasNext, pagination.page, loadPage]);

  const goToPreviousPage = useCallback(async () => {
    if (pagination.hasPrevious) {
      await loadPage(pagination.page - 1);
    }
  }, [pagination.hasPrevious, pagination.page, loadPage]);

  const goToFirstPage = useCallback(async () => {
    if (pagination.page !== 1) {
      await loadPage(1);
    }
  }, [pagination.page, loadPage]);

  const goToLastPage = useCallback(async () => {
    if (pagination.page !== pagination.totalPages) {
      await loadPage(pagination.totalPages);
    }
  }, [pagination.page, pagination.totalPages, loadPage]);

  // Auto-load on mount and when userId changes
  useEffect(() => {
    if (autoLoad && userId) {
      loadTradelines();
    }
  }, [userId, autoLoad]); // Remove loadTradelines from dependencies

  return {
    tradelines,
    pagination,
    loading,
    error,
    
    loadPage,
    refresh,
    setPageSize,
    setSorting,
    
    goToNextPage,
    goToPreviousPage,
    goToFirstPage,
    goToLastPage,
  };
};