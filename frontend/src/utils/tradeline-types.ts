// File: src/utils/tradelineParser.ts
import { supabase } from '@/integrations/supabase/client';
import { v4 as uuidv4 } from 'uuid';
import { z } from 'zod';
import type { Database } from '@/integrations/supabase/types';

// ==================== TYPE DEFINITIONS ====================

// API tradeline from backend
export interface APITradeline {
  creditor_name: string;
  account_number: string;
  account_balance: string;
  account_status: string;
  account_type: string;
  date_opened: string;
  credit_limit: string;
  credit_bureau: string;
  monthly_payment: string;
  is_negative?: boolean;
  dispute_count?: number;
}

// Parsed tradeline for frontend
export interface ParsedTradeline {
  id: string;
  user_id: string;
  creditor_name: string;
  account_number: string;
  account_balance: string;
  account_status: string;
  account_type: string;
  date_opened: string;
  is_negative: boolean;
  dispute_count: number;
  created_at: string;
  credit_limit: string;
  credit_bureau: string;
  monthly_payment: string;
}

// Update interface for tradeline modifications
export interface TradelineUpdate {
  id: string;
  updates: Partial<ParsedTradeline>;
}

// Pagination options
export interface PaginationOptions {
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

// Paginated response
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

// Zod schemas for validation
export const APITradelineSchema = z.object({
  creditor_name: z.string().min(1),
  account_number: z.string().min(1),
  account_balance: z.string().default('$0'),
  account_status: z.string().default(''),
  account_type: z.string().min(1),
  date_opened: z.string().nullable().default(''),
  credit_limit: z.string().default('$0'),
  credit_bureau: z.string().default(''),
  monthly_payment: z.string().default('$0'),
  is_negative: z.boolean().default(false),
  dispute_count: z.number().int().min(0).default(0)
});

export const ParsedTradelineSchema = z.object({
  id: z.string().min(1),
  user_id: z.string().min(1),
  creditor_name: z.string().min(1),
  account_number: z.string().min(1),
  account_balance: z.string().default('$0'),
  account_status: z.string().default(''),
  account_type: z.string().min(1),
  date_opened: z.string().default(''),
  is_negative: z.boolean().default(false),
  dispute_count: z.number().int().min(0).default(0),
  created_at: z.string().min(1),
  credit_limit: z.string().default('$0'),
  credit_bureau: z.string().default(''),
  monthly_payment: z.string().default('$0')
});

// ==================== DATABASE TYPE DEFINITIONS ====================

// Extract exact database types from your Supabase schema
export type DatabaseTradeline = Database['public']['Tables']['tradelines']['Row'];
export type InsertTradeline = Database['public']['Tables']['tradelines']['Insert'];
export type UpdateTradeline = Database['public']['Tables']['tradelines']['Update'];

// ==================== CONSTANTS ====================

// Negative account indicators
const NEGATIVE_INDICATORS = [
  'charged off', 'charge off', 'collection', 'collections',
  'late', 'delinquent', 'past due', 'default', 'bankruptcy',
  'foreclosure', 'repossession', 'settlement', 'closed', 
  '30-day late', '60-day late', '90-day late', '120-day late',
  // Add database enum values
  'in_collection', 'charged_off', 'disputed', 'collections'
];

// ==================== UTILITY FUNCTIONS ====================

// Generate proper UUID
export const generateUUID = (): string => {
  return uuidv4();
};

// Normalize date string to ISO format (YYYY-MM-DD) or null
export const normalizeDate = (dateStr: string | null | undefined): string | null => {
  if (!dateStr || dateStr.trim() === "") {
    return null; // Avoid empty string — send null
  }
  
  try {
    const trimmed = dateStr.trim();
    
    // Handle MM/DD/YYYY format
    const mmddyyyyMatch = trimmed.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
    if (mmddyyyyMatch) {
      const [, month, day, year] = mmddyyyyMatch;
      const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
      
      // Validate the date is valid (handles cases like 02/30/2023)
      if (date.getFullYear() === parseInt(year) && 
          date.getMonth() === parseInt(month) - 1 && 
          date.getDate() === parseInt(day)) {
        return date.toISOString().split('T')[0]; // Return YYYY-MM-DD
      }
    }
    
    // Try parsing as ISO date (YYYY-MM-DD)
    const isoMatch = trimmed.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
    if (isoMatch) {
      const date = new Date(trimmed);
      if (!isNaN(date.getTime())) {
        return date.toISOString().split('T')[0];
      }
    }
    
    // Try other common formats
    const date = new Date(trimmed);
    if (!isNaN(date.getTime())) {
      return date.toISOString().split('T')[0];
    }
    
    return null; // Invalid format fallback
  } catch (error) {
    console.warn(`[WARN] Invalid date format: "${dateStr}"`);
    return null; // Invalid format fallback
  }
};

// Sanitize Supabase data to match ParsedTradeline type
function sanitizeDatabaseTradeline(dbTradeline: DatabaseTradeline): ParsedTradeline {
  // Normalize date from database (in case it's in an unexpected format)
  const normalizedDate = normalizeDate(dbTradeline.date_opened);
  
  return {
    id: dbTradeline.id || '',
    user_id: dbTradeline.user_id || '',
    creditor_name: dbTradeline.creditor_name || '',
    account_number: dbTradeline.account_number || '',
    account_balance: dbTradeline.account_balance || '$0',
    account_status: dbTradeline.account_status || '',
    account_type: dbTradeline.account_type || '',
    date_opened: normalizedDate || '', // Use normalized date
    is_negative: dbTradeline.is_negative || false,
    dispute_count: dbTradeline.dispute_count || 0,
    created_at: dbTradeline.created_at || '',
    credit_limit: dbTradeline.credit_limit || '$0',
    credit_bureau: dbTradeline.credit_bureau || '',
    monthly_payment: dbTradeline.monthly_payment || '$0',
  };
}

// Convert ParsedTradeline to database insert format
function convertToInsertFormat(tradeline: ParsedTradeline): InsertTradeline {
  return {
    id: tradeline.id,
    user_id: tradeline.user_id,
    creditor_name: tradeline.creditor_name,
    account_number: tradeline.account_number,
    account_balance: tradeline.account_balance,
    account_status: tradeline.account_status,
    account_type: tradeline.account_type,
    date_opened: tradeline.date_opened || null,
    is_negative: tradeline.is_negative,
    dispute_count: tradeline.dispute_count,
    created_at: tradeline.created_at,
    credit_limit: tradeline.credit_limit,
    credit_bureau: tradeline.credit_bureau,
    monthly_payment: tradeline.monthly_payment,
  };
}

// ==================== CORE FUNCTIONS ====================

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

  // Normalize date_opened before storing
  const normalizedDate = normalizeDate(apiTradeline.date_opened);
  if (apiTradeline.date_opened && apiTradeline.date_opened !== normalizedDate) {
    console.log(`[DEBUG] 📅 Normalized date: "${apiTradeline.date_opened}" → "${normalizedDate}"`);
  }

  return {
    id: generateUUID(), // Generate proper UUID
    user_id: authUserId, // Use auth user ID
    creditor_name: apiTradeline.creditor_name || '',
    account_number: apiTradeline.account_number || '',
    account_balance: apiTradeline.account_balance || '$0',
    account_status: apiTradeline.account_status || '',
    account_type: apiTradeline.account_type || '',
    date_opened: normalizedDate || '', // Use normalized date or empty string
    is_negative: isNegative,
    dispute_count: apiTradeline.dispute_count || 0,
    created_at: new Date().toISOString(),
    credit_bureau: apiTradeline.credit_bureau || '',
    credit_limit: apiTradeline.credit_limit || '$0',
    monthly_payment: apiTradeline.monthly_payment || '$0'
  };
};

// Simple fuzzy matching function (enhanced to match your database)
const findExistingTradelineByFuzzyMatch = async (
  tradeline: ParsedTradeline, 
  userId: string
): Promise<{ isMatch: boolean; existingTradeline?: ParsedTradeline } | null> => {
  try {
    // Exact match on account number and creditor name
    const { data: exactMatches, error: exactError } = await supabase
      .from('tradelines')
      .select('*')
      .eq('user_id', userId)
      .eq('account_number', tradeline.account_number)
      .eq('creditor_name', tradeline.creditor_name);

    if (!exactError && exactMatches?.length) {
      return {
        isMatch: true,
        existingTradeline: sanitizeDatabaseTradeline(exactMatches[0])
      };
    }

    // Fuzzy match on creditor name (case insensitive, partial match)
    const { data: fuzzyMatches, error: fuzzyError } = await supabase
      .from('tradelines')
      .select('*')
      .eq('user_id', userId)
      .eq('account_number', tradeline.account_number)
      .ilike('creditor_name', `%${tradeline.creditor_name}%`);

    if (!fuzzyError && fuzzyMatches?.length) {
      return {
        isMatch: true,
        existingTradeline: sanitizeDatabaseTradeline(fuzzyMatches[0])
      };
    }

    return { isMatch: false };
  } catch (error) {
    console.error('[ERROR] Fuzzy match failed:', error);
    return { isMatch: false };
  }
};

// Merge tradeline fields (only update empty fields)
const mergeTradelineFields = (
  existing: ParsedTradeline, 
  incoming: ParsedTradeline
): Partial<ParsedTradeline> => {
  const updates: Partial<ParsedTradeline> = {};
  
  // Only update fields that are empty in existing tradeline
  const fieldsToCheck: (keyof ParsedTradeline)[] = [
    'account_balance', 'account_status', 'account_type', 'date_opened',
    'credit_limit', 'credit_bureau', 'monthly_payment'
  ];
  
  fieldsToCheck.forEach(field => {
    if ((!existing[field] || existing[field] === '' || existing[field] === '$0') && 
        incoming[field] && incoming[field] !== '' && incoming[field] !== '$0') {
      (updates as any)[field] = incoming[field];
    }
  });
  
  return updates;
};

// Update tradeline fields in database
const updateTradelineFields = async (
  id: string, 
  updates: Partial<ParsedTradeline>
): Promise<boolean> => {
  try {
    // Convert to database update format
    const dbUpdates: UpdateTradeline = {
      account_balance: updates.account_balance || undefined,
      account_status: updates.account_status || undefined,
      account_type: updates.account_type || undefined,
      date_opened: updates.date_opened || undefined,
      credit_limit: updates.credit_limit || undefined,
      credit_bureau: updates.credit_bureau || undefined,
      monthly_payment: updates.monthly_payment || undefined,
      is_negative: updates.is_negative !== undefined ? updates.is_negative : undefined,
      dispute_count: updates.dispute_count !== undefined ? updates.dispute_count : undefined,
    };

    const { error } = await supabase
      .from('tradelines')
      .update(dbUpdates)
      .eq('id', id);

    if (error) {
      console.error(`[ERROR] Failed to update tradeline ${id}:`, error);
      return false;
    }

    console.log(`[SUCCESS] Updated tradeline ${id} with:`, updates);
    return true;
  } catch (error) {
    console.error(`[ERROR] Exception updating tradeline ${id}:`, error);
    return false;
  }
};

// Save tradelines to Supabase database with fuzzy matching for deduplication
export const saveTradelinesToDatabase = async (
  tradelines: ParsedTradeline[], 
  authUserId: string
): Promise<ParsedTradeline[]> => {
  try {
    console.log(`[DEBUG] 💾 Saving ${tradelines.length} tradelines to Supabase for user ${authUserId}`);
    
    const userId = authUserId;
    console.log(`[DEBUG] 👤 Using auth user ID directly: ${userId}`);
    
    const newTradelines: ParsedTradeline[] = [];
    const updatedTradelines: TradelineUpdate[] = [];
    
    // Process each tradeline individually for fuzzy matching
    for (const tradeline of tradelines) {
      // Ensure we only include valid database fields with proper defaults
      const normalizedDate = normalizeDate(tradeline.date_opened);
      if (tradeline.date_opened && tradeline.date_opened !== normalizedDate) {
        console.log(`[DEBUG] 📅 Normalized date in processing: "${tradeline.date_opened}" → "${normalizedDate}"`);
      }
      
      const tradelineForDB: ParsedTradeline = {
        id: tradeline.id || generateUUID(),
        user_id: userId,
        creditor_name: tradeline.creditor_name || '',
        account_number: tradeline.account_number || '',
        account_balance: tradeline.account_balance || '$0',
        account_status: tradeline.account_status || '',
        account_type: tradeline.account_type || '',
        date_opened: normalizedDate || '', // Use normalized date
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
      
      // Filter out tradelines with missing required fields and validate the rest
      const validatedTradelines = newTradelines
        .filter((tradeline) => {
          // Skip tradelines without required fields
          if (!tradeline.creditor_name || tradeline.creditor_name.trim() === '') {
            console.warn(`[WARN] ⚠️ Skipping tradeline with missing creditor_name: ${JSON.stringify(tradeline)}`);
            return false;
          }
          // Skip tradelines without account numbers
          if (!tradeline.account_number || tradeline.account_number.trim() === '') {
            console.warn(`[WARN] ⚠️ Skipping tradeline with missing account_number: ${tradeline.creditor_name}`);
            return false;
          }
          return true;
        })
        .map((tradeline) => {
          const validation = validateParsedTradeline(tradeline);
          if (!validation.success) {
            console.error('[ERROR] ❌ Tradeline validation failed:', validation.error);
            throw new Error(`Tradeline validation failed: ${validation.error}`);
          }
          return validation.data!;
        });

      // Remove duplicates within the current batch
      const uniqueTradelines = validatedTradelines.filter((tradeline, index, self) => {
        const key = `${tradeline.user_id}-${tradeline.account_number}-${tradeline.creditor_name}-${tradeline.credit_bureau}-${tradeline.date_opened}`;
        return index === self.findIndex(t => 
          `${t.user_id}-${t.account_number}-${t.creditor_name}-${t.credit_bureau}-${t.date_opened}` === key
        );
      });

      console.log(`[DEBUG] Filtered ${newTradelines.length} tradelines → ${validatedTradelines.length} valid → ${uniqueTradelines.length} unique`);

      if (uniqueTradelines.length > 0) {
        // Convert to database insert format
        const dbInserts = uniqueTradelines.map(convertToInsertFormat);
        
        const { data: insertData, error: insertError } = await supabase
          .from('tradelines')
          .upsert(dbInserts, { 
            onConflict: 'user_id,account_number,creditor_name',
            ignoreDuplicates: false 
          })
          .select('*');

        if (insertError) {
          console.error('[ERROR] ❌ Failed to upsert new tradelines:', insertError);
          throw insertError;
        }
        
        if (insertData) {
          const sanitizedInserts = insertData.map(item => sanitizeDatabaseTradeline(item));
          results.push(...sanitizedInserts);
          console.log(`[SUCCESS] ✅ Successfully upserted ${insertData.length} tradelines`);
        }
      } else {
        console.log(`[INFO] ℹ️ No valid tradelines to insert after filtering`);
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

    // Sanitize all tradeline fields using the sanitization function
    const sanitizedTradelines = (tradelines || []).map(t => sanitizeDatabaseTradeline(t));

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

// ==================== VALIDATION FUNCTIONS ====================

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

// Re-export types for convenience
export type { APITradeline, ParsedTradeline, TradelineUpdate, PaginationOptions, PaginatedTradelinesResponse };