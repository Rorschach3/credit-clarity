// Enhanced tradelineParser.ts with improved data handling
import { supabase } from '@/integrations/supabase/client';
import { v4 as uuidv4 } from 'uuid';
import { z } from 'zod';

// Enhanced Zod schemas that match backend normalized data
export const APITradelineSchema = z.object({
  creditor_name: z.string().min(1, "Creditor name is required"),
  account_number: z.string().nullable().transform(val => val === "" ? null : val),
  account_balance: z.string().nullable().transform(val => val === "" ? null : val),
  account_status: z.enum(['Current', 'Closed', 'Late', 'Collection']).or(z.string()).nullable(),
  account_type: z.enum(['Revolving', 'Installment']).or(z.string()),
  date_opened: z.string().nullable().transform(val => val === "" ? null : val),
  credit_limit: z.string().nullable().transform(val => val === "" ? null : val),
  credit_bureau: z.enum(['Experian', 'Equifax', 'TransUnion']).nullable(),
  monthly_payment: z.string().nullable().transform(val => val === "" ? null : val),
  is_negative: z.boolean().default(false),
  dispute_count: z.number().int().min(0).default(0)
});

export const ParsedTradelineSchema = z.object({
  id: z.string().uuid("Invalid UUID format"),
  user_id: z.string().uuid("Invalid user ID format"),
  creditor_name: z.string().min(1, "Creditor name is required"),
  account_number: z.string().nullable(),
  account_balance: z.string().nullable(),
  account_status: z.string().nullable(),
  account_type: z.string().min(1, "Account type is required"),
  date_opened: z.string().nullable(),
  is_negative: z.boolean().default(false),
  dispute_count: z.number().int().min(0).default(0),
  created_at: z.string().datetime("Invalid datetime format"),
  credit_limit: z.string().nullable(),
  credit_bureau: z.string().nullable(),
  monthly_payment: z.string().nullable(),
});

// Enhanced type definitions
export type APITradeline = z.infer<typeof APITradelineSchema>;
export type ParsedTradeline = z.infer<typeof ParsedTradelineSchema>;

// Enhanced database tradeline interface matching backend structure
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
  updated_at?: string | null;
}

// Data normalization utility class
class TradelineNormalizer {
  private accountTypeMapping = {
    'Credit Card': 'Revolving',
    'Store Card': 'Revolving',
    'Line of Credit': 'Revolving',
    'Auto Loan': 'Installment',
    'Student Loan': 'Installment',
    'Personal Loan': 'Installment',
    'Mortgage': 'Installment',
    'Installment Loan': 'Installment',
  };

  private accountStatusMapping = {
    'Current Account': 'Current',
    'Paid, Closed; was Paid as agreed': 'Closed',
    'Account Closed': 'Closed',
    'Paid as agreed': 'Current',
    'Open': 'Current',
  };

  normalizeAccountType(type: string): string {
    if (!type) return 'Revolving'; // Default
    
    const normalized = this.accountTypeMapping[type as keyof typeof this.accountTypeMapping];
    if (normalized) return normalized;
    
    // Fallback logic
    const typeLower = type.toLowerCase();
    if (typeLower.includes('revolving') || typeLower.includes('card')) {
      return 'Revolving';
    }
    if (typeLower.includes('installment') || typeLower.includes('loan')) {
      return 'Installment';
    }
    
    return 'Revolving'; // Default
  }

  normalizeAccountStatus(status: string): string {
    if (!status) return 'Current'; // Default
    
    const normalized = this.accountStatusMapping[status as keyof typeof this.accountStatusMapping];
    if (normalized) return normalized;
    
    // Fallback logic
    const statusLower = status.toLowerCase();
    if (statusLower.includes('current') || statusLower.includes('good')) {
      return 'Current';
    }
    if (statusLower.includes('closed') || statusLower.includes('paid')) {
      return 'Closed';
    }
    if (statusLower.includes('late') || statusLower.includes('delinquent')) {
      return 'Late';
    }
    if (statusLower.includes('collection') || statusLower.includes('charge')) {
      return 'Collection';
    }
    
    return 'Current'; // Default
  }

  normalizeCurrency(value: string | null): string | null {
    if (!value || value.trim() === '') return null;
    
    // Handle malformed values
    if (value === '$,' || value === '$') return null;
    
    // Extract numeric value
    const numericMatch = value.match(/[\d,]+\.?\d*/);
    if (!numericMatch) return null;
    
    try {
      const numericStr = numericMatch[0].replace(/,/g, '');
      const amount = parseFloat(numericStr);
      
      if (isNaN(amount)) return null;
      if (amount === 0) return '$0';
      
      return `$${amount.toLocaleString()}`;
    } catch {
      return null;
    }
  }

  normalizeDate(date: string | null): string | null {
    if (!date || date.trim() === '') return null;
    
    // Handle malformed dates
    if (date.includes('xxxx') || date.includes("'\"")) return null;
    
    // Try to parse various date formats
    const datePatterns = [
      /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/,  // MM/DD/YYYY
      /^(\d{1,2})-(\d{1,2})-(\d{4})$/,   // MM-DD-YYYY
      /^(\d{4})-(\d{1,2})-(\d{1,2})$/,   // YYYY-MM-DD
    ];

    for (const pattern of datePatterns) {
      const match = date.match(pattern);
      if (match) {
        try {
          let month: number, day: number, year: number;
          
          if (pattern.source.startsWith('^(\\d{4})')) {
            // YYYY-MM-DD format
            [, year, month, day] = match.map(Number);
          } else {
            // MM/DD/YYYY or MM-DD-YYYY format
            [, month, day, year] = match.map(Number);
          }
          
          // Validate ranges
          if (month >= 1 && month <= 12 && 
              day >= 1 && day <= 31 && 
              year >= 1950 && year <= new Date().getFullYear()) {
            return `${month.toString().padStart(2, '0')}/${day.toString().padStart(2, '0')}/${year}`;
          }
        } catch {
          continue;
        }
      }
    }
    
    return null;
  }

  determineNegativeStatus(status: string | null, accountType: string | null): boolean {
    if (!status) return false;
    
    const statusLower = status.toLowerCase();
    const negativeIndicators = [
      'late', 'delinquent', 'past due', 'collection', 'collections',
      'charged off', 'charge off', 'write off', 'default', 'bankruptcy',
      'foreclosure', 'repossession', 'settlement'
    ];
    
    return negativeIndicators.some(indicator => statusLower.includes(indicator));
  }
}

const normalizer = new TradelineNormalizer();

// Enhanced sanitization with normalization
function sanitizeDatabaseTradeline(dbTradeline: DatabaseTradeline): ParsedTradeline {
  const normalized = {
    id: dbTradeline.id || '',
    user_id: dbTradeline.user_id || '',
    creditor_name: dbTradeline.creditor_name || '',
    account_number: dbTradeline.account_number,
    account_balance: normalizer.normalizeCurrency(dbTradeline.account_balance),
    account_status: normalizer.normalizeAccountStatus(dbTradeline.account_status || ''),
    account_type: normalizer.normalizeAccountType(dbTradeline.account_type || ''),
    date_opened: normalizer.normalizeDate(dbTradeline.date_opened),
    is_negative: dbTradeline.is_negative || normalizer.determineNegativeStatus(
      dbTradeline.account_status, 
      dbTradeline.account_type
    ),
    dispute_count: dbTradeline.dispute_count || 0,
    created_at: dbTradeline.created_at || new Date().toISOString(),
    credit_limit: normalizer.normalizeCurrency(dbTradeline.credit_limit),
    credit_bureau: dbTradeline.credit_bureau,
    monthly_payment: normalizer.normalizeCurrency(dbTradeline.monthly_payment),
  };

  return normalized;
}

// Enhanced conversion with normalization
export const convertAPITradelineToDatabase = (
  apiTradeline: APITradeline,
  authUserId: string,
): ParsedTradeline => {
  const normalizedType = normalizer.normalizeAccountType(apiTradeline.account_type);
  const normalizedStatus = normalizer.normalizeAccountStatus(apiTradeline.account_status || '');
  
  return {
    id: uuidv4(),
    user_id: authUserId,
    creditor_name: apiTradeline.creditor_name,
    account_number: apiTradeline.account_number,
    account_balance: normalizer.normalizeCurrency(apiTradeline.account_balance),
    account_status: normalizedStatus,
    account_type: normalizedType,
    date_opened: normalizer.normalizeDate(apiTradeline.date_opened),
    is_negative: apiTradeline.is_negative || normalizer.determineNegativeStatus(
      normalizedStatus, 
      normalizedType
    ),
    dispute_count: apiTradeline.dispute_count || 0,
    created_at: new Date().toISOString(),
    credit_limit: normalizer.normalizeCurrency(apiTradeline.credit_limit),
    credit_bureau: apiTradeline.credit_bureau,
    monthly_payment: normalizer.normalizeCurrency(apiTradeline.monthly_payment),
  };
};

// Enhanced validation with better error messages
export const validateAPITradeline = (
  tradeline: unknown
): { success: boolean; data?: APITradeline; error?: string } => {
  try {
    const validated = APITradelineSchema.parse(tradeline);
    return { success: true, data: validated };
  } catch (error) {
    if (error instanceof z.ZodError) {
      const detailedErrors = error.errors.map(e => {
        const field = e.path.join('.');
        return `${field}: ${e.message} (received: ${JSON.stringify(e.received)})`;
      });
      return { 
        success: false, 
        error: `Validation failed for fields: ${detailedErrors.join(', ')}` 
      };
    }
    return { success: false, error: `Unknown validation error: ${error}` };
  }
};

// Enhanced database save with better error handling
export const saveTradelinesToDatabase = async (
  tradelines: ParsedTradeline[], 
  authUserId: string
): Promise<{
  success: boolean;
  savedTradelines: ParsedTradeline[];
  errors: string[];
  summary: {
    total: number;
    saved: number;
    updated: number;
    failed: number;
  };
}> => {
  const results = {
    success: true,
    savedTradelines: [] as ParsedTradeline[],
    errors: [] as string[],
    summary: {
      total: tradelines.length,
      saved: 0,
      updated: 0,
      failed: 0
    }
  };

  try {
    console.log(`[DEBUG] 💾 Processing ${tradelines.length} tradelines for user ${authUserId}`);

    // Import fuzzy matching
    const { 
      findExistingTradelineByFuzzyMatch, 
      mergeTradelineFields, 
      updateTradelineFields 
    } = await import('@/utils/fuzzyTradelineMatching');

    const newTradelines: ParsedTradeline[] = [];
    const updateOperations: Array<{id: string, updates: Partial<ParsedTradeline>}> = [];

    // Process each tradeline with enhanced validation
    for (const tradeline of tradelines) {
      try {
        // Validate before processing
        const validation = validateParsedTradeline(tradeline);
        if (!validation.success) {
          console.error(`[ERROR] Validation failed for ${tradeline.creditor_name}:`, validation.error);
          results.errors.push(`${tradeline.creditor_name}: ${validation.error}`);
          results.summary.failed++;
          continue;
        }

        const validatedTradeline = validation.data!;
        validatedTradeline.user_id = authUserId; // Ensure correct user ID

        // Check for existing matches
        const fuzzyMatch = await findExistingTradelineByFuzzyMatch(validatedTradeline, authUserId);

        if (fuzzyMatch?.isMatch && fuzzyMatch.existingTradeline) {
          // Merge with existing
          const updates = mergeTradelineFields(fuzzyMatch.existingTradeline, validatedTradeline);
          
          if (Object.keys(updates).length > 0) {
            updateOperations.push({
              id: fuzzyMatch.existingTradeline.id,
              updates
            });
            console.log(`[DEBUG] 🔄 Queued update for ${fuzzyMatch.existingTradeline.creditor_name}`);
          }
        } else {
          // Add as new
          newTradelines.push(validatedTradeline);
          console.log(`[DEBUG] ➕ Queued insert for ${validatedTradeline.creditor_name}`);
        }

      } catch (error) {
        console.error(`[ERROR] Failed to process tradeline ${tradeline.creditor_name}:`, error);
        results.errors.push(`${tradeline.creditor_name}: ${error}`);
        results.summary.failed++;
      }
    }

    // Batch insert new tradelines
    if (newTradelines.length > 0) {
      try {
        const { data: insertedData, error: insertError } = await supabase
          .from('tradelines')
          .upsert(newTradelines, { 
            onConflict: 'user_id,account_number,creditor_name,credit_bureau',
            ignoreDuplicates: false 
          })
          .select('*');

        if (insertError) {
          console.error('[ERROR] Batch insert failed:', insertError);
          results.errors.push(`Batch insert failed: ${insertError.message}`);
          results.summary.failed += newTradelines.length;
        } else if (insertedData) {
          const sanitized = insertedData.map(item => sanitizeDatabaseTradeline(item as DatabaseTradeline));
          results.savedTradelines.push(...sanitized);
          results.summary.saved += insertedData.length;
          console.log(`[SUCCESS] ✅ Inserted ${insertedData.length} new tradelines`);
        }
      } catch (error) {
        console.error('[ERROR] Database insert exception:', error);
        results.errors.push(`Database insert failed: ${error}`);
        results.summary.failed += newTradelines.length;
      }
    }

    // Process updates
    if (updateOperations.length > 0) {
      for (const { id, updates } of updateOperations) {
        try {
          const success = await updateTradelineFields(id, updates);
          if (success) {
            results.summary.updated++;
          } else {
            results.summary.failed++;
            results.errors.push(`Failed to update tradeline ${id}`);
          }
        } catch (error) {
          results.summary.failed++;
          results.errors.push(`Update failed for ${id}: ${error}`);
        }
      }
    }

    console.log(`[SUMMARY] 📊 Processing complete:`, results.summary);
    
    results.success = results.summary.failed === 0;
    return results;

  } catch (error) {
    console.error('[ERROR] Critical error in saveTradelinesToDatabase:', error);
    return {
      success: false,
      savedTradelines: [],
      errors: [`Critical error: ${error}`],
      summary: {
        total: tradelines.length,
        saved: 0,
        updated: 0,
        failed: tradelines.length
      }
    };
  }
};

// Keep existing functions for backward compatibility
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

// Re-export other functions from original parser for compatibility
export * from './tradelineParser';