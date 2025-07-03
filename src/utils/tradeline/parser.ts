
import { ParsedTradeline, ParsedTradelineSchema } from './types';
import { ZodError } from 'zod';

// Patterns for parsing credit report text
const TRADELINE_PATTERNS = {
  creditorName: /^([A-Z\s&'-]+)(?:\s+\*{4}\d{4})?/m,
  accountNumber: /\*{4}(\d{4})/,
  balance: /\$[\d,]+(?:\.\d{2})?/g,
  dateOpened: /(?:Opened|Date Opened)[:\s]+(\d{1,2}\/\d{1,2}\/\d{2,4})/i,
  accountStatus: /(?:Status|Account Status)[:\s]+(Open|Closed|Charged Off|Collection|Disputed)/i,
};

/**
 * Parses a single tradeline from raw text
 * @param rawText - The raw text containing tradeline information
 * @param userId - The user ID to associate with the tradeline
 * @returns Parsed tradeline object
 */
export function parseTradeline(rawText: string, userId?: string): ParsedTradeline {
  try {
    // Parse creditor name
    const creditorMatch = rawText.match(TRADELINE_PATTERNS.creditorName);
    const creditor_name = creditorMatch ? creditorMatch[1].trim() : '';

    // Parse account number
    const accountMatch = rawText.match(TRADELINE_PATTERNS.accountNumber);
    const account_number = accountMatch ? `****${accountMatch[1]}` : '';

    // Parse balance (get the last balance mentioned)
    const balanceMatches = rawText.match(TRADELINE_PATTERNS.balance);
    const account_balance = balanceMatches ? balanceMatches[balanceMatches.length - 1] : '';

    // Parse date opened
    const dateMatch = rawText.match(TRADELINE_PATTERNS.dateOpened);
    const date_opened = dateMatch ? dateMatch[1] : '';

    // Parse account status
    const statusMatch = rawText.match(TRADELINE_PATTERNS.accountStatus);
    const account_status = statusMatch ? statusMatch[1].toLowerCase() : '';

    // Determine account type based on creditor name
    let account_type: any = '';
    if (creditor_name.toLowerCase().includes('mortgage') || creditor_name.toLowerCase().includes('home')) {
      account_type = 'mortgage';
    } else if (creditor_name.toLowerCase().includes('auto') || creditor_name.toLowerCase().includes('car')) {
      account_type = 'auto_loan';
    } else if (creditor_name.toLowerCase().includes('student')) {
      account_type = 'student_loan';
    } else if (account_status.includes('collection')) {
      account_type = 'collection';
    } else if (creditor_name.toLowerCase().includes('card')) {
      account_type = 'credit_card';
    }

    // Determine if tradeline is negative
    const is_negative = account_status.includes('charged') || 
                       account_status.includes('collection') || 
                       account_status.includes('late') ||
                       rawText.toLowerCase().includes('delinquent');

    const tradelineData = {
      user_id: userId,
      creditor_name: creditor_name || "",
      account_number: account_number || "",
      account_balance: account_balance || "",
      date_opened: date_opened || "",
      account_type: account_type || "",
      account_status: account_status || "",
      is_negative: is_negative || false,
      credit_limit: "",
      monthly_payment: "",
      credit_bureau: "",
      dispute_count: 0,
    };

    return ParsedTradelineSchema.parse(tradelineData);
  } catch (error) {
    console.error('Error parsing tradeline:', error);
    
    // Return a minimal valid tradeline on error
    return ParsedTradelineSchema.parse({
      user_id: userId,
      creditor_name: "",
      account_number: "",
      account_balance: "",
      credit_limit: "",
      monthly_payment: "",
      date_opened: "",
      is_negative: false,
      account_type: "",
      account_status: "",
      credit_bureau: "",
      dispute_count: 0,
    });
  }
}

/**
 * Parses multiple tradelines from credit report text
 * @param creditReportText - The full credit report text
 * @param userId - The user ID to associate with tradelines
 * @returns Array of parsed tradelines
 */
export function parseTradelinesFromText(creditReportText: string, userId?: string): ParsedTradeline[] {
  try {
    // Split the text into potential tradeline sections
    const sections = creditReportText.split(/\n\s*\n/).filter(section => 
      section.trim().length > 50 && 
      (section.includes('$') || section.toLowerCase().includes('account'))
    );

    const tradelines: ParsedTradeline[] = [];

    for (const section of sections) {
      try {
        const tradeline = parseTradeline(section, userId);
        if (tradeline.creditor_name) {
          tradelines.push(tradeline);
        }
      } catch (error) {
        console.warn('Failed to parse tradeline section:', error);
        continue;
      }
    }

    return tradelines;
  } catch (error) {
    console.error('Error parsing tradelines from text:', error);
    return [];
  }
}

/**
 * Validates and sanitizes tradeline data
 * @param tradelines - Array of tradelines to validate
 * @returns Array of validated tradelines
 */
export function validateTradelines(tradelines: any[]): ParsedTradeline[] {
  const validTradelines: ParsedTradeline[] = [];

  for (const tradeline of tradelines) {
    try {
      const validatedTradeline = ParsedTradelineSchema.parse(tradeline);
      validTradelines.push(validatedTradeline);
    } catch (error) {
      if (error instanceof ZodError) {
        console.warn('Tradeline validation failed:', error.errors);
      } else {
        console.warn('Unexpected validation error:', error);
      }
    }
  }

  return validTradelines;
}
