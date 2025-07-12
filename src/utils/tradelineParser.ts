import { z } from "zod";

// Define the ParsedTradeline schema - this should match your Supabase schema
export const ParsedTradelineSchema = z.object({
  id: z.string().optional(), // ✅ Removed .uuid() to allow any string format
  user_id: z.string().optional(), // ✅ Removed .uuid() for flexibility 
  creditor_name: z.string().default('NULL'),
  account_balance: z.string().default(''),
  created_at: z.string(), // Required field to match component expectations
  dispute_count: z.number().int().default(0),
  credit_limit: z.string().default(''),
  monthly_payment: z.string().default(''),
  account_number: z.string().default(''),
  date_opened: z.string().default('xxxx/xx/xx'),
  is_negative: z.boolean().default(false),
  account_type: z.string().default(''),
  account_status: z.string().default(''),
  credit_bureau: z.string().default(''),
});

// Export the inferred type
export type ParsedTradeline = z.infer<typeof ParsedTradelineSchema>;

// Function to parse and validate tradeline data
export const parseTradeline = (data: unknown): ParsedTradeline => {
  return ParsedTradelineSchema.parse(data);
};

// Function to safely parse tradeline with error handling
export const safelyParseTradeline = (data: unknown): { success: true; data: ParsedTradeline } | { success: false; error: string } => {
  try {
    const parsed = ParsedTradelineSchema.parse(data);
    return { success: true, data: parsed };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return { success: false, error: error.errors.map(e => e.message).join(', ') };
    }
    return { success: false, error: 'Unknown parsing error' };
  }
};

// Function to create a tradeline with default values
export const createTradelineWithDefaults = (partial: Partial<ParsedTradeline>): ParsedTradeline => {
  const now = new Date().toISOString();
  return {
    id: partial.id || `tradeline-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    user_id: partial.user_id || '',
    creditor_name: partial.creditor_name || 'NULL',
    account_balance: partial.account_balance || '',
    created_at: partial.created_at || now,
    dispute_count: partial.dispute_count || 0,
    credit_limit: partial.credit_limit || '',
    monthly_payment: partial.monthly_payment || '',
    account_number: partial.account_number || '',
    date_opened: partial.date_opened || 'xxxx/xx/xx',
    is_negative: partial.is_negative || false,
    account_type: partial.account_type || '',
    account_status: partial.account_status || '',
    credit_bureau: partial.credit_bureau || '',
  };
};

// Function to save tradelines to database (you'll need to implement this based on your backend)
export const saveTradelinesToDatabase = async (tradelines: ParsedTradeline[], userId: string): Promise<void> => {
  try {
    // This would typically make an API call to your backend
    // For now, just log the action
    console.log(`Saving ${tradelines.length} tradelines for user ${userId}`);
    
    // Example API call (adjust URL and method based on your backend):
    // const response = await fetch('/api/tradelines', {
    //   method: 'POST',
    //   headers: {
    //     'Content-Type': 'application/json',
    //   },
    //   body: JSON.stringify({ userId, tradelines }),
    // });
    
    // if (!response.ok) {
    //   throw new Error('Failed to save tradelines');
    // }
    
    // For now, just simulate success
    await new Promise(resolve => setTimeout(resolve, 100));
    
  } catch (error) {
    console.error('Error saving tradelines:', error);
    throw new Error(error instanceof Error ? error.message : 'Failed to save tradelines');
  }
};

// Utility function to validate multiple tradelines
export const validateTradelines = (tradelines: unknown[]): { valid: ParsedTradeline[]; invalid: { index: number; error: string }[] } => {
  const valid: ParsedTradeline[] = [];
  const invalid: { index: number; error: string }[] = [];
  
  tradelines.forEach((tradeline, index) => {
    const result = safelyParseTradeline(tradeline);
    if (result.success) {
      valid.push(result.data);
    } else {
      invalid.push({ index, error: result.error });
    }
  });
  
  return { valid, invalid };
};