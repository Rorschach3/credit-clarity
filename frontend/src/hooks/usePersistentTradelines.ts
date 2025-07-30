import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { ParsedTradeline } from '@/utils/tradelineParser';
import { syncTradelinesFromDatabase, refreshTradelinesSync, clearTradelinesCache } from '@/utils/tradelineSync';
import { useAuth } from '@/hooks/use-auth';

interface UsePersistentTradelinesReturn {
  tradelines: ParsedTradeline[];
  setTradelines: (tradelines: ParsedTradeline[]) => void;
  loading: boolean;
  error: string | null;
  refreshTradelines: () => Promise<void>;
  addTradelines: (newTradelines: ParsedTradeline[]) => void;
  updateTradeline: (id: string, updates: Partial<ParsedTradeline>) => void;
  deleteTradeline: (id: string) => void;
  getTradelineById: (id: string) => ParsedTradeline | undefined;
  getTradelinesByStatus: (status: string) => ParsedTradeline[];
  getNegativeTradelines: () => ParsedTradeline[];
  getPositiveTradelines: () => ParsedTradeline[];
}

export const usePersistentTradelines = (): UsePersistentTradelinesReturn => {
  const { user } = useAuth();
  const [tradelines, setTradelines] = useState<ParsedTradeline[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshTradelines = useCallback(async () => {
    if (!user?.id) {
      setTradelines([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('[DEBUG] Refreshing tradelines from database for user:', user.id);
      const loadedTradelines = await syncTradelinesFromDatabase(user.id);
      console.log('[DEBUG] Loaded tradelines:', loadedTradelines.length);
      
      setTradelines(loadedTradelines);
      
      if (loadedTradelines.length > 0) {
        console.log('[SUCCESS] ✅ Tradelines loaded successfully');
      } else {
        console.log('[INFO] No tradelines found in database');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load tradelines';
      console.error('[ERROR] Failed to load tradelines:', err);
      setError(errorMessage);
      toast.error('Failed to load tradelines', {
        description: errorMessage
      });
    } finally {
      setLoading(false);
    }
  }, [user?.id]);

  // Manual refresh function that bypasses cache
  const forceRefreshTradelines = useCallback(async () => {
    if (!user?.id) {
      setTradelines([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('[DEBUG] Force refreshing tradelines (bypassing cache) for user:', user.id);
      const loadedTradelines = await refreshTradelinesSync(user.id);
      console.log('[DEBUG] Force loaded tradelines:', loadedTradelines.length);
      
      setTradelines(loadedTradelines);
      
      toast.success('Tradelines refreshed from database', {
        description: `${loadedTradelines.length} tradeline(s) loaded`
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to refresh tradelines';
      console.error('[ERROR] Failed to force refresh tradelines:', err);
      setError(errorMessage);
      toast.error('Failed to refresh tradelines', {
        description: errorMessage
      });
    } finally {
      setLoading(false);
    }
  }, [user?.id]);

  // Load tradelines on mount and when user changes
  useEffect(() => {
    refreshTradelines();
  }, [refreshTradelines]);

  const addTradelines = useCallback((newTradelines: ParsedTradeline[]) => {
    setTradelines(prev => {
      // Avoid duplicates by checking ID
      const existingIds = new Set(prev.map(t => t.id));
      const uniqueNewTradelines = newTradelines.filter(t => !existingIds.has(t.id));
      
      console.log('[DEBUG] Adding tradelines - existing:', prev.length, 'new:', uniqueNewTradelines.length);
      
      // Clear cache when adding new tradelines to ensure fresh data
      if (uniqueNewTradelines.length > 0) {
        clearTradelinesCache();
      }
      
      return [...prev, ...uniqueNewTradelines];
    });
  }, []);

  const updateTradeline = useCallback((id: string, updates: Partial<ParsedTradeline>) => {
    setTradelines(prev => 
      prev.map(tradeline => 
        tradeline.id === id 
          ? { ...tradeline, ...updates }
          : tradeline
      )
    );
  }, []);

  const deleteTradeline = useCallback((id: string) => {
    setTradelines(prev => prev.filter(tradeline => tradeline.id !== id));
  }, []);

  const getTradelineById = useCallback((id: string): ParsedTradeline | undefined => {
    return tradelines.find(t => t.id === id);
  }, [tradelines]);

  const getTradelinesByStatus = useCallback((status: string): ParsedTradeline[] => {
    return tradelines.filter(t => t.account_status?.toLowerCase() === status.toLowerCase());
  }, [tradelines]);

  const getNegativeTradelines = useCallback((): ParsedTradeline[] => {
    const negativeIndicators = [
      'charged off', 'charge off', 'collection', 'collections',
      'late', 'delinquent', 'past due', 'default', 'bankruptcy',
      'foreclosure', 'repossession', 'settlement', 'closed'
    ];

    return tradelines.filter(t => 
      t.is_negative || 
      negativeIndicators.some(indicator => 
        t.account_status?.toLowerCase().includes(indicator.toLowerCase())
      )
    );
  }, [tradelines]);

  const getPositiveTradelines = useCallback((): ParsedTradeline[] => {
    const negativeTradelines = getNegativeTradelines();
    const negativeIds = new Set(negativeTradelines.map(t => t.id));
    return tradelines.filter(t => !negativeIds.has(t.id));
  }, [tradelines, getNegativeTradelines]);

  return {
    tradelines,
    setTradelines,
    loading,
    error,
    refreshTradelines: forceRefreshTradelines, // Use force refresh for manual triggers
    addTradelines,
    updateTradeline,
    deleteTradeline,
    getTradelineById,
    getTradelinesByStatus,
    getNegativeTradelines,
    getPositiveTradelines,
  };
};