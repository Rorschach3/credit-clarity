
import { ParsedTradeline, ParsedTradelineSchema } from './types';
import { ZodError } from 'zod';

// Enhanced patterns for parsing credit report text
const TRADELINE_PATTERNS = {
  // Creditor name patterns - look for company names at start of lines
  creditorName: [
    /^([A-Z][A-Z\s&'-]+(?:BANK|CARD|CREDIT|FINANCIAL|CORP|INC|LLC|CO|CAPITAL|CHASE|WELLS|CITI|DISCOVER|AMEX|AMERICAN\s+EXPRESS))[^\n]*$/gim,
    /^([A-Z][A-Z\s&'-]{3,})\s*(?:\*{4}\d{4}|Account|Acct)/gim,
    /^([A-Z\s&'-]{4,})\s+\d{4}\s*$/gim
  ],
  
  // Account number patterns
  accountNumber: [
    /(?:Account|Acct|#|Number)[:\s]*(\*{4}\d{4}|\d{4})/gi,
    /\*{4}(\d{4})/g,
    /(?:ending|last\s+4)[:\s]*(\d{4})/gi
  ],
  
  // Balance patterns
  balance: [
    /(?:Balance|Bal|Amount|Outstanding)[:\s]*\$?([\d,]+\.?\d*)/gi,
    /\$\s?([\d,]+\.?\d*)/g,
    /(?:Current|Present|Total)[:\s]*\$?([\d,]+\.?\d*)/gi
  ],
  
  // Date patterns
  dateOpened: [
    /(?:Opened|Date\s+Opened|Open\s+Date)[:\s]*(\d{1,2}\/\d{1,2}\/\d{2,4})/gi,
    /(\d{1,2}\/\d{1,2}\/\d{2,4})/g
  ],
  
  // Status patterns
  accountStatus: [
    /(?:Status|Account\s+Status)[:\s]*(Open|Closed|Charged\s+Off|Collection|Disputed|Current|Delinquent)/gi,
    /(Open|Closed|Charged\s+Off|Collection|Disputed|Current|Delinquent)/gi
  ],
  
  // Credit limit patterns
  creditLimit: [
    /(?:Credit\s+Limit|Limit|High\s+Credit)[:\s]*\$?([\d,]+\.?\d*)/gi,
    /(?:CL|CR\s+LMT)[:\s]*\$?([\d,]+\.?\d*)/gi
  ],
  
  // Monthly payment patterns
  monthlyPayment: [
    /(?:Monthly\s+Payment|Payment|Pmt)[:\s]*\$?([\d,]+\.?\d*)/gi,
    /(?:Min\s+Payment|Minimum)[:\s]*\$?([\d,]+\.?\d*)/gi
  ]
};

/**
 * Enhanced function to extract a value using multiple patterns
 */
function extractValue(text: string, patterns: RegExp[]): string {
  for (const pattern of patterns) {
    const matches = text.match(pattern);
    if (matches && matches.length > 0) {
      // Return the first capture group if it exists, otherwise the full match
      return matches[1] || matches[0];
    }
  }
  return "";
}

/**
 * Determines account type based on creditor name and other context
 */
function determineAccountType(creditorName: string, context: string): string {
  const name = creditorName.toLowerCase();
  const fullContext = (creditorName + " " + context).toLowerCase();
  
  if (name.includes('mortgage') || name.includes('home') || fullContext.includes('mortgage')) {
    return 'mortgage';
  } else if (name.includes('auto') || name.includes('car') || fullContext.includes('auto')) {
    return 'auto_loan';
  } else if (name.includes('student') || fullContext.includes('student')) {
    return 'student_loan';
  } else if (fullContext.includes('collection') || name.includes('collection')) {
    return 'collection';
  } else if (name.includes('card') || name.includes('credit') || fullContext.includes('credit card')) {
    return 'credit_card';
  } else if (name.includes('loan') || fullContext.includes('loan')) {
    return 'loan';
  }
  
  return '';
}

/**
 * Determines if a tradeline is negative based on status and context
 */
function isNegativeTradeline(status: string, context: string): boolean {
  const statusLower = status.toLowerCase();
  const contextLower = context.toLowerCase();
  
  return statusLower.includes('charged') || 
         statusLower.includes('collection') || 
         statusLower.includes('delinquent') ||
         statusLower.includes('late') ||
         contextLower.includes('delinquent') ||
         contextLower.includes('past due') ||
         contextLower.includes('charge off') ||
         contextLower.includes('collection');
}

/**
 * Parses a single tradeline from raw text with enhanced pattern matching
 */
export function parseTradeline(rawText: string, userId?: string): ParsedTradeline {
  try {
    console.log("Parsing tradeline from text:", rawText.substring(0, 200));
    
    // Clean the text
    const cleanText = rawText.replace(/\s+/g, ' ').trim();
    
    // Extract creditor name using multiple patterns
    const creditor_name = extractValue(cleanText, TRADELINE_PATTERNS.creditorName).trim();
    
    // Extract account number
    const accountMatch = extractValue(cleanText, TRADELINE_PATTERNS.accountNumber);
    const account_number = accountMatch ? `****${accountMatch.replace(/\*+/, '')}` : '';
    
    // Extract balance
    const balanceRaw = extractValue(cleanText, TRADELINE_PATTERNS.balance);
    const account_balance = balanceRaw ? `$${balanceRaw.replace(/[^\d.,]/g, '')}` : '';
    
    // Extract date opened
    const date_opened = extractValue(cleanText, TRADELINE_PATTERNS.dateOpened);
    
    // Extract account status
    const account_status = extractValue(cleanText, TRADELINE_PATTERNS.accountStatus).toLowerCase();
    
    // Extract credit limit
    const creditLimitRaw = extractValue(cleanText, TRADELINE_PATTERNS.creditLimit);
    const credit_limit = creditLimitRaw ? `$${creditLimitRaw.replace(/[^\d.,]/g, '')}` : '';
    
    // Extract monthly payment
    const paymentRaw = extractValue(cleanText, TRADELINE_PATTERNS.monthlyPayment);
    const monthly_payment = paymentRaw ? `$${paymentRaw.replace(/[^\d.,]/g, '')}` : '';
    
    // Determine account type
    const account_type = determineAccountType(creditor_name, cleanText);
    
    // Determine if negative
    const is_negative = isNegativeTradeline(account_status, cleanText);
    
    const tradelineData = {
      id: crypto.randomUUID(),
      user_id: userId || "",
      creditor_name: creditor_name || "",
      account_number: account_number || "",
      account_balance: account_balance || "",
      created_at: new Date().toISOString(),
      credit_limit: credit_limit || "",
      monthly_payment: monthly_payment || "",
      date_opened: date_opened || "",
      is_negative: is_negative,
      account_type: account_type || "",
      account_status: account_status || "",
      credit_bureau: "",
      dispute_count: 0,
    };

    console.log("Parsed tradeline data:", tradelineData);
    return ParsedTradelineSchema.parse(tradelineData);
    
  } catch (error) {
    console.error('Error parsing tradeline:', error);
    
    // Return a minimal valid tradeline on error
    return ParsedTradelineSchema.parse({
      id: crypto.randomUUID(),
      user_id: userId || "",
      creditor_name: "",
      account_number: "",
      account_balance: "",
      created_at: new Date().toISOString(),
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
 * Enhanced function to parse multiple tradelines from credit report text
 */
export function parseTradelinesFromText(creditReportText: string, userId?: string): ParsedTradeline[] {
  try {
    console.log("Starting to parse tradelines from text, length:", creditReportText.length);
    
    if (!creditReportText || creditReportText.trim().length === 0) {
      console.warn("Empty credit report text provided");
      return [];
    }
    
    // Split the text into potential tradeline sections using various delimiters
    const sections = creditReportText
      .split(/\n\s*\n|_{3,}|-{3,}|={3,}|\f/)
      .filter(section => {
        const trimmed = section.trim();
        return trimmed.length > 20 && (
          trimmed.match(/[A-Z]{2,}/g) || // Has uppercase words
          trimmed.includes('$') || // Has currency
          trimmed.toLowerCase().includes('account') ||
          trimmed.toLowerCase().includes('credit') ||
          trimmed.toLowerCase().includes('balance')
        );
      });

    console.log(`Found ${sections.length} potential tradeline sections`);
    
    const tradelines: ParsedTradeline[] = [];
    
    for (let i = 0; i < sections.length; i++) {
      const section = sections[i];
      console.log(`Processing section ${i + 1}:`, section.substring(0, 100));
      
      try {
        const tradeline = parseTradeline(section, userId);
        
        // Only add tradelines that have at least a creditor name
        if (tradeline.creditor_name && tradeline.creditor_name.length > 2) {
          tradelines.push(tradeline);
          console.log(`Successfully parsed tradeline: ${tradeline.creditor_name}`);
        } else {
          console.log("Skipping tradeline with no creditor name");
        }
      } catch (error) {
        console.warn(`Failed to parse section ${i + 1}:`, error);
        continue;
      }
    }

    console.log(`Successfully parsed ${tradelines.length} tradelines`);
    return tradelines;
    
  } catch (error) {
    console.error('Error parsing tradelines from text:', error);
    return [];
  }
}

/**
 * Validates and sanitizes tradeline data
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
