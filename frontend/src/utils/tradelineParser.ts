// File: src/utils/tradelineParser.ts
import { supabase } from '@/integrations/supabase/client';
import { v4 as uuidv4 } from 'uuid';
import { z } from 'zod';

// Zod schemas for validation - Updated to match backend normalized data
export const APITradelineSchema = z.object({
  creditor_name: z.string().min(1, "Creditor name is required"),
  account_number: z.string().default(""), // Allow empty strings - backend handles missing account numbers
  account_balance: z.string().default("$0"),
  account_status: z.string().default(""), // Allow empty strings - backend normalizes statuses
  account_type: z.string().min(1, "Account type is required"), // Still required
  date_opened: z.string().default(""), // Allow empty strings - backend handles date parsing
  credit_limit: z.string().default("$0"),
  credit_bureau: z.string().default(""), // Allow empty strings - backend detects bureau
  monthly_payment: z.string().default("$0"),
  is_negative: z.boolean().default(false),
  dispute_count: z.number().int().min(0).default(0)
});

export const ParsedTradelineSchema = z.object({
  id: z.string().uuid("Invalid UUID format"),
  user_id: z.string().uuid("Invalid user ID format"),
  creditor_name: z.string().min(1, "Creditor name is required"),
  account_number: z.string().default(""), // Allow empty strings - backend handles missing account numbers
  account_balance: z.string().default("$0"),
  account_status: z.string().default(""), // Allow empty strings - backend normalizes statuses  
  account_type: z.string().min(1, "Account type is required"), // Still required
  date_opened: z.string().default(""), // Allow empty strings - backend handles date parsing
  is_negative: z.boolean().default(false),
  dispute_count: z.number().int().min(0).default(0),
  created_at: z.string().datetime("Invalid datetime format"),
  credit_limit: z.string().default("$0"),
  credit_bureau: z.string().default(""), // Allow empty strings - backend detects bureau
  monthly_payment: z.string().default("$0"),
});

// TypeScript interfaces inferred from Zod schemas
export type APITradeline = z.infer<typeof APITradelineSchema>;
export type ParsedTradeline = z.infer<typeof ParsedTradelineSchema>;

// Type for raw Supabase tradeline data (with nullable fields)
interface DatabaseTradeline {
  id: string | null;
  user_id: string | null;
  creditor_name: string | null;
  account_number: string | null;
  account_balance: string | null;
  account_status: string | null;
  account_type: string | null;
  date_opened: string | null;
  is_negative: boolean | null;
  dispute_count: number | null;
  created_at: string | null;
  credit_limit: string | null;
  credit_bureau: string | null;
  monthly_payment: string | null;
}

// Interface for update operations
interface TradelineUpdate {
  id: string;
  updates: Partial<ParsedTradeline>;
}

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

// Sanitize Supabase data to match ParsedTradeline type
function sanitizeDatabaseTradeline(dbTradeline: DatabaseTradeline): ParsedTradeline {
  return {
    id: dbTradeline.id || '',
    user_id: dbTradeline.user_id || '',
    creditor_name: dbTradeline.creditor_name || '',
    account_number: dbTradeline.account_number || '',
    account_balance: dbTradeline.account_balance || '$0',
    account_status: dbTradeline.account_status || '',
    account_type: dbTradeline.account_type || '',
    date_opened: dbTradeline.date_opened || '',
    is_negative: dbTradeline.is_negative || false,
    dispute_count: dbTradeline.dispute_count || 0,
    created_at: dbTradeline.created_at || '',
    credit_limit: dbTradeline.credit_limit || '$0',
    credit_bureau: dbTradeline.credit_bureau || '',
    monthly_payment: dbTradeline.monthly_payment || '$0',
  };
}

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
    creditor_name: apiTradeline.creditor_name || '',
    account_number: apiTradeline.account_number || '',
    account_balance: apiTradeline.account_balance || '$0',
    account_status: apiTradeline.account_status || '',
    account_type: apiTradeline.account_type || '',
    date_opened: apiTradeline.date_opened || '',
    is_negative: isNegative,
    dispute_count: apiTradeline.dispute_count || 0,
    created_at: new Date().toISOString(),
    credit_bureau: '',
    credit_limit: '$0',
    monthly_payment: '$0'
  };
};

// Save tradelines to Supabase database with fuzzy matching for deduplication
export const saveTradelinesToDatabase = async (tradelines: ParsedTradeline[], authUserId: string): Promise<ParsedTradeline[]> => {
  try {
    console.log(`[DEBUG] 💾 Saving ${tradelines.length} tradelines to Supabase for user ${authUserId}`);
    
    const userId = authUserId;
    console.log(`[DEBUG] 👤 Using auth user ID directly: ${userId}`);
    
    // Import fuzzy matching functions
    const { 
      findExistingTradelineByFuzzyMatch, 
      mergeTradelineFields, 
      updateTradelineFields 
    } = await import('@/utils/fuzzyTradelineMatching');
    
    const newTradelines: ParsedTradeline[] = [];
    const updatedTradelines: TradelineUpdate[] = [];
    
    // Process each tradeline individually for fuzzy matching
    for (const tradeline of tradelines) {
      // Ensure we only include valid database fields with proper defaults
      const tradelineForDB: ParsedTradeline = {
        id: tradeline.id || generateUUID(),
        user_id: userId,
        creditor_name: tradeline.creditor_name || '',
        account_number: tradeline.account_number || '',
        account_balance: tradeline.account_balance || '$0',
        account_status: tradeline.account_status || '',
        account_type: tradeline.account_type || '',
        date_opened: tradeline.date_opened || '',
        is_negative: Boolean(tradeline.is_negative),
        dispute_count: tradeline.dispute_count || 0,
        created_at: tradeline.created_at || new Date().toISOString(),
        credit_limit: tradeline.credit_limit || '$0',
        credit_bureau: tradeline.credit_bureau || '',
        monthly_payment: tradeline.monthly_payment || '$0',
      };
      
      console.log(`[DEBUG] 🔍 Processing tradeline: ${tradeline.creditor_name} - ${tradeline.account_number}`);
      
      // Check for fuzzy matches
      const fuzzyMatch = await findExistingTradelineByFuzzyMatch(tradelineForDB, userId);
      
      if (fuzzyMatch && fuzzyMatch.isMatch && fuzzyMatch.existingTradeline) {
        // Found a match - merge only empty fields
        const updates = mergeTradelineFields(fuzzyMatch.existingTradeline, tradelineForDB);
        
        if (Object.keys(updates).length > 0) {
          updatedTradelines.push({
            id: fuzzyMatch.existingTradeline.id,
            updates
          });
          console.log(`[DEBUG] 🔄 Will update existing tradeline ${fuzzyMatch.existingTradeline.id} with ${Object.keys(updates).length} fields`);
        } else {
          console.log(`[DEBUG] ✅ Existing tradeline ${fuzzyMatch.existingTradeline.id} is already complete, no updates needed`);
        }
      } else {
        // No match found - add as new tradeline
        newTradelines.push(tradelineForDB);
        console.log(`[DEBUG] ➕ New tradeline: ${tradeline.creditor_name} inserted`);
      }
    }
    
    const results: ParsedTradeline[] = [];
    
    // Insert new tradelines (duplicates are already handled by fuzzy matching)
    if (newTradelines.length > 0) {
      console.log(`[DEBUG] ➕ Upserting ${newTradelines.length} new tradelines`);
      console.log('[DEBUG] 📋 Sample tradeline data being upserted:', JSON.stringify(newTradelines[0], null, 2));
      
      // Validate all tradelines before upsert
    // Validate all tradelines before upsert
    const validatedTradelines = newTradelines.map((tradeline) => {
      const validation = validateParsedTradeline(tradeline);
      if (!validation.success) {
        console.error('[ERROR] ❌ Tradeline validation failed:', validation.error);
        throw new Error(`Tradeline validation failed: ${validation.error}`);
      }
      return validation.data!;
    });

    // Remove duplicates within the current batch
    const uniqueTradelines = validatedTradelines.filter((tradeline, index, self) => {
      const key = `${tradeline.user_id}-${tradeline.account_number}-${tradeline.creditor_name}-${tradeline.credit_bureau}`;
      return index === self.findIndex(t => 
        `${t.user_id}-${t.account_number}-${t.creditor_name}-${t.credit_bureau}` === key
      );
    });

    console.log(`[DEBUG] Filtered ${validatedTradelines.length} down to ${uniqueTradelines.length} unique tradelines`);

    const { data: insertData, error: insertError } = await supabase
      .from('tradelines')
      .upsert(uniqueTradelines, { 
        onConflict: 'user_id,account_number,creditor_name,credit_bureau',
        ignoreDuplicates: false 
      })
      .select('*');

      if (insertError) {
        console.error('[ERROR] ❌ Failed to upsert new tradelines:', insertError);
        throw insertError;
      }
      
      if (insertData) {
        const sanitizedInserts = insertData.map(item => sanitizeDatabaseTradeline(item as DatabaseTradeline));
        results.push(...sanitizedInserts);
        console.log(`[SUCCESS] ✅ Successfully upserted ${insertData.length} tradelines`);
      }
    }
    
    // Update existing tradelines
    if (updatedTradelines.length > 0) {
      console.log(`[DEBUG] 🔄 Updating ${updatedTradelines.length} existing tradelines`);
      
      for (const { id, updates } of updatedTradelines) {
        const success = await updateTradelineFields(id, updates);
        if (!success) {
          console.warn(`[WARNING] ⚠️ Failed to update tradeline ${id}`);
        }
      }
      
      console.log(`[SUCCESS] ✅ Successfully processed ${updatedTradelines.length} tradeline updates`);
    }
    
    console.log(`[SUMMARY] 📊 Tradeline processing complete:`, {
      total: tradelines.length,
      newInserts: newTradelines.length,
      updates: updatedTradelines.length,
      totalProcessed: newTradelines.length + updatedTradelines.length
    });
    
    return results;
    
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
      pageSize = 50, 
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

    // Sanitize all tradeline fields using the sanitization function
    const sanitizedTradelines = (tradelines || []).map(t => sanitizeDatabaseTradeline(t as DatabaseTradeline));

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

// Validate tradeline data (legacy function - updated to match new requirements)
export const validateTradeline = (tradeline: APITradeline): boolean => {
  // Only require creditor_name and account_type - other fields can be empty
  const required = ['creditor_name', 'account_type'] as const;
  return required.every(field => {
    const value = tradeline[field];
    return typeof value === 'string' && value.trim().length > 0;
  });
};

// Validate API tradeline with Zod schema
export const validateAPITradeline = (
  tradeline: unknown
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

// Validate parsed tradeline with Zod schema
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