import { EnhancedCreditReportParser } from './enhanced-credit-report-parser';
import { ParsedTradeline } from './tradeline/types';
import { processDocumentWithAI, DocumentAIResult } from './document-ai-parser';

/**
 * Enhanced Document AI Integration
 * 
 * This module integrates the EnhancedCreditReportParser with the existing 
 * Document AI processing pipeline, providing fallback and comparison capabilities.
 */
export class EnhancedDocumentAIIntegration {
  private enhancedParser: EnhancedCreditReportParser;
  
  constructor() {
    this.enhancedParser = new EnhancedCreditReportParser();
  }
  
  /**
   * Process document with enhanced parsing capabilities
   * Uses both Document AI and enhanced parsing for better results
   */
  public async processDocumentEnhanced(
    file: File, 
    userId: string,
    options: {
      useEnhancedParser?: boolean;
      fallbackToEnhanced?: boolean;
      compareResults?: boolean;
    } = {}
  ): Promise<{
    tradelines: ParsedTradeline[];
    documentResult: DocumentAIResult;
    parsingMethod: 'document-ai' | 'enhanced' | 'combined';
    comparison?: {
      documentAI: ParsedTradeline[];
      enhanced: ParsedTradeline[];
      combined: ParsedTradeline[];
    };
  }> {
    const {
      useEnhancedParser = true,
      fallbackToEnhanced = true,
      compareResults = false
    } = options;
    
    console.log('🚀 Starting enhanced document processing...', {
      fileName: file.name,
      useEnhanced: useEnhancedParser,
      fallback: fallbackToEnhanced,
      compare: compareResults
    });
    
    let documentResult: DocumentAIResult;
    let documentAITradelines: ParsedTradeline[] = [];
    let enhancedTradelines: ParsedTradeline[] = [];
    let finalTradelines: ParsedTradeline[] = [];
    let parsingMethod: 'document-ai' | 'enhanced' | 'combined' = 'document-ai';
    
    try {
      // Step 1: Try Document AI processing
      documentResult = await processDocumentWithAI(file);
      
      if (documentResult.text && documentResult.text.length > 100) {
        // Try original Document AI parsing
        try {
          const { parseTradelinesFromDocumentAI } = await import('./document-ai-parser');
          documentAITradelines = parseTradelinesFromDocumentAI(documentResult.text);
          
          // Set user_id on all tradelines
          documentAITradelines = documentAITradelines.map(tl => ({
            ...tl,
            user_id: userId
          }));
          
          console.log(`📊 Document AI extracted ${documentAITradelines.length} tradelines`);
        } catch (docAIError) {
          console.warn('⚠️ Document AI parsing failed:', docAIError);
        }
      }
      
      // Step 2: Try enhanced parsing if enabled
      if (useEnhancedParser) {
        try {
          enhancedTradelines = this.enhancedParser.parseEnhancedCreditReport(
            documentResult.text, 
            userId
          );
          console.log(`🎯 Enhanced parser extracted ${enhancedTradelines.length} tradelines`);
        } catch (enhancedError) {
          console.warn('⚠️ Enhanced parsing failed:', enhancedError);
        }
      }
      
      // Step 3: Determine final result strategy
      if (compareResults && documentAITradelines.length > 0 && enhancedTradelines.length > 0) {
        // Compare and combine results
        finalTradelines = this.combineTradelineResults(documentAITradelines, enhancedTradelines);
        parsingMethod = 'combined';
        
        return {
          tradelines: finalTradelines,
          documentResult,
          parsingMethod,
          comparison: {
            documentAI: documentAITradelines,
            enhanced: enhancedTradelines,
            combined: finalTradelines
          }
        };
      } else if (enhancedTradelines.length > documentAITradelines.length) {
        // Enhanced parser found more tradelines
        finalTradelines = enhancedTradelines;
        parsingMethod = 'enhanced';
      } else if (documentAITradelines.length > 0) {
        // Document AI found tradelines
        finalTradelines = documentAITradelines;
        parsingMethod = 'document-ai';
      } else if (fallbackToEnhanced && enhancedTradelines.length > 0) {
        // Fallback to enhanced parser
        finalTradelines = enhancedTradelines;
        parsingMethod = 'enhanced';
      }
      
      console.log(`✅ Final result: ${finalTradelines.length} tradelines using ${parsingMethod} method`);
      
      return {
        tradelines: finalTradelines,
        documentResult,
        parsingMethod
      };
      
    } catch (error) {
      console.error('❌ Enhanced document processing failed:', error);
      
      // Last resort: try enhanced parser on error
      if (fallbackToEnhanced) {
        try {
          // Try to extract text from file directly for enhanced parsing
          const text = await this.extractTextFromFile(file);
          if (text) {
            enhancedTradelines = this.enhancedParser.parseEnhancedCreditReport(text, userId);
            
            return {
              tradelines: enhancedTradelines,
              documentResult: { text, pages: 1 },
              parsingMethod: 'enhanced'
            };
          }
        } catch (fallbackError) {
          console.error('❌ Fallback parsing also failed:', fallbackError);
        }
      }
      
      throw error;
    }
  }
  
  /**
   * Combine results from Document AI and Enhanced parsing
   * Uses intelligent deduplication and field merging
   */
  private combineTradelineResults(
    documentAI: ParsedTradeline[], 
    enhanced: ParsedTradeline[]
  ): ParsedTradeline[] {
    console.log('🔄 Combining tradeline results...');
    
    const combined: ParsedTradeline[] = [];
    const processedKeys = new Set<string>();
    
    // Process Document AI results first (usually more accurate for basic fields)
    for (const docTradeline of documentAI) {
      const key = this.generateTradelineKey(docTradeline);
      
      // Look for matching enhanced tradeline
      const enhancedMatch = enhanced.find(enh => 
        this.generateTradelineKey(enh) === key ||
        this.isLikelyMatch(docTradeline, enh)
      );
      
      if (enhancedMatch) {
        // Merge the two tradelines, preferring Document AI for accuracy
        // but enhanced parser for completeness
        const merged = this.mergeTradelineData(docTradeline, enhancedMatch);
        combined.push(merged);
        processedKeys.add(key);
      } else {
        combined.push(docTradeline);
        processedKeys.add(key);
      }
    }
    
    // Add any enhanced tradelines that weren't matched
    for (const enhTradeline of enhanced) {
      const key = this.generateTradelineKey(enhTradeline);
      
      if (!processedKeys.has(key)) {
        // Check if this is truly unique
        const isDuplicate = combined.some(existing => 
          this.isLikelyMatch(existing, enhTradeline)
        );
        
        if (!isDuplicate) {
          combined.push(enhTradeline);
        }
      }
    }
    
    console.log(`🎯 Combined ${documentAI.length} + ${enhanced.length} = ${combined.length} unique tradelines`);
    return combined;
  }
  
  /**
   * Generate a unique key for tradeline matching
   */
  private generateTradelineKey(tradeline: ParsedTradeline): string {
    const creditor = tradeline.creditor_name.replace(/[^A-Z0-9]/g, '').substring(0, 20);
    const account = tradeline.account_number.replace(/[^0-9]/g, '').substring(-4);
    return `${creditor}-${account}`.toLowerCase();
  }
  
  /**
   * Check if two tradelines are likely the same account
   */
  private isLikelyMatch(t1: ParsedTradeline, t2: ParsedTradeline): boolean {
    // Exact match on key fields
    if (t1.creditor_name === t2.creditor_name && t1.account_number === t2.account_number) {
      return true;
    }
    
    // Fuzzy match on creditor name and account number
    const creditor1 = t1.creditor_name.replace(/[^A-Z0-9]/g, '');
    const creditor2 = t2.creditor_name.replace(/[^A-Z0-9]/g, '');
    
    const account1 = t1.account_number.replace(/[^0-9]/g, '');
    const account2 = t2.account_number.replace(/[^0-9]/g, '');
    
    // Check for partial matches
    const creditorSimilar = creditor1.includes(creditor2.substring(0, 8)) || 
                           creditor2.includes(creditor1.substring(0, 8));
    
    const accountSimilar = account1.length >= 4 && account2.length >= 4 && 
                          (account1.substring(-4) === account2.substring(-4));
    
    return creditorSimilar && accountSimilar;
  }
  
  /**
   * Merge two tradeline objects, preferring more complete data
   */
  private mergeTradelineData(primary: ParsedTradeline, secondary: ParsedTradeline): ParsedTradeline {
    return {
      id: primary.id,
      user_id: primary.user_id || secondary.user_id,
      creditor_name: primary.creditor_name || secondary.creditor_name,
      account_number: primary.account_number || secondary.account_number,
      account_balance: primary.account_balance || secondary.account_balance,
      account_status: primary.account_status || secondary.account_status,
      account_type: primary.account_type || secondary.account_type,
      date_opened: primary.date_opened || secondary.date_opened,
      credit_limit: primary.credit_limit || secondary.credit_limit,
      credit_bureau: primary.credit_bureau || secondary.credit_bureau,
      monthly_payment: primary.monthly_payment || secondary.monthly_payment,
      is_negative: primary.is_negative || secondary.is_negative, // Prefer positive identification
      dispute_count: Math.max(primary.dispute_count || 0, secondary.dispute_count || 0),
      created_at: primary.created_at || secondary.created_at
    };
  }
  
  /**
   * Extract text from file for fallback processing
   */
  private async extractTextFromFile(file: File): Promise<string | null> {
    try {
      if (file.type === 'text/plain') {
        return await file.text();
      }
      
      // For other file types, we'd need more sophisticated extraction
      // This is a placeholder for basic text extraction
      console.warn('Advanced text extraction not implemented for file type:', file.type);
      return null;
      
    } catch (error) {
      console.error('Failed to extract text from file:', error);
      return null;
    }
  }
  
  /**
   * Generate parsing quality metrics
   */
  public generateParsingMetrics(
    tradelines: ParsedTradeline[],
    documentResult: DocumentAIResult,
    parsingMethod: string
  ): {
    totalTradelines: number;
    negativeItems: number;
    completenessScore: number;
    confidenceScore: number;
    parsingMethod: string;
    recommendations: string[];
  } {
    const totalTradelines = tradelines.length;
    const negativeItems = tradelines.filter(t => t.is_negative).length;
    
    // Calculate completeness score based on filled fields
    const fieldCounts = tradelines.map(t => {
      const fields = [
        t.creditor_name, t.account_number, t.account_balance, 
        t.account_status, t.account_type, t.date_opened, 
        t.credit_limit, t.monthly_payment
      ];
      return fields.filter(field => field && field.trim() !== '').length;
    });
    
    const avgFieldsPerTradeline = fieldCounts.reduce((a, b) => a + b, 0) / Math.max(totalTradelines, 1);
    const completenessScore = Math.round((avgFieldsPerTradeline / 8) * 100);
    
    // Estimate confidence based on parsing method and completeness
    let confidenceScore = 0;
    switch (parsingMethod) {
      case 'document-ai':
        confidenceScore = Math.min(90, completenessScore + 10);
        break;
      case 'enhanced':
        confidenceScore = Math.min(85, completenessScore + 5);
        break;
      case 'combined':
        confidenceScore = Math.min(95, completenessScore + 15);
        break;
    }
    
    // Generate recommendations
    const recommendations: string[] = [];
    
    if (totalTradelines === 0) {
      recommendations.push('No tradelines found. Verify this is a credit report.');
    } else if (totalTradelines < 3) {
      recommendations.push('Few tradelines found. Document may be incomplete or low quality.');
    }
    
    if (completenessScore < 50) {
      recommendations.push('Low completeness score. Consider manual review of extracted data.');
    }
    
    if (parsingMethod === 'enhanced') {
      recommendations.push('Used fallback parsing. Document AI may not be available.');
    }
    
    if (negativeItems > totalTradelines * 0.7) {
      recommendations.push('High percentage of negative items detected. Verify accuracy.');
    }
    
    return {
      totalTradelines,
      negativeItems,
      completenessScore,
      confidenceScore,
      parsingMethod,
      recommendations
    };
  }
}

// Export singleton instance for easy use
export const enhancedDocumentAI = new EnhancedDocumentAIIntegration();