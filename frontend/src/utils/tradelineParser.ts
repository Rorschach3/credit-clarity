<<<<<<< Updated upstream:src/utils/tradelineParser.ts
import { sanitizeText } from "./ocr-parser";
import { supabase } from "../../supabase/client";
import { z } from "zod";

// Zod schema for a parsed tradeline
export const ParsedTradelineSchema = z.object({
  id: z.string().optional(),
  creditorName: z.string().min(2, { message: "Creditor name must be at least 2 characters." }),
  accountNumber: z.string().min(4, { message: "Account number must be at least 4 characters." }),
  accountName: z.string().min(2, { message: "Account name must be at least 2 characters." }), // Ensure accountName is required
  accountStatus: z.string().min(2, { message: "Status must be at least 2 characters." }),
  isNegative: z.boolean(),
  accountBalance: z.string().nullable().default("0"),
  dateOpened: z.string().nullable(),
  negativeReason: z.string().nullable().optional(),
  accountType: z.string().nullable().optional(),
  creditLimit: z.string().nullable().optional().default("0"),
  monthlyPayment: z.string().nullable().optional().default("0"),
  creditBureau: z.string().nullable(),
  disputeCount: z.number().default(0)
});

export type ParsedTradeline = z.infer<typeof ParsedTradelineSchema>;

const accountNumberRegexes = [
  /Account\s+[+:]?\s*(\d{4,}[XxXx]*)/i,
  /Account Number\s*[:#]?\s*(\d{4,}[XxXx]*)/i,
  /\b(\d{4,})(?:X{2,}|\*+)?\b/,
  /Acct\s*#[: ]*\s*(\d{4,}[XxXx]*)/i,
];

const statusKeywords = {
  chargedOff: /charged off/i,
  collection: /sent to collections|in collection/i,
  closed: /account closed/i,
  paid: /paid in full/i,
  open: /open account|current/i,
};

const negativeRegex = /collection|charge.?off|late/i;

export const parseTradelinesFromText = (
  text: string,
): { valid: ParsedTradeline[]; rejected: { entry: string; errors: z.ZodIssue[] }[] } => {
  const valid: ParsedTradeline[] = [];
  const rejected: { entry: string; errors: z.ZodIssue[] }[] = [];
  const sanitized = sanitizeText(text);

  const entries = sanitized.split(
    /^(?=CHASE CARD|SCHOOLSFIRST|BANK OF AMERICA|CITIBANK|CAPITAL ONE|AMEX|DISCOVER|WELLS FARGO|CLIMB CREDIT|CAPITAL ONE N\.A\.)/gim,
  );

  for (const entry of entries) {
    if (!entry.trim()) continue;

    const creditorName = entry.match(/^(.*?)(?:\n|Account Number:|Status:)/i)?.[1]?.trim() || "Unknown";
    let accountNumber = "N/A";
    for (const rx of accountNumberRegexes) {
      const match = entry.match(rx);
      if (match?.[1]) {
        accountNumber = match[1].replace(/\s/g, "");
        break;
      }
    }
    let accountStatus = "Unknown";
    const detected = Object.entries(statusKeywords).find(([, rx]) => rx.test(entry));
    if (detected) accountStatus = detected[0];

    const isNegative = negativeRegex.test(entry) || negativeRegex.test(accountStatus);
    const negativeReason = negativeRegex.exec(entry)?.[0] ?? negativeRegex.exec(accountStatus)?.[0] ?? null;

    const balanceMatch = entry.match(/Balance:\s*\$?([\d,]+\.?\d{0,2})/i);
    const accountBalance = balanceMatch ? parseFloat(balanceMatch[1].replace(/,/g, "")).toString() : "0";

    const dateMatch = entry.match(/Date Opened:\s*(\d{2}\/\d{2}\/\d{4})/i);
    const dateOpened = dateMatch?.[1] ?? null;

    const creditBureau = /Experian/i.test(entry)
      ? "Experian"
      : /TransUnion/i.test(entry)
      ? "TransUnion"
      : /Equifax/i.test(entry)
      ? "Equifax"
      : null;

    const tradeline: Omit<ParsedTradeline, "id"> = {
      creditorName,
      accountNumber,
      accountStatus,
      isNegative,
      negativeReason,
      accountBalance,
      dateOpened,
      accountType: isNegative ? "Negative" : "Good",
      creditLimit: null,
      monthlyPayment: null,
      creditBureau: creditBureau,
    };
    
    const result = ParsedTradelineSchema.omit({ id: true }).safeParse(tradeline);
    if (result.success) {
      valid.push(result.data);
    } else {
      rejected.push({ entry: entry.trim(), errors: result.error.errors });
    }
  }

  return { valid, rejected };
};

interface TradelineRow {
  id: string;
  user_id: string;
  creditor_name: string;
  account_number: string;
  account_status?: string;
  account_balance?: string;
  date_opened: string | null;
  account_type?: string | null;
  credit_limit?: string | null;
  monthly_payment?: string | null;
  credit_bureau: string | null;
  created_at?: Date;
  dispute_count?: number;
  isNegative?: boolean;
}

export function fetchUserTradelines(data: TradelineRow[]): ParsedTradeline[] {
  return (data || []).map((row: TradelineRow) => {
    const isNegative = row.account_status ? negativeRegex.test(row.account_status) : false;
    return ParsedTradelineSchema.parse({
      id: row.id,
      creditorName: row.creditor_name || "",
      accountNumber: row.account_number || "",
      accountStatus: row.account_status || "",
      isNegative,
      negativeReason: row.account_status ? negativeRegex.exec(row.account_status)?.[0] ?? null : null,
      accountBalance: typeof row.account_balance === 'string' ? parseFloat(row.account_balance) || "0" : row.account_balance || "0",
      dateOpened: row.date_opened,
      accountType: row.account_type,
      creditLimit: typeof row.credit_limit === 'string' ? parseFloat(row.credit_limit) || "0" : row.credit_limit || "0",
      monthlyPayment: typeof row.monthly_payment === 'string' ? parseFloat(row.monthly_payment) || "0" : row.monthly_payment || "0",
      creditBureau: row.credit_bureau,
    });
  });
}

export async function saveTradelinesToDatabase(tradelines: ParsedTradeline[], userId: string): Promise<void> {
  if (!userId || tradelines.length === 0) return;

  const convertDateFormat = (dateString: string | null): string | null => {
    const match = dateString?.match(/(\d{2})\/(\d{2})\/(\d{4})/);
    return match ? `${match[3]}-${match[1]}-${match[2]}` : null;
  };

  const rows = tradelines.map((tradeline) => ({
    id: tradeline.id || tradeline.id,
    user_id: userId,
    created_at: new Date(),
    dispute_count: tradeline.disputeCount,
    creditor_name: tradeline.creditorName,
    account_number: tradeline.accountNumber,
    account_status: tradeline.accountStatus,
    account_type: tradeline.accountType,
    account_balance: tradeline.accountBalance,
    date_opened: convertDateFormat(tradeline.dateOpened),
    credit_limit: tradeline.creditLimit,
    monthly_payment: tradeline.monthlyPayment,
    credit_bureau: tradeline.creditBureau,
    isNegative: tradeline.isNegative,
  }));

  const { error } = await supabase.from("tradelines").insert(rows);
  if (error) {
    throw new Error(`Failed to save tradelines: ${error.message}`);
  }
}
=======
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

// Types for pagination
interface PaginationOptions {
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

interface PaginatedTradelinesResponse {
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

// Save tradelines to Supabase database with enhanced duplicate detection
export const saveTradelinesToDatabase = async (tradelines: ParsedTradeline[], authUserId: string) => {
  try {
    console.log(`[DEBUG] 💾 Saving ${tradelines.length} tradelines to Supabase with enhanced duplicate detection for user ${authUserId}`);
    
    // Use the new enhanced database logic
    const { saveTradelinesWithEnrichment } = await import('@/utils/tradeline/enhanced-database');
    return await saveTradelinesWithEnrichment(tradelines, authUserId);
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
>>>>>>> Stashed changes:frontend/src/utils/tradelineParser.ts
