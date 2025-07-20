// Non-hook utility functions for credit report processing
import { ParsedTradeline } from '@/utils/tradelineParser';

// Processing progress interface
export interface ProcessingProgress {
  step: string;
  progress: number;
  message: string;
}

// Pure utility function for OCR processing (no hooks)
export const processWithOCR = async (file: File, userId?: string): Promise<string> => {
  // BULLETPROOF FILE VALIDATION
  if (!(file instanceof File)) {
    console.error('❌ NOT A FILE INSTANCE:', typeof file, file);
    throw new Error(`Expected File instance, got ${typeof file}`);
  }
  
  console.log('✅ OCR File validation passed:', {
    name: file.name,
    type: file.type, 
    size: file.size,
    isFile: file instanceof File,
    constructor: file.constructor.name
  });
  
  // BULLETPROOF FORMDATA
  const formData = new FormData();
  formData.append('file', file); // Raw File object, no JSON, no toString()
  if (userId) {
    formData.append('user_id', userId);
  }
  
  try {
    const response = await fetch('http://localhost:8000/process-credit-report', {
      method: 'POST',
      body: formData
      // NO HEADERS - Let browser set multipart/form-data with boundary
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ OCR Backend error:', response.status, errorText);
      throw new Error(`Backend error ${response.status}: ${errorText}`);
    }
    
    const result = await response.json();
    console.log('✅ OCR Success:', result);
    
    return result.extracted_text || '';
  } catch (error) {
    console.error('❌ OCR Request failed:', error);
    throw error;
  }
};

// Pure utility function for AI processing (no hooks)
export const processWithAI = async (file: File, userId?: string): Promise<{ tradelines: ParsedTradeline[] }> => {
  // BULLETPROOF FILE VALIDATION
  if (!(file instanceof File)) {
    console.error('❌ NOT A FILE INSTANCE:', typeof file, file);
    throw new Error(`Expected File instance, got ${typeof file}`);
  }
  
  console.log('✅ File validation passed:', {
    name: file.name,
    type: file.type, 
    size: file.size,
    isFile: file instanceof File,
    constructor: file.constructor.name
  });
  
  // BULLETPROOF FORMDATA
  const formData = new FormData();
  formData.append('file', file); // Raw File object, no JSON, no toString()
  if (userId) {
    formData.append('user_id', userId);
  }
  
  // Debug FormData contents
  console.log('📦 FormData entries:');
  for (const [key, value] of formData.entries()) {
    console.log(`  ${key}:`, value instanceof File ? `File(${value.name})` : value);
  }
  
  try {
    const response = await fetch('http://localhost:8000/process-credit-report', {
      method: 'POST',
      body: formData
      // NO HEADERS - Let browser set multipart/form-data with boundary
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Backend error:', response.status, errorText);
      throw new Error(`Backend error ${response.status}: ${errorText}`);
    }
    
    const result = await response.json();
    console.log('✅ Success:', result);
    
    return { tradelines: result.tradelines || [] };
  } catch (error) {
    console.error('❌ Request failed:', error);
    throw error;
  }
};

// Extract keywords from text content
export const extractKeywordsFromText = (textContent: string): string[] => {
  if (!textContent) return [];
  
  const creditKeywords = [
    'payment history', 'credit utilization', 'length of credit history',
    'credit mix', 'new credit', 'delinquent', 'collection', 'charge off',
    'bankruptcy', 'foreclosure', 'late payment', 'credit score',
    'credit limit', 'balance', 'minimum payment', 'apr', 'interest rate'
  ];
  
  const foundKeywords = creditKeywords.filter(keyword => 
    textContent.toLowerCase().includes(keyword.toLowerCase())
  );
  
  // Extract creditor names (common patterns)
  const creditorPattern = /(?:CHASE|CITIBANK|BANK OF AMERICA|CAPITAL ONE|DISCOVER|AMEX|WELLS FARGO)/gi;
  const creditorMatches = textContent.match(creditorPattern) || [];
  const uniqueCreditors = [...new Set(creditorMatches.map(c => c.toUpperCase()))];
  
  return [...foundKeywords, ...uniqueCreditors].slice(0, 15);
};

// Generate AI insights from text and keywords
export const generateAIInsights = (textContent: string, keywords: string[]): string => {
  if (!textContent || textContent.length < 100) {
    return "Document appears to be too short or empty for analysis.";
  }
  
  let insights = "Credit Report Analysis:\n\n";
  
  // Account analysis
  const accountMatches = textContent.match(/account|tradeline/gi);
  if (accountMatches) {
    insights += `• Found ${accountMatches.length} potential account references\n`;
  }
  
  // Negative items detection
  const negativeTerms = ['late', 'delinquent', 'collection', 'charge', 'bankruptcy'];
  const negativeCount = negativeTerms.reduce((count, term) => {
    const matches = textContent.toLowerCase().match(new RegExp(term, 'gi'));
    return count + (matches ? matches.length : 0);
  }, 0);
  
  if (negativeCount > 0) {
    insights += `• Detected ${negativeCount} potential negative item indicators\n`;
  }
  
  // Payment history analysis
  if (textContent.toLowerCase().includes('payment')) {
    insights += "• Payment history information found\n";
  }
  
  // Credit utilization
  if (textContent.toLowerCase().includes('balance') || textContent.toLowerCase().includes('limit')) {
    insights += "• Credit utilization data detected\n";
  }
  
  if (keywords.length > 0) {
    insights += `\nKey terms identified: ${keywords.slice(0, 8).join(', ')}`;
  }
  
  return insights;
};