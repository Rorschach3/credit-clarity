import { extract as fuzzyExtract, token_set_ratio } from 'fuzzball';
import { knownCreditors } from './knownCreditors';

/**
 * Standardizes creditor names using fuzzy matching against known creditors
 * @param extractedName Raw creditor name extracted from credit report
 * @returns Standardized creditor name
 */
export function standardizeCreditorName(extractedName: string): string {
  if (!extractedName || extractedName === null) {
    return extractedName;
  }
  
  const matches = fuzzyExtract(extractedName.toUpperCase(), knownCreditors, {
    scorer: token_set_ratio,
    limit: 1,
    cutoff: 75 // Minimum match score (0-100)
  });
  
  return matches.length > 0 ? matches[0][0] : extractedName;
}