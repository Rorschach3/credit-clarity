// Fuzzy matching utilities for tradeline deduplication
import { ParsedTradeline } from '@/utils/tradelineParser';
import { supabase } from '@/integrations/supabase/client';

export interface FuzzyMatchResult {
  isMatch: boolean;
  existingTradeline?: ParsedTradeline;
  confidence: number;
  matchingCriteria: {
    creditorNameMatch: boolean;
    accountNumberMatch: boolean; 
    dateOpenedMatch: boolean;
    creditBureauMatch: boolean;
  };
}

/**
 * Normalize creditor name for comparison
 * - Remove extra whitespace, convert to lowercase
 * - Handle common variations and abbreviations
 */
export function normalizeCreditorName(name: string): string {
  if (!name) return '';
  
  let normalized = name
    .trim()
    .toLowerCase()
    .replace(/\s+/g, ' ') // Replace multiple spaces with single space
    .replace(/[^\w\s]/g, ''); // Remove special characters except spaces
  
  // Handle common abbreviations and variations
  const abbreviations: Record<string, string> = {
    'boa': 'bank of america',
    'bofa': 'bank of america',
    'chase': 'jp morgan chase',
    'amex': 'american express',
    'citi': 'citibank',
    'wells': 'wells fargo',
    'discover': 'discover financial',
    'capital one': 'capital one financial',
    'usaa': 'united services automobile association'
  };
  
  // Check if the normalized name matches any abbreviation
  for (const [abbr, fullName] of Object.entries(abbreviations)) {
    if (normalized === abbr) {
      normalized = fullName;
      break;
    }
  }
  
  // Remove common suffixes after abbreviation expansion
  normalized = normalized
    .replace(/\b(bank|credit|card|company|corp|inc|llc|financial|services|association)\b/g, '')
    .replace(/\s+/g, ' ')
    .trim();
    
  return normalized;
}

/**
 * Extract first 4 digits from account number
 * - Handles various formats: "1234-5678-9012", "1234 5678 9012", "1234567890123456"
 * - Returns only numeric characters
 */
export function extractAccountPrefix(accountNumber: string): string {
  if (!accountNumber) return '';
  
  // Extract only digits and take first 4
  const digits = accountNumber.replace(/\D/g, '');
  return digits.substring(0, 4);
}

/**
 * Normalize date for comparison
 * - Handles various date formats: "2020-01-15", "01/15/2020", "Jan 15 2020"
 * - Returns standardized YYYY-MM-DD format or empty string
 */
export function normalizeDate(dateStr: string): string {
  if (!dateStr) return '';
  
  try {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return '';
    
    return date.toISOString().split('T')[0]; // YYYY-MM-DD format
  } catch {
    return '';
  }
}

/**
 * Check if two tradelines match based on fuzzy criteria
 */
export function isTradelineMatch(
  incomingTradeline: ParsedTradeline,
  existingTradeline: ParsedTradeline
): FuzzyMatchResult {
  const normalizedIncomingCreditor = normalizeCreditorName(incomingTradeline.creditor_name);
  const normalizedExistingCreditor = normalizeCreditorName(existingTradeline.creditor_name);
  
  const incomingAccountPrefix = extractAccountPrefix(incomingTradeline.account_number);
  const existingAccountPrefix = extractAccountPrefix(existingTradeline.account_number);
  
  const incomingDate = normalizeDate(incomingTradeline.date_opened);
  const existingDate = normalizeDate(existingTradeline.date_opened);
  
  // Check matching criteria
  const creditorNameMatch = normalizedIncomingCreditor === normalizedExistingCreditor;
  
  // Handle "Unknown" account numbers - if both are "Unknown", consider it a match
  const bothAccountsUnknown = incomingTradeline.account_number === 'Unknown' && existingTradeline.account_number === 'Unknown';
  const accountNumberMatch = bothAccountsUnknown || (incomingAccountPrefix === existingAccountPrefix && incomingAccountPrefix.length === 4);
  
  const dateOpenedMatch = incomingDate === existingDate && incomingDate !== '';
  
  // Credit bureau must match for duplicates - same account from different bureaus are separate records
  const creditBureauMatch = incomingTradeline.credit_bureau === existingTradeline.credit_bureau;
  
  // For "Unknown" accounts, require creditor + bureau match
  // For known accounts, require creditor + account + bureau + date match  
  const isMatch = creditorNameMatch && creditBureauMatch && (
    bothAccountsUnknown ? true : (accountNumberMatch && dateOpenedMatch)
  );
  
  // Calculate confidence score (0-100)
  let confidence = 0;
  if (creditorNameMatch) confidence += 30;
  if (accountNumberMatch) confidence += 25;
  if (dateOpenedMatch) confidence += 25;
  if (creditBureauMatch) confidence += 20;
  
  return {
    isMatch,
    existingTradeline: isMatch ? existingTradeline : undefined,
    confidence,
    matchingCriteria: {
      creditorNameMatch,
      accountNumberMatch,
      dateOpenedMatch,
      creditBureauMatch
    }
  };
}

/**
 * Find existing tradeline that matches the incoming tradeline using fuzzy logic
 */
export async function findExistingTradelineByFuzzyMatch(
  incomingTradeline: ParsedTradeline,
  userId: string
): Promise<FuzzyMatchResult | null> {
  try {
    console.log('🔍 Fuzzy matching for tradeline:', {
      creditor: incomingTradeline.creditor_name,
      account: incomingTradeline.account_number,
      dateOpened: incomingTradeline.date_opened
    });
    
    // Fetch all existing tradelines for the user
    const { data: existingTradelines, error } = await supabase
      .from('tradelines')
      .select('*')
      .eq('user_id', userId);
    
    if (error) {
      console.error('Error fetching existing tradelines:', error);
      return null;
    }
    
    if (!existingTradelines || existingTradelines.length === 0) {
      console.log('📝 No existing tradelines found for user');
      return null;
    }
    
    // Check each existing tradeline for a match
    for (const existing of existingTradelines) {
      const matchResult = isTradelineMatch(incomingTradeline, existing as ParsedTradeline);
      
      if (matchResult.isMatch) {
        console.log('✅ Found fuzzy match:', {
          existingId: existing.id,
          creditor: existing.creditor_name,
          confidence: matchResult.confidence,
          criteria: matchResult.matchingCriteria
        });
        
        return matchResult;
      }
    }
    
    console.log('❌ No fuzzy match found');
    return null;
    
  } catch (error) {
    console.error('Error in fuzzy matching:', error);
    return null;
  }
}

/**
 * Merge tradeline fields, only updating empty/null fields in existing tradeline
 */
export function mergeTradelineFields(
  existingTradeline: ParsedTradeline,
  incomingTradeline: ParsedTradeline
): Partial<ParsedTradeline> {
  const updates: Partial<ParsedTradeline> = {};
  
  // Helper function to check if a field is empty/null
  const isEmpty = (value: any): boolean => {
    return value === null || value === undefined || value === '' || value === '$0';
  };
  
  // Only update fields that are empty in the existing tradeline
  if (isEmpty(existingTradeline.account_balance) && !isEmpty(incomingTradeline.account_balance)) {
    updates.account_balance = incomingTradeline.account_balance;
  }
  
  if (isEmpty(existingTradeline.account_status) && !isEmpty(incomingTradeline.account_status)) {
    updates.account_status = incomingTradeline.account_status;
  }
  
  if (isEmpty(existingTradeline.account_type) && !isEmpty(incomingTradeline.account_type)) {
    updates.account_type = incomingTradeline.account_type;
  }
  
  if (isEmpty(existingTradeline.credit_limit) && !isEmpty(incomingTradeline.credit_limit)) {
    updates.credit_limit = incomingTradeline.credit_limit;
  }
  
  if (isEmpty(existingTradeline.monthly_payment) && !isEmpty(incomingTradeline.monthly_payment)) {
    updates.monthly_payment = incomingTradeline.monthly_payment;
  }
  
  if (isEmpty(existingTradeline.credit_bureau) && !isEmpty(incomingTradeline.credit_bureau)) {
    updates.credit_bureau = incomingTradeline.credit_bureau;
  }
  
  // Update negative status if incoming has more specific information
  if (incomingTradeline.is_negative && !existingTradeline.is_negative) {
    updates.is_negative = incomingTradeline.is_negative;
  }
  
  console.log('🔄 Merging tradeline fields:', {
    existingId: existingTradeline.id,
    updatesCount: Object.keys(updates).length,
    updates: updates
  });
  
  return updates;
}

/**
 * Update specific fields of an existing tradeline
 */
export async function updateTradelineFields(
  tradelineId: string,
  updates: Partial<ParsedTradeline>
): Promise<boolean> {
  try {
    if (Object.keys(updates).length === 0) {
      console.log('📝 No updates needed for tradeline:', tradelineId);
      return true;
    }
    
    const { error } = await supabase
      .from('tradelines')
      .update(updates)
      .eq('id', tradelineId);
    
    if (error) {
      console.error('Error updating tradeline:', error);
      return false;
    }
    
    console.log('✅ Successfully updated tradeline:', tradelineId);
    return true;
    
  } catch (error) {
    console.error('Error in updateTradelineFields:', error);
    return false;
  }
}