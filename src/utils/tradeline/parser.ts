
import { sanitizeText } from "../ocr-parser";
import { supabase } from "@/integrations/supabase/client";
import { extractTradelineData } from "@/services/llm-parser";
import { ParsedTradeline, ParsedTradelineSchema, AccountType, AccountStatus, CreditBureau } from "./types";

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
    date_opened: String(safeExtract('date_opened', "xxxx/xx/xx")),
    is_negative: Boolean(safeExtract('is_negative', false)),
    account_type: validateAccountType(parsedObj.account_type) || "credit_card",
    account_status: validateAccountStatus(parsedObj.account_status) || "open",
    credit_bureau: validateCreditBureau(parsedObj.credit_bureau) || "",
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
    raw_text: originalText || "",
  });
}

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
