// Enhanced fuzzy matching utilities for tradeline deduplication
import { ParsedTradeline, DatabaseTradeline } from '@/utils/tradelineParser';
import { supabase } from '@/integrations/supabase/client';

export interface FuzzyMatchResult {
  isMatch: boolean;
  existingTradeline?: ParsedTradeline;
  confidence: number;
  matchingCriteria: {
    creditorNameScore: number;
    accountNumberScore: number; 
    dateOpenedMatch: boolean;
    creditBureauMatch: boolean;
    overallScore: number;
    accountNumberMatch?: boolean;
    creditorNameMatch?: boolean;
  };
}

/**
 * Calculate Levenshtein distance between two strings
 */
function levenshteinDistance(str1: string, str2: string): number {
  const matrix = Array(str2.length + 1).fill(null).map(() => Array(str1.length + 1).fill(null));
  
  for (let i = 0; i <= str1.length; i++) matrix[0][i] = i;
  for (let j = 0; j <= str2.length; j++) matrix[j][0] = j;
  
  for (let j = 1; j <= str2.length; j++) {
    for (let i = 1; i <= str1.length; i++) {
      const indicator = str1[i - 1] === str2[j - 1] ? 0 : 1;
      matrix[j][i] = Math.min(
        matrix[j][i - 1] + 1,     // deletion
        matrix[j - 1][i] + 1,     // insertion
        matrix[j - 1][i - 1] + indicator // substitution
      );
    }
  }
  
  return matrix[str2.length][str1.length];
}

/**
 * Calculate similarity percentage between two strings (0-100)
 */
function calculateSimilarity(str1: string, str2: string): number {
  if (!str1 || !str2) return 0;
  if (str1 === str2) return 100;
  
  const maxLength = Math.max(str1.length, str2.length);
  if (maxLength === 0) return 100;
  
  const distance = levenshteinDistance(str1, str2);
  return Math.round(((maxLength - distance) / maxLength) * 100);
}

/**
 * Extract account number prefix for matching
 */
export function extractAccountPrefix(accountNumber: string, length: number = 4): string {
  if (!accountNumber) return '';
  const digits = accountNumber.replace(/\D/g, '');
  return digits.substring(0, length);
}

/**
 * Enhanced creditor name normalization - preserves important identifiers
 */
export function normalizeCreditorName(name: string): string {
  if (!name) return '';
  
  let normalized = name
    .trim()
    .toLowerCase()
    .replace(/\bn\.?a\.?\b/g, 'na')
    .replace(/[^\w\s]/g, ' ')
    .replace(/\s+/g, ' ');

  const wordsToRemove = new Set([
    'bank',
    'card',
    'corp',
    'corporation',
    'company',
    'inc',
    'llc',
    'financial'
  ]);

  let words = normalized.split(' ').filter(Boolean);
  words = words.filter(word => !wordsToRemove.has(word));

  if (words[words.length - 1] === 'na') {
    const trimmed = words.slice(0, -1);
    if (trimmed.length === 1 && trimmed[0].length > 2) {
      words = trimmed;
    }
  }

  normalized = words.join(' ');

  return normalized.trim();
}

/**
 * Enhanced account number comparison with flexible matching
 */
export function compareAccountNumbers(account1: string, account2: string): number {
  if (!account1 || !account2) return 0;
  if (account1 === account2) return 100;

  // Extract digits only
  const digits1 = account1.replace(/\D/g, '');
  const digits2 = account2.replace(/\D/g, '');

  if (!digits1 || !digits2) return 0;
  if (digits1 === digits2) return 100;

  const prefix1 = digits1.substring(0, 4);
  const prefix2 = digits2.substring(0, 4);
  if (prefix1 && prefix2 && prefix1 === prefix2) return 100;

  return 0;
}

/**
 * Enhanced creditor name comparison with multiple matching strategies
 */
export function compareCreditorNames(name1: string, name2: string): number {
  const normalized1 = normalizeCreditorName(name1);
  const normalized2 = normalizeCreditorName(name2);
  
  if (!normalized1 || !normalized2) return 0;
  if (normalized1 === normalized2) return 100;
  
  // Split into tokens for partial matching
  const tokens1 = normalized1.split(' ').filter(t => t.length > 1);
  const tokens2 = normalized2.split(' ').filter(t => t.length > 1);
  
  // Exact token matches
  const commonTokens = tokens1.filter(token => tokens2.includes(token));
  const tokenMatchScore = commonTokens.length > 0 ? 
    (commonTokens.length / Math.max(tokens1.length, tokens2.length)) * 100 : 0;
  
  // Check for substring containment (handles "SIMPLE" in "ACIMA DIGITAL FKA SIMPLE")
  const containmentScore1 = tokens1.some(token => normalized2.includes(token)) ? 60 : 0;
  const containmentScore2 = tokens2.some(token => normalized1.includes(token)) ? 60 : 0;
  const containmentScore = Math.max(containmentScore1, containmentScore2);
  
  // Fuzzy string similarity
  const similarityScore = calculateSimilarity(normalized1, normalized2);
  
  // Return the highest score from different matching strategies
  const finalScore = Math.max(tokenMatchScore, containmentScore, similarityScore);
  
  console.log(`🔍 Creditor comparison: "${name1}" vs "${name2}" = ${finalScore}%`, {
    normalized1,
    normalized2,
    tokenMatchScore,
    containmentScore,
    similarityScore,
    finalScore
  });
  
  return finalScore;
}

/**
 * Normalize date for comparison with flexible parsing
 */
export function normalizeDate(dateStr: string): string {
  if (!dateStr) return '';
  
  try {
    // Handle various date formats
    let cleanDate = dateStr.trim();
    
    // Handle MM/DD/YYYY format
    if (cleanDate.match(/^\d{1,2}\/\d{1,2}\/\d{4}$/)) {
      const [month, day, year] = cleanDate.split('/');
      cleanDate = `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
    }
    
    const date = new Date(cleanDate);
    if (isNaN(date.getTime())) return '';
    
    return date.toISOString().split('T')[0]; // YYYY-MM-DD format
  } catch {
    return '';
  }
}

// Define threshold interface
interface MatchingThresholds {
  creditorNameMinScore: number;
  accountNumberMinScore: number;
  overallMinScore: number;
  requireCreditBureauMatch: boolean;
  requireDateMatch: boolean;
}

/**
 * Enhanced tradeline matching with configurable thresholds
 */
export function isTradelineMatch(
  incomingTradeline: ParsedTradeline,
  existingTradeline: ParsedTradeline,
  customThresholds?: Partial<MatchingThresholds>
): FuzzyMatchResult {
  const thresholds: MatchingThresholds = {
    creditorNameMinScore: 70,
    accountNumberMinScore: 100,
    overallMinScore: 100,
    requireCreditBureauMatch: false,
    requireDateMatch: true,
    ...customThresholds
  };

  const creditorNameScore = compareCreditorNames(
    incomingTradeline.creditor_name,
    existingTradeline.creditor_name
  );

  const accountNumberScore = compareAccountNumbers(
    incomingTradeline.account_number || '',
    existingTradeline.account_number || ''
  );

  const incomingDate = normalizeDate(incomingTradeline.date_opened ?? '');
  const existingDate = normalizeDate(existingTradeline.date_opened ?? '');
  const dateOpenedMatch = incomingDate !== '' && incomingDate === existingDate;

  const creditBureauMatch = !thresholds.requireCreditBureauMatch ||
    incomingTradeline.credit_bureau === existingTradeline.credit_bureau;

  const creditorNameMatch = creditorNameScore >= thresholds.creditorNameMinScore;
  const accountNumberMatch = accountNumberScore >= thresholds.accountNumberMinScore;

  let overallScore = 0;
  if (creditorNameMatch) overallScore += 40;
  if (accountNumberMatch) overallScore += 30;
  if (dateOpenedMatch) overallScore += 30;

  const isMatch = overallScore >= thresholds.overallMinScore &&
    creditorNameMatch &&
    accountNumberMatch &&
    dateOpenedMatch &&
    creditBureauMatch;
  
  const result = {
    isMatch,
    existingTradeline: isMatch ? existingTradeline : undefined,
    confidence: Math.round(overallScore),
    matchingCriteria: {
      creditorNameScore,
      accountNumberScore,
      dateOpenedMatch,
      creditBureauMatch,
      overallScore,
      accountNumberMatch,
      creditorNameMatch
    }
  };
  
  console.log(`🎯 Tradeline match result:`, {
    incoming: `${incomingTradeline.creditor_name} (${incomingTradeline.account_number})`,
    existing: `${existingTradeline.creditor_name} (${existingTradeline.account_number})`,
    ...result
  });
  
  return result;
}

/**
 * Sanitize Supabase data to match ParsedTradeline type
 */
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
    credit_bureau: dbTradeline.credit_bureau || 'Unknown',
    monthly_payment: dbTradeline.monthly_payment || '$0',
  };
}

/**
 * Optimized database query to reduce candidates before fuzzy matching
 */
export async function findCandidateTradelines(
  incomingTradeline: ParsedTradeline,
  userId: string
): Promise<ParsedTradeline[]> {
  try {
    // Extract key terms from creditor name for pre-filtering
    const normalizedCreditor = normalizeCreditorName(incomingTradeline.creditor_name);
    const searchTerms = normalizedCreditor.split(' ').filter(term => term.length > 2);
    
    if (searchTerms.length === 0) {
      // Fallback to all tradelines if no good search terms
      const { data, error } = await supabase
        .from('tradelines')
        .select('*')
        .eq('user_id', userId);
        
      if (error) throw error;
      return (data || []).map(sanitizeDatabaseTradeline);
    }
    
    // Use multiple search strategies
    const candidates = new Map<string, DatabaseTradeline>();
    
    // Strategy 1: Search by main creditor terms
    for (const term of searchTerms.slice(0, 3)) { // Limit to first 3 terms for performance
      const { data, error } = await supabase
        .from('tradelines')
        .select('*')
        .eq('user_id', userId)
        .ilike('creditor_name', `%${term}%`);
        
      if (!error && data) {
        data.forEach(item => candidates.set(item.id, item as DatabaseTradeline));
      }
    }
    
    // Strategy 2: Exact creditor name search (case insensitive)
    const { data: exactMatches, error: exactError } = await supabase
      .from('tradelines')
      .select('*')
      .eq('user_id', userId)
      .ilike('creditor_name', incomingTradeline.creditor_name);
      
    if (!exactError && exactMatches) {
      exactMatches.forEach(item => candidates.set(item.id, item as DatabaseTradeline));
    }
    
    // Strategy 3: Account number prefix search (if available)
    const accountPrefix = extractAccountPrefix(incomingTradeline.account_number, 4);
    if (accountPrefix && accountPrefix.length === 4) {
      const { data: accountMatches, error: accountError } = await supabase
        .from('tradelines')
        .select('*')
        .eq('user_id', userId)
        .ilike('account_number', `${accountPrefix}%`);
        
      if (!accountError && accountMatches) {
        accountMatches.forEach(item => candidates.set(item.id, item as DatabaseTradeline));
      }
    }
    
    const result = Array.from(candidates.values()).map(sanitizeDatabaseTradeline);
    console.log(`📋 Found ${result.length} candidate tradelines for fuzzy matching`);
    
    return result;
    
  } catch (error) {
    console.error('Error finding candidate tradelines:', error);
    // Fallback to all tradelines
    const { data } = await supabase
      .from('tradelines')
      .select('*')
      .eq('user_id', userId);
      
    return (data || []).map(sanitizeDatabaseTradeline);
  }
}

/**
 * Enhanced fuzzy matching with optimized database queries
 */
export async function findExistingTradelineByFuzzyMatch(
  incomingTradeline: ParsedTradeline,
  userId: string,
  customThresholds?: Partial<MatchingThresholds>
): Promise<FuzzyMatchResult | null> {
  try {
    console.log('🔍 Enhanced fuzzy matching for tradeline:', {
      creditor: incomingTradeline.creditor_name,
      account: incomingTradeline.account_number,
      dateOpened: incomingTradeline.date_opened
    });
    
    // Get optimized candidate list instead of all tradelines
    const candidateTradelines = await findCandidateTradelines(incomingTradeline, userId);
    
    if (candidateTradelines.length === 0) {
      console.log('📝 No candidate tradelines found for user');
      return null;
    }
    
    console.log(`🎯 Checking ${candidateTradelines.length} candidates for matches`);
    
    // Find the best match
    let bestMatch: FuzzyMatchResult | null = null;
    
    for (const candidate of candidateTradelines) {
      const matchResult = isTradelineMatch(incomingTradeline, candidate, customThresholds);
      
      if (matchResult.isMatch) {
        // Keep the highest confidence match
        if (!bestMatch || matchResult.confidence > bestMatch.confidence) {
          bestMatch = matchResult;
        }
      }
    }
    
    if (bestMatch) {
      console.log('✅ Found enhanced fuzzy match:', {
        existingId: bestMatch.existingTradeline?.id,
        creditor: bestMatch.existingTradeline?.creditor_name,
        confidence: bestMatch.confidence,
        criteria: bestMatch.matchingCriteria
      });
    } else {
      console.log('❌ No fuzzy match found with enhanced algorithm');
    }
    
    return bestMatch;
    
  } catch (error) {
    console.error('Error in enhanced fuzzy matching:', error);
    return null;
  }
}

// Type for fields that can be empty/null/default
type FieldValue = string | null | undefined | boolean | number;

/**
 * Enhanced merge function with smarter field prioritization
 */
export function mergeTradelineFields(
  existingTradeline: ParsedTradeline,
  incomingTradeline: ParsedTradeline
): Partial<ParsedTradeline> {
  const updates: Partial<ParsedTradeline> = {};
  
  // Helper function to check if a field is empty/null/default
  const isEmpty = (value: FieldValue): boolean => {
    if (value === null || value === undefined) return true;
    
    if (typeof value === 'string') {
      return value === '' || value === '$0' || value === 'Unknown' || value === '0' || value.trim() === '';
    }
    
    if (typeof value === 'number') {
      return value === 0;
    }
    
    return false;
  };
  
  // Helper function to determine if incoming value is better
  const isBetterValue = (existing: FieldValue, incoming: FieldValue): boolean => {
    if (isEmpty(existing) && !isEmpty(incoming)) return true;
    
    // Prefer more specific/detailed values for strings
    if (typeof existing === 'string' && typeof incoming === 'string') {
      return incoming.length > existing.length && !isEmpty(incoming);
    }
    
    return false;
  };
  
  // Define updatable string fields - these are the fields we want to merge
  const stringFieldsToCheck: Array<keyof Pick<ParsedTradeline, 
    'account_balance' | 'account_status' | 'account_type' | 
    'credit_limit' | 'monthly_payment' | 'credit_bureau' | 'date_opened'
  >> = [
    'account_balance',
    'account_status', 
    'account_type',
    'credit_limit',
    'monthly_payment',
    'credit_bureau',
    'date_opened'
  ];
  
  // Type-safe field updates
  const updateOnlyIfEmpty = new Set<keyof ParsedTradeline>([
    'account_balance',
    'account_status',
    'credit_bureau'
  ]);

  stringFieldsToCheck.forEach(field => {
    const existingValue = existingTradeline[field];
    const incomingValue = incomingTradeline[field];

    if (updateOnlyIfEmpty.has(field)) {
      if (isEmpty(existingValue) && !isEmpty(incomingValue)) {
        updates[field] = incomingValue as string | undefined;
      }
      return;
    }

    if (isBetterValue(existingValue, incomingValue)) {
      const value = incomingValue;
      if (value !== null) {
        updates[field] = value as string | undefined;
      }
    }
  });
  
  // Update negative status if incoming has more specific information
  if (incomingTradeline.is_negative && !existingTradeline.is_negative) {
    updates.is_negative = incomingTradeline.is_negative;
  }
  
  // Increment dispute count if incoming shows disputes
  if (incomingTradeline.dispute_count > existingTradeline.dispute_count) {
    updates.dispute_count = incomingTradeline.dispute_count;
  }
  
  console.log('🔄 Enhanced merging tradeline fields:', {
    existingId: existingTradeline.id,
    updatesCount: Object.keys(updates).length,
    updates: updates
  });
  
  return updates;
}

/**
 * Enhanced update function with validation
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
    
    // Validate updates before applying - only include non-empty values
    const validUpdates: Record<string, string | number | boolean> = {};    
    // Type-safe iteration over updates
    (Object.keys(updates) as Array<keyof ParsedTradeline>).forEach(key => {
      const value = updates[key];
      if (value !== null && value !== undefined && value !== '') {
        validUpdates[key as string] = value;
      }
    });
    
    if (Object.keys(validUpdates).length === 0) {
      console.log('📝 No valid updates for tradeline:', tradelineId);
      return true;
    }
    
    const { error } = await supabase
      .from('tradelines')
      .update(validUpdates)
      .eq('id', tradelineId);
    
    if (error) {
      console.error('Error updating tradeline:', error);
      return false;
    }
    
    console.log('✅ Successfully updated tradeline:', tradelineId, 'with fields:', Object.keys(validUpdates));
    return true;
    
  } catch (error) {
    console.error('Error in updateTradelineFields:', error);
    return false;
  }
}
