/**
 * Enhanced Credit Report Parsing - Usage Examples
 * 
 * This file demonstrates how to use the new enhanced parsing system
 * with section anchors, regex-driven extraction, payment history normalization,
 * and account delimiter heuristics.
 */

import { EnhancedCreditReportParser } from './enhanced-credit-report-parser';
import { enhancedDocumentAI } from './enhanced-document-ai-integration';
import { ParsedTradeline } from './tradeline/types';

/**
 * Example 1: Basic Enhanced Parsing
 */
export async function basicEnhancedParsing(file: File, userId: string): Promise<ParsedTradeline[]> {
  console.log('📋 Example 1: Basic Enhanced Parsing');
  
  try {
    const result = await enhancedDocumentAI.processDocumentEnhanced(file, userId, {
      useEnhancedParser: true,
      fallbackToEnhanced: true,
      compareResults: false
    });
    
    console.log(`✅ Parsed ${result.tradelines.length} tradelines using ${result.parsingMethod}`);
    
    // Generate quality metrics
    const metrics = enhancedDocumentAI.generateParsingMetrics(
      result.tradelines,
      result.documentResult,
      result.parsingMethod
    );
    
    console.log('📊 Parsing Metrics:', metrics);
    
    return result.tradelines;
    
  } catch (error) {
    console.error('❌ Basic enhanced parsing failed:', error);
    throw error;
  }
}

/**
 * Example 2: Comparative Parsing (Document AI vs Enhanced)
 */
export async function comparativeParsing(file: File, userId: string) {
  console.log('🔄 Example 2: Comparative Parsing');
  
  try {
    const result = await enhancedDocumentAI.processDocumentEnhanced(file, userId, {
      useEnhancedParser: true,
      fallbackToEnhanced: true,
      compareResults: true // Enable comparison mode
    });
    
    if (result.comparison) {
      console.log('📊 Parsing Comparison Results:');
      console.log(`  Document AI: ${result.comparison.documentAI.length} tradelines`);
      console.log(`  Enhanced: ${result.comparison.enhanced.length} tradelines`);
      console.log(`  Combined: ${result.comparison.combined.length} tradelines`);
      
      // Show quality comparison
      const docAIMetrics = enhancedDocumentAI.generateParsingMetrics(
        result.comparison.documentAI,
        result.documentResult,
        'document-ai'
      );
      
      const enhancedMetrics = enhancedDocumentAI.generateParsingMetrics(
        result.comparison.enhanced,
        result.documentResult,
        'enhanced'
      );
      
      console.log('🎯 Quality Comparison:');
      console.log(`  Document AI Completeness: ${docAIMetrics.completenessScore}%`);
      console.log(`  Enhanced Completeness: ${enhancedMetrics.completenessScore}%`);
      
      return {
        final: result.tradelines,
        comparison: result.comparison,
        metrics: { docAI: docAIMetrics, enhanced: enhancedMetrics }
      };
    }
    
    return { final: result.tradelines };
    
  } catch (error) {
    console.error('❌ Comparative parsing failed:', error);
    throw error;
  }
}

/**
 * Example 3: Section-Specific Parsing 
 */
export async function sectionSpecificParsing(creditReportText: string, userId: string) {
  console.log('📋 Example 3: Section-Specific Parsing');
  
  const parser = new EnhancedCreditReportParser();
  
  // Step 1: Segment the document
  const segments = parser.segmentBySectionAnchors(creditReportText);
  
  console.log('🔍 Document Segments:');
  console.log(`  Negative Items: ${segments.negativeItems ? 'Found' : 'Not found'}`);
  console.log(`  Good Standing: ${segments.goodStanding ? 'Found' : 'Not found'}`);
  console.log(`  Inquiries: ${segments.inquiries ? 'Found' : 'Not found'}`);
  
  // Step 2: Parse each section separately
  const results = {
    negativeItems: [] as ParsedTradeline[],
    goodStanding: [] as ParsedTradeline[],
    all: [] as ParsedTradeline[]
  };
  
  if (segments.negativeItems) {
    const negativeBlocks = parser.parseAccountBlocks(segments.negativeItems);
    console.log(`🔴 Found ${negativeBlocks.length} negative account blocks`);
    
    for (const block of negativeBlocks) {
      const details = parser.extractAccountDetails(block);
      if (parser['isValidTradeline'](details)) {
        const tradeline = parser['createTradeline'](details, userId, true);
        if (tradeline) results.negativeItems.push(tradeline);
      }
    }
  }
  
  if (segments.goodStanding) {
    const goodBlocks = parser.parseAccountBlocks(segments.goodStanding);
    console.log(`🟢 Found ${goodBlocks.length} good standing account blocks`);
    
    for (const block of goodBlocks) {
      const details = parser.extractAccountDetails(block);
      if (parser['isValidTradeline'](details)) {
        const tradeline = parser['createTradeline'](details, userId, false);
        if (tradeline) results.goodStanding.push(tradeline);
      }
    }
  }
  
  results.all = [...results.negativeItems, ...results.goodStanding];
  
  console.log('📊 Section Parsing Results:');
  console.log(`  Negative Items: ${results.negativeItems.length}`);
  console.log(`  Good Standing: ${results.goodStanding.length}`);
  console.log(`  Total: ${results.all.length}`);
  
  return results;
}

/**
 * Example 4: Payment History Analysis
 */
export function paymentHistoryAnalysis(creditReportText: string) {
  console.log('📅 Example 4: Payment History Analysis');
  
  const parser = new EnhancedCreditReportParser();
  
  // Look for payment history sections in the text
  const paymentHistoryPatterns = [
    /Payment\s+History[\s\S]*?(?=Account|$)/gi,
    /Monthly\s+Payment\s+Status[\s\S]*?(?=Account|$)/gi,
    /\d{4}[\s\S]*?(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[\s\S]*?(?:[A-Z]{2,4}|\d{2,3})/gi
  ];
  
  const paymentHistories: Array<{month: string, status: string}> = [];
  
  paymentHistoryPatterns.forEach(pattern => {
    const matches = creditReportText.match(pattern);
    if (matches) {
      matches.forEach(match => {
        const history = parser.normalizePaymentHistory(match);
        paymentHistories.push(...history);
      });
    }
  });
  
  // Analyze payment patterns
  const analysis = {
    totalEntries: paymentHistories.length,
    negativeEntries: paymentHistories.filter(h => 
      h.status.includes('Late') || 
      h.status.includes('Charge Off') || 
      h.status.includes('Collection')
    ).length,
    recentTrend: 'Unknown' as 'Improving' | 'Declining' | 'Stable' | 'Unknown'
  };
  
  // Determine recent trend (last 6 months)
  const recentEntries = paymentHistories
    .sort((a, b) => b.month.localeCompare(a.month))
    .slice(0, 6);
  
  if (recentEntries.length >= 3) {
    const recentNegative = recentEntries.filter(h => 
      !h.status.includes('On-time') && !h.status.includes('Current')
    ).length;
    
    if (recentNegative === 0) {
      analysis.recentTrend = 'Improving';
    } else if (recentNegative >= recentEntries.length * 0.7) {
      analysis.recentTrend = 'Declining';
    } else {
      analysis.recentTrend = 'Stable';
    }
  }
  
  console.log('📊 Payment History Analysis:', analysis);
  console.log('📅 Sample Entries:', paymentHistories.slice(0, 5));
  
  return {
    paymentHistories,
    analysis
  };
}

/**
 * Example 5: Advanced Account Delimiter Detection
 */
export function advancedAccountDelimiterDemo(creditReportText: string) {
  console.log('🔍 Example 5: Advanced Account Delimiter Detection');
  
  const parser = new EnhancedCreditReportParser();
  
  // Test different delimiter patterns
  const lines = creditReportText.split('\\n');
  const delimiters: Array<{line: string, index: number, isDelimiter: boolean}> = [];
  
  lines.forEach((line, index) => {
    const isDelimiter = parser['isAccountDelimiter'](line.trim());
    if (isDelimiter) {
      delimiters.push({
        line: line.trim(),
        index,
        isDelimiter: true
      });
    }
  });
  
  console.log(`🎯 Found ${delimiters.length} account delimiters:`);
  delimiters.forEach((delimiter, i) => {
    console.log(`  ${i + 1}. Line ${delimiter.index}: "${delimiter.line.substring(0, 50)}..."`);
  });
  
  // Test account block parsing
  const accountBlocks = parser.parseAccountBlocks(creditReportText);
  
  console.log('📋 Account Block Analysis:');
  console.log(`  Total blocks found: ${accountBlocks.length}`);
  
  accountBlocks.forEach((block, index) => {
    const details = parser.extractAccountDetails(block);
    console.log(`  Block ${index + 1}:`, {
      creditor: details.creditor_name || 'Unknown',
      account: details.account_number || 'Unknown',
      status: details.account_status || 'Unknown',
      valid: parser['isValidTradeline'](details)
    });
  });
  
  return {
    delimiters,
    accountBlocks: accountBlocks.length,
    validBlocks: accountBlocks.filter(block => {
      const details = parser.extractAccountDetails(block);
      return parser['isValidTradeline'](details);
    }).length
  };
}

/**
 * Example 6: Complete Workflow with Error Handling
 */
export async function completeEnhancedWorkflow(file: File, userId: string) {
  console.log('🚀 Example 6: Complete Enhanced Workflow');
  
  try {
    // Step 1: Process document with all options
    const result = await enhancedDocumentAI.processDocumentEnhanced(file, userId, {
      useEnhancedParser: true,
      fallbackToEnhanced: true,
      compareResults: true
    });
    
    // Step 2: Generate comprehensive metrics
    const metrics = enhancedDocumentAI.generateParsingMetrics(
      result.tradelines,
      result.documentResult,
      result.parsingMethod
    );
    
    // Step 3: Analyze results
    const analysis = {
      fileName: file.name,
      fileSize: file.size,
      fileType: file.type,
      processingMethod: result.parsingMethod,
      documentPages: result.documentResult.pages,
      textLength: result.documentResult.text.length,
      tradelineStats: {
        total: result.tradelines.length,
        negative: result.tradelines.filter(t => t.is_negative).length,
        positive: result.tradelines.filter(t => !t.is_negative).length,
        creditCards: result.tradelines.filter(t => t.account_type === 'credit_card').length,
        loans: result.tradelines.filter(t => t.account_type?.includes('loan')).length,
        collections: result.tradelines.filter(t => t.account_type === 'collection').length
      },
      qualityMetrics: metrics,
      recommendations: metrics.recommendations
    };
    
    console.log('📊 Complete Analysis:', analysis);
    
    // Step 4: Return structured result
    return {
      success: true,
      tradelines: result.tradelines,
      analysis,
      comparison: result.comparison,
      warnings: metrics.recommendations.length > 0 ? metrics.recommendations : undefined
    };
    
  } catch (error) {
    console.error('❌ Complete workflow failed:', error);
    
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      tradelines: [],
      analysis: null
    };
  }
}