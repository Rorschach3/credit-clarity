// src/utils/tradelineParser.ts
import { sanitizeText } from "./ocr-parser";
import { z } from "zod";
import { supabase } from "@/integrations/supabase/client";
import { extractTradelineData } from "@/services/llm-parser";

// Type definitions for enum values
export type AccountType = "credit_card" | "loan" | "mortgage" | "auto_loan" | "student_loan" | "collection" | "";
export type AccountStatus = "open" | "closed" | "in_collection" | "charged_off" | "disputed" | "";
export type CreditBureau = "equifax" | "transunion" | "experian";

// Enhanced Zod schema with better validation and error handling
export const ParsedTradelineSchema = z.object({
  id: z.string().uuid().optional(),
  user_id: z.string().uuid().optional(),
  creditor_name: z.string().min(1).default(""),
  account_number: z.string().min(1).default(""),
  account_balance: z.string().default("$0"),
  created_at: z.string().datetime().default(() => new Date().toISOString()),
  credit_limit: z.string().default("$0"),
  monthly_payment: z.string().default("$0"),
  date_opened: z.string().default(""),
  is_negative: z.boolean().default(false),
  account_type: z.enum(["credit_card", "loan", "mortgage", "auto_loan", "student_loan", "collection", ""]).default("credit_card"),
  account_status: z.enum(["open", "closed", "in_collection", "charged_off", "disputed", ""]).default("open"),
  credit_bureau: z.enum(["equifax", "transunion", "experian", ""]).default(""),
  dispute_count: z.number().int().min(0).default(0),
  raw_text: z.string().default(""), // Renamed raw_text to rawText
});

export type ParsedTradeline = z.infer<typeof ParsedTradelineSchema>;

// Enhanced parsing with better error handling and retry logic
export async function parseTradelinesFromText(
  text: string,
  userId: string,
  options: {
    maxRetries?: number;
    timeoutMs?: number;
    fallbackToBasicParsing?: boolean;
  } = {}
): Promise<ParsedTradeline[]> {
  const { maxRetries = 2, timeoutMs = 30000, fallbackToBasicParsing = true } = options;
  
  if (!text?.trim()) {
    console.warn("⚠️ Empty or invalid text provided for parsing");
    return [];
  }

  // More robust text splitting with multiple patterns
  const entries = sanitizeText(text)
    .split(/^(?=(?:CHASE|SCHOOLSFIRST|BANK OF AMERICA|CITIBANK|CAPITAL ONE|AMERICAN EXPRESS|AMEX|DISCOVER|WELLS FARGO|CAPITAL ONE N\.A\.)\b)/mi)
    .filter((e) => e.trim().length > 10);

  if (entries.length === 0) {
    console.warn("⚠️ No valid tradeline entries found in text");
    return fallbackToBasicParsing ? [createFallbackTradeline(userId, ["No tradeline entries found"])] : [];
  }

  const parsedTradelines: ParsedTradeline[] = [];
  console.log(`📊 Processing ${entries.length} tradeline entries`);

  for (const [index, entry] of entries.entries()) {
    console.log(`🔄 Processing entry ${index + 1}/${entries.length}`);
    
    const result = await parseTradelineWithRetry(entry, userId, maxRetries, timeoutMs);
    if (result) {
      parsedTradelines.push(result);
    } else if (fallbackToBasicParsing) {
      const fallback = createFallbackTradeline(userId, [`Failed to parse entry ${index + 1}`], entry);
      parsedTradelines.push(fallback);
    }
  }

  console.log(`✅ Successfully parsed ${parsedTradelines.length} tradelines`);
  return parsedTradelines;
}

// Retry logic for individual tradeline parsing
async function parseTradelineWithRetry(
  entry: string, 
  userId: string, 
  maxRetries: number,
  timeoutMs: number
): Promise<ParsedTradeline | null> {
  let lastError: Error | null = null;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      console.log(`🔄 Attempt ${attempt}/${maxRetries} for tradeline parsing`);
      
      // Add timeout to LLM call
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => reject(new Error('LLM parsing timeout')), timeoutMs);
      });
      
      const llmPromise = extractTradelineData(entry);
      const jsonResult = await Promise.race([llmPromise, timeoutPromise]);

      if (!jsonResult || typeof jsonResult !== 'string') {
        throw new Error('LLM returned empty or invalid response');
      }
      
      if (jsonResult.trim() === '') {
        throw new Error('LLM returned empty response');
      }

      let parsed: Record<string, unknown>;
      try {
        parsed = JSON.parse(jsonResult);
      } catch (parseError) {
        throw new Error(`Invalid JSON response from LLM: ${(parseError as Error).message}`);
      }

      // Check critical fields explicitly
      if (!parsed.creditor_name || !parsed.account_number) {
        throw new Error('LLM response missing critical fields (creditor_name or account_number)');
      }

      // Automatically correct 'is_negative' for collections
      if ((parsed.account_type as string)?.toLowerCase() === 'collection') {
        parsed.is_negative = true;
      }

      // Enhanced data sanitization
      const sanitizedParsed = sanitizeTradelineData(parsed, userId, entry);
      
      // Validate against schema
      const validatedTradeline = ParsedTradelineSchema.parse(sanitizedParsed);
      
      console.log(`✅ Successfully parsed tradeline on attempt ${attempt}`);
      return validatedTradeline;

    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      console.warn(`⚠️ Attempt ${attempt}/${maxRetries} failed:`, lastError.message);
      
      // Add exponential backoff for retries
      if (attempt < maxRetries) {
        const backoffMs = Math.min(1000 * Math.pow(2, attempt - 1), 5000);
        console.log(`⏳ Waiting ${backoffMs}ms before retry...`);
        await new Promise(resolve => setTimeout(resolve, backoffMs));
      }
    }
  }
  
  console.error(`❌ All ${maxRetries} attempts failed for tradeline parsing:`, lastError?.message);
  return null;
}

// Enhanced data sanitization with better defaults and validation
function sanitizeTradelineData(parsed: unknown, userId: string, originalText?: string): Partial<ParsedTradeline> {
  const warnings: string[] = [];
  let confidenceScore = 0.8; // Start with high confidence

  // Type guard to ensure parsed is an object
  if (!parsed || typeof parsed !== 'object') {
    return createFallbackData(userId, ["Invalid parsed data structure"]);
  }

  const parsedObj = parsed as Record<string, unknown>;

  // Helper function to safely extract and validate field
  const safeExtract = (field: string, defaultValue: string | number | boolean, validator?: (val: unknown) => boolean) => {
    const value = parsedObj[field];
    if (value === null || value === undefined || value === '') {
      warnings.push(`Missing ${field}, using default`);
      confidenceScore -= 0.1;
      return defaultValue;
    }
    if (validator && !validator(value)) {
      warnings.push(`Invalid ${field} format, using default`);
      confidenceScore -= 0.1;
      return defaultValue;
    }
    return value;
  };

  return {
    creditor_name: String(safeExtract('creditor_name', "")),
    account_number: String(safeExtract('account_number', "")),
    account_balance: String(safeExtract('account_balance', "$0")),
    created_at: new Date().toISOString(),
    credit_limit: String(safeExtract('credit_limit', "$0")),
    monthly_payment: String(safeExtract('monthly_payment', "$0")),
    date_opened: String(safeExtract('date_opened', "xxxx/xx/xx")), // Changed default to match DB schema
    is_negative: Boolean(safeExtract('is_negative', false)),
    account_type: validateAccountType(parsedObj.account_type) || "credit_card", // Ensure valid default
    account_status: validateAccountStatus(parsedObj.account_status) || "open",   // Ensure valid default
    credit_bureau: validateCreditBureau(parsedObj.credit_bureau) || "",   // Ensure valid default
    user_id: userId,
    dispute_count: Number(safeExtract('dispute_count', 0)) || 0,
    raw_text: String(originalText || ""),
  };
}
// Helper function to create fallback data structure
function createFallbackData(userId: string, warnings: string[]): Partial<ParsedTradeline> {
  console.warn("⚠️ Creating fallback data structure. Warnings:", warnings);
  return {
    creditor_name: "",
    account_number: "",
    account_balance: "$0",
    created_at: new Date().toISOString(),
    credit_limit: "$0",
    monthly_payment: "$0",
    date_opened: "",
    is_negative: false,
    account_type: "" as AccountType,
    account_status: "" as AccountStatus,
    credit_bureau: "" as CreditBureau,
    user_id: userId,
    dispute_count: 0,
  };
}

// Create fallback tradeline when parsing fails
function createFallbackTradeline(userId: string, warnings: string[] = [], originalText?: string): ParsedTradeline {
  console.warn("⚠️ Creating fallback tradeline due to parsing failure. Warnings:", warnings);
  let creditorName = "";
  
  // Try to extract creditor name from original text if available
  if (originalText) {
    const creditorMatch = originalText.match(/^([A-Z\s&.]+)/);
    if (creditorMatch) {
      creditorName = creditorMatch[1].trim();
    }
  }

  return ParsedTradelineSchema.parse({
    creditor_name: creditorName,
    account_number: "",
    account_balance: "$0",
    created_at: new Date().toISOString(),
    credit_limit: "$0",
    monthly_payment: "$0",
    date_opened: "",
    is_negative: false,
    account_type: "" as AccountType,
    account_status: "" as AccountStatus,
    credit_bureau: "" as CreditBureau,
    user_id: userId,
    dispute_count: 0,
    raw_text: originalText || "", // Renamed raw_text to rawText
  });
}


const uuidSchema = z.string().uuid();

// Enhanced database save with better error handling
export async function saveTradelinesToDatabase(tradelines: ParsedTradeline[], userId: string) {
  if (!uuidSchema.safeParse(userId).success) {
    console.error("❌ Invalid user_id provided:", userId);
    return;
  }

  try {
    // Filter out partial tradelines (missing critical fields)
    const validTradelines = tradelines.filter(tl =>
      tl.creditor_name && tl.account_number && tl.account_type
    );
    
    const partialTradelines = tradelines.filter(tl =>
      !tl.creditor_name || !tl.account_number || !tl.account_type
    );
    
    if (partialTradelines.length > 0) {
      console.warn(`⚠️ Skipping ${partialTradelines.length} partial tradelines:`, partialTradelines);
    }

    if (validTradelines.length === 0) {
      console.warn("⚠️ No valid tradelines to save after filtering");
      return;
    }

    // Deduplicate tradelines using the same composite key as backend
    const dedupedTradelines = validTradelines.reduce((acc, current) => {
      const key = `${current.user_id}|${current.creditor_name}|${current.account_number}|${current.account_type}`;
      
      // Only add if we haven't seen this combination before
      if (!acc.has(key)) {
        acc.set(key, current);
      } else {
        console.log(`⚠️ Skipping duplicate tradeline: ${key}`);
      }
      
      return acc;
    }, new Map<string, ParsedTradeline>());

    const uniqueTradelines = Array.from(dedupedTradelines.values());
    
    if (uniqueTradelines.length < validTradelines.length) {
      console.warn(`⚠️ Removed ${validTradelines.length - uniqueTradelines.length} duplicate tradelines`);
    }

    console.log('Saving tradelines to database:', uniqueTradelines);
    console.log("Attempting to save tradelines via Edge Function:", { count: uniqueTradelines.length, userId });
    
    const payload = { tradelines: uniqueTradelines.map(tl => ({ ...tl, user_id: userId })) };
    console.log("Payload sent to Edge Function:", JSON.stringify(payload, null, 2));

    const response = await fetch('https://gywohmbqohytziwsjrps.supabase.co/functions/v1/add-tradeline', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${import.meta.env.VITE_SUPABASE_ANON_KEY}`,
      },
      body: JSON.stringify(payload),
    });

    console.log(`Edge Function response status: ${response.status} ${response.statusText}`);

    if (!response.ok) {
      const errorData = await response.json();
      console.error("Edge Function error response body:", errorData);
      throw new Error(`Failed to save tradelines via Edge Function: ${errorData.message || response.statusText}`);
    }

    const result = await response.json();
    console.log("Tradeline save successful via Edge Function:", result);
    return result;
  } catch (error) {
    console.error("Error in saveTradelinesToDatabase (Edge Function call):", error);
    throw error;
  }
}

// Add logging to your fetch function
export const fetchUserTradelines = async (user_id: string): Promise<ParsedTradeline[]> => {
  try {
    console.log("Fetching tradelines for user:", user_id);
    
    const { data, error } = await supabase
      .from('tradelines')
      .select('*')
      .eq('user_id', user_id);
  
    if (error) {
      console.error("Database fetch error:", error);
      throw error;
    }
    
    console.log("Fetch successful:", { count: data?.length || 0, data });
    
    // Validate and transform fetched data to ParsedTradeline schema
    const parsedData = data ? data.map(item => ParsedTradelineSchema.parse(item)) : [];
    
    // Filter out partial tradelines (missing critical fields)
    return parsedData.filter(tl =>
      tl.creditor_name && tl.account_number && tl.account_type
    );
  } catch (error) {
    console.error("Error in fetchUserTradelines:", error);
    throw error;
  }
};

// Enhanced validation functions with better type safety
export function validateAccountType(type: unknown): AccountType | undefined {
  if (!type || typeof type !== 'string') return undefined;
  const validTypes: AccountType[] = ["credit_card", "loan", "mortgage", "auto_loan", "student_loan", "collection", ""];
  const normalizedType = type.toLowerCase().replace(/[_\s]/g, '_') as AccountType;
  return validTypes.includes(normalizedType) ? normalizedType : undefined;
}

export function validateAccountStatus(status: unknown): AccountStatus | undefined {
  if (!status || typeof status !== 'string') return undefined;
  const validStatuses: AccountStatus[] = ["open", "closed", "in_collection", "charged_off", "disputed", ""];
  const normalizedStatus = status.toLowerCase().replace(/\s/g, '_') as AccountStatus;
  return validStatuses.includes(normalizedStatus) ? normalizedStatus : undefined;
}

function validateCreditBureau(bureau: unknown): CreditBureau | undefined {
  if (!bureau || typeof bureau !== 'string') return undefined;
  const validBureaus: CreditBureau[] = ["equifax", "transunion", "experian"];
  const normalizedBureau = bureau.toLowerCase() as CreditBureau;
  return validBureaus.includes(normalizedBureau) ? normalizedBureau : undefined;
}