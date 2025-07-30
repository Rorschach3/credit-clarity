import { loadAllTradelinesFromDatabase, ParsedTradeline } from './tradelineParser';

// Cache for tradelines to avoid excessive database calls
let tradelinesCache: {
  userId: string;
  tradelines: ParsedTradeline[];
  timestamp: number;
} | null = null;

const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

export const getCachedTradelines = (userId: string): ParsedTradeline[] | null => {
  if (!tradelinesCache || tradelinesCache.userId !== userId) {
    return null;
  }
  
  const now = Date.now();
  if (now - tradelinesCache.timestamp > CACHE_DURATION) {
    tradelinesCache = null;
    return null;
  }
  
  return tradelinesCache.tradelines;
};

export const setCachedTradelines = (userId: string, tradelines: ParsedTradeline[]): void => {
  tradelinesCache = {
    userId,
    tradelines,
    timestamp: Date.now()
  };
};

export const clearTradelinesCache = (): void => {
  tradelinesCache = null;
};

export const syncTradelinesFromDatabase = async (userId: string): Promise<ParsedTradeline[]> => {
  try {
    // Check cache first
    const cached = getCachedTradelines(userId);
    if (cached) {
      console.log('[DEBUG] Using cached tradelines:', cached.length);
      return cached;
    }

    // Load from database
    console.log('[DEBUG] Loading tradelines from database for user:', userId);
    const tradelines = await loadAllTradelinesFromDatabase(userId);
    
    // Cache the result
    setCachedTradelines(userId, tradelines);
    
    console.log('[DEBUG] Synced tradelines from database:', tradelines.length);
    return tradelines;
  } catch (error) {
    console.error('[ERROR] Failed to sync tradelines:', error);
    return [];
  }
};

// Helper function to manually refresh tradelines and clear cache
export const refreshTradelinesSync = async (userId: string): Promise<ParsedTradeline[]> => {
  clearTradelinesCache();
  return await syncTradelinesFromDatabase(userId);
};