// File: src/utils/tradelineParser.ts
import { supabase } from '@/integrations/supabase/client';
import { v4 as uuidv4 } from 'uuid';
import { z } from 'zod';

// Zod schemas for validation
export const APITradelineSchema = z.object({
  creditor_name: z.string().min(1, "Creditor name is required"),
  account_number: z.string().min(1, "Account number is required"),
  account_balance: z.string().default("$0"),
  account_status: z.string().min(1, "Account status is required"),
  account_type: z.string().min(1, "Account type is required"),
  date_opened: z.string().default(""),
  is_negative: z.boolean().default(false),
  dispute_count: z.number().int().min(0).default(0)
});

export const ParsedTradelineSchema = z.object({
  id: z.string().uuid("Invalid UUID format"),
  user_id: z.string().uuid("Invalid user ID format"),
  creditor_name: z.string().min(1, "Creditor name is required"),
  account_number: z.string().min(1, "Account number is required"),
  account_balance: z.string().default("$0"),
  account_status: z.string().min(1, "Account status is required"),
  account_type: z.string().min(1, "Account type is required"),
  date_opened: z.string().default(""),
  is_negative: z.boolean().default(false),
  dispute_count: z.number().int().min(0).default(0),
  created_at: z.string().datetime("Invalid datetime format"),
  credit_limit: z.string().default("$0"),
  credit_bureau: z.string().default("Unknown"),
  monthly_payment: z.string().default("$0"),
});

// TypeScript interfaces inferred from Zod schemas
export type APITradeline = z.infer<typeof APITradelineSchema>;
export type ParsedTradeline = z.infer<typeof ParsedTradelineSchema>;

// Negative account indicators
const NEGATIVE_INDICATORS = [
  'charged off', 'charge off', 'collection', 'collections',
  'late', 'delinquent', 'past due', 'default', 'bankruptcy',
  'foreclosure', 'repossession', 'settlement', 'closed', 
  '30-day late', '60-day late', '90-day late', '120-day late'
];

// Generate proper UUID
export const generateUUID = (): string => {
  return uuidv4();
};

// Get user profile ID from auth user ID
export const getUserProfileId = async (authUserId: string): Promise<string | null> => {
  try {
    console.log('[DEBUG] getUserProfileId called with:', authUserId, typeof authUserId);
    
    // Ensure we have a valid string ID
    if (!authUserId || typeof authUserId !== 'string') {
      console.error('[ERROR] Invalid authUserId provided:', authUserId);
      return null;
    }
    
    const { data: profile, error } = await supabase
      .from('profiles')
      .select('id')
      .eq('user_id', authUserId)
      .single();

    if (error) {
      console.error('[ERROR] Failed to get user profile ID:', error);
      return null;
    }

    return profile?.id || null;
  } catch (error) {
    console.error('[ERROR] Exception getting user profile ID:', error);
    return null;
  }
};

// Convert API tradeline to database format
export const convertAPITradelineToDatabase = (
  apiTradeline: APITradeline, 
  authUserId: string,
): ParsedTradeline => {
  // Determine if tradeline is negative
  const isNegative = apiTradeline.is_negative || 
    NEGATIVE_INDICATORS.some(indicator => 
      apiTradeline.account_status.toLowerCase().includes(indicator)
    );

  return {
  id: generateUUID(), // Generate proper UUID
  user_id: authUserId, // Use auth user ID
  creditor_name: apiTradeline.creditor_name || 'Unknown Creditor',
  account_number: apiTradeline.account_number || 'Unknown',
  account_balance: apiTradeline.account_balance || '$0',
  account_status: apiTradeline.account_status || 'Unknown',
  account_type: apiTradeline.account_type || 'Unknown',
  date_opened: apiTradeline.date_opened || '',
  is_negative: isNegative,
  dispute_count: apiTradeline.dispute_count || 0,
  created_at: new Date().toISOString(),
  credit_bureau: '',
  credit_limit: '',
  monthly_payment: ''
};
};

// Save tradelines to Supabase database
export const saveTradelinesToDatabase = async (tradelines: ParsedTradeline[], authUserId: string) => {
  try {
    console.log(`[DEBUG] 💾 Saving ${tradelines.length} tradelines to Supabase for user ${authUserId}`);
    
    // ✅ Use authUserId directly instead of getUserProfileId
    const userId = authUserId; // Don't call getUserProfileId
    
    console.log(`[DEBUG] 👤 Using auth user ID directly: ${userId}`);
    
    // No deletion - just upsert new tradelines (will update existing duplicates)
    const tradelinesForDB = tradelines.map(t => ({
      ...t,
      user_id: userId, // Use auth user ID
    }));

    // Log each tradeline being saved for debugging
    console.log(`[DEBUG] ➕ Upserting ${tradelinesForDB.length} tradelines (will overwrite duplicates)`);
    console.log(`[DEBUG] Tradelines to save:`, tradelinesForDB.map(t => ({
      creditor: t.creditor_name,
      account: t.account_number,
      user_id: t.user_id
    })));
    
    const { data, error: insertError } = await supabase
      .from('tradelines')
      .upsert(tradelinesForDB, { 
        onConflict: 'user_id,account_number,creditor_name',
        ignoreDuplicates: false 
      })
      .select();

    if (insertError) {
      console.error('[ERROR] ❌ Failed to save tradelines to Supabase:', insertError);
      throw insertError;
    }

    console.log(`[SUCCESS] ✅ Successfully saved ${data?.length || 0} tradelines`);
    return data;
    
  } catch (error) {
    console.error('[ERROR] ❌ Error in saveTradelinesToDatabase:', error);
    throw error;
  }
};

// Pagination options interface
export interface PaginationOptions {
  page?: number;
  pageSize?: number;
  sortBy?: 'created_at' | 'creditor_name' | 'account_balance';
  sortOrder?: 'asc' | 'desc';
}

// Paginated response interface
export interface PaginatedTradelinesResponse {
  data: ParsedTradeline[];
  pagination: {
    page: number;
    pageSize: number;
    totalCount: number;
    totalPages: number;
    hasNext: boolean;
    hasPrevious: boolean;
  };
}

// Load tradelines with pagination
export const loadTradelinesFromDatabase = async (
  authUserId: string,
  options: PaginationOptions = {}
): Promise<PaginatedTradelinesResponse> => {
  try {
    const userId = authUserId;
    const { 
      page = 1, 
      pageSize = 20, 
      sortBy = 'created_at', 
      sortOrder = 'desc' 
    } = options;

    console.log(`[DEBUG] 📖 Loading tradelines for profile: ${userId} (page ${page}, size ${pageSize})`);
    console.log(`[DEBUG] Options received:`, { page, pageSize, sortBy, sortOrder });

    // Calculate offset for pagination
    const offset = (page - 1) * pageSize;

    // Get total count first
    const { count, error: countError } = await supabase
      .from('tradelines')
      .select('*', { count: 'exact', head: true })
      .eq('user_id', userId);

    if (countError) {
      console.error('[ERROR] Failed to get tradelines count:', countError);
      throw countError;
    }

    const totalCount = count || 0;
    const totalPages = Math.ceil(totalCount / pageSize);

    // Load tradelines with pagination
    const { data: tradelines, error } = await supabase
      .from('tradelines')
      .select('*')
      .eq('user_id', userId)
      .order(sortBy, { ascending: sortOrder === 'asc' })
      .range(offset, offset + pageSize - 1);

    if (error) {
      console.error('[ERROR] Failed to load tradelines:', error);
      throw error;
    }

    console.log(`[SUCCESS] ✅ Loaded ${tradelines?.length || 0}/${totalCount} tradelines from database`);
    // [DEBUG] Log shape and values before returning
    console.log('[DEBUG] Returning from loadTradelinesFromDatabase:', {
      tradelinesType: Array.isArray(tradelines),
      tradelinesLength: tradelines?.length,
      page,
      pageSize,
      totalCount,
      totalPages,
      hasNext: page < totalPages,
      hasPrevious: page > 1,
      sampleTradeline: tradelines && tradelines.length > 0 ? tradelines[0] : null
    });
    // Sanitize all tradeline fields: map nulls to empty strings for strings, 0 for numbers, false for booleans
    const sanitizedTradelines = (tradelines || []).map(t => ({
      id: t.id ?? '',
      user_id: t.user_id ?? '',
      creditor_name: t.creditor_name ?? '',
      account_number: t.account_number ?? '',
      account_balance: t.account_balance ?? '',
      account_status: t.account_status ?? '',
      account_type: t.account_type ?? '',
      date_opened: t.date_opened ?? '',
      is_negative: t.is_negative ?? false,
      dispute_count: t.dispute_count ?? 0,
      created_at: t.created_at ?? '',
      credit_limit: t.credit_limit ?? '',
      credit_bureau: t.credit_bureau ?? '',
      monthly_payment: t.monthly_payment ?? '',
    }));

    return {
      data: sanitizedTradelines,
      pagination: {
        page,
        pageSize,
        totalCount,
        totalPages,
        hasNext: page < totalPages,
        hasPrevious: page > 1,
      }
    };

  } catch (error) {
    console.error('[ERROR] Error loading tradelines:', error);
    return {
      data: [],
      pagination: {
        page: 1,
        pageSize: 20,
        totalCount: 0,
        totalPages: 0,
        hasNext: false,
        hasPrevious: false,
      }
    };
  }
};

// Legacy function for backward compatibility
export const loadAllTradelinesFromDatabase = async (authUserId: string): Promise<ParsedTradeline[]> => {
  const response = await loadTradelinesFromDatabase(authUserId, { pageSize: 1000 });
  return response.data;
};

// Get negative tradelines only
export const getNegativeTradelines = (tradelines: ParsedTradeline[]): ParsedTradeline[] => {
  return tradelines.filter(t => 
    t.is_negative || 
    NEGATIVE_INDICATORS.some(indicator => 
      t.account_status.toLowerCase().includes(indicator)
    )
  );
};

// Validate tradeline data
export const validateTradeline = (tradeline: APITradeline): boolean => {
  const required = ['creditor_name', 'account_number', 'account_status'] as const;
  return required.every(field => tradeline[field]?.trim?.().length > 0);
};

// Validate API tradeline with Zod schema
export const validateAPITradeline = (
  tradeline: unknown // strict input
): { success: boolean; data?: APITradeline; error?: string } => {
  try {
    const validated = APITradelineSchema.parse(tradeline);
    return { success: true, data: validated };
  } catch (error) {
    if (error instanceof z.ZodError) {
      const errorMessage = error.errors.map(e => `${e.path.join('.')}: ${e.message}`).join(', ');
      return { success: false, error: errorMessage };
    }
    return { success: false, error: 'Unknown validation error' };
  }
};

// validate parsed tradeline with Zod schema
export const validateParsedTradeline = (
  tradeline: unknown
): { success: boolean; data?: ParsedTradeline; error?: string } => {
  try {
    const validated = ParsedTradelineSchema.parse(tradeline);
    return { success: true, data: validated };
  } catch (error) {
    if (error instanceof z.ZodError) {
      const errorMessage = error.errors.map(e => `${e.path.join('.')}: ${e.message}`).join(', ');
      return { success: false, error: errorMessage };
    }
    return { success: false, error: 'Unknown validation error' };
  }
};