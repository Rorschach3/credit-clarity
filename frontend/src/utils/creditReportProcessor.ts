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
    console.log('🚀 Starting OCR fetch request to backend...');
    
    // Create AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      console.warn('⏰ OCR Request timeout - aborting after 5 minutes');
      controller.abort();
    }, 5 * 60 * 1000); // 5 minute timeout
    
    const response = await fetch('/api/process-credit-report', {
      method: 'POST',
      body: formData,
      signal: controller.signal
      // NO HEADERS - Let browser set multipart/form-data with boundary
    });
    
    clearTimeout(timeoutId); // Clear timeout if request completes
    console.log('📨 OCR Response received:', response.status, response.statusText);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ OCR Backend error:', response.status, errorText);
      throw new Error(`Backend error ${response.status}: ${errorText}`);
    }
    
    console.log('📖 Reading OCR JSON response...');
    const result = await response.json();
    console.log('✅ OCR Success:', result);
    
    return result.extracted_text || '';
  } catch (error) {
    if (error.name === 'AbortError') {
      console.error('❌ OCR Request was aborted due to timeout');
      throw new Error('OCR request timed out after 5 minutes. Please try with a smaller file or contact support.');
    }
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
    console.log('🚀 Starting fetch request to backend...');
    
    // Create AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      console.warn('⏰ Request timeout - aborting after 5 minutes');
      controller.abort();
    }, 5 * 60 * 1000); // 5 minute timeout
    
    const response = await fetch('/api/process-credit-report', {
      method: 'POST',
      body: formData,
      signal: controller.signal
      // NO HEADERS - Let browser set multipart/form-data with boundary
    });
    
    clearTimeout(timeoutId); // Clear timeout if request completes
    console.log('📨 Response received:', response.status, response.statusText);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Backend error:', response.status, errorText);
      throw new Error(`Backend error ${response.status}: ${errorText}`);
    }
    
    console.log('📖 Reading JSON response...');
    const result = await response.json();
    console.log('✅ Success - received result:', {
      success: result.success,
      tradelines_count: result.tradelines?.length || 0,
      processing_method: result.processing_method
    });
    
    return { tradelines: result.tradelines || [] };
  } catch (error) {
    if (error.name === 'AbortError') {
      console.error('❌ Request was aborted due to timeout');
      throw new Error('Request timed out after 5 minutes. Please try with a smaller file or contact support.');
    }
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

// Quick connectivity test
export const testBackendConnection = async (file: File): Promise<boolean> => {
  try {
    console.log('🔍 Testing backend connection...');
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', 'test-connection');
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
    
    const response = await fetch('/api/quick-test', {
      method: 'POST',
      body: formData,
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (response.ok) {
      const result = await response.json();
      console.log('✅ Backend connection test successful:', result);
      return true;
    } else {
      console.error('❌ Backend connection test failed:', response.status);
      return false;
    }
  } catch (error) {
    console.error('❌ Backend connection test error:', error);
    return false;
  }
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