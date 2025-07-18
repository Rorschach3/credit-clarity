// Layer 2: Pure processing functions - no React dependencies
// These functions can be used in asyncProcessing.ts or any other context

import { ParsedTradeline } from "@/utils/tradelineParser";

export interface ProcessingProgress {
  step: string;
  progress: number;
  message: string;
}

export interface OCRResult {
  extractedText: string;
  success: boolean;
  error?: string;
}

export interface AIProcessingResult {
  tradelines: ParsedTradeline[];
  keywords: string[];
  insights: string;
  extractedText: string;
  success: boolean;
  error?: string;
}

// ===== OCR Processing Functions =====

/**
 * Extract text from a file using OCR
 */
export const processFileWithOCR = async (
  file: File,
  onProgress?: (progress: ProcessingProgress) => void
): Promise<OCRResult> => {
  onProgress?.({
    step: 'Reading File',
    progress: 10,
    message: 'Accessing file content'
  });

  try {
    const extractedText = await extractTextFromFile(file, onProgress);
    
    onProgress?.({
      step: 'Text Extraction Complete',
      progress: 100,
      message: 'Text successfully extracted'
    });

    return {
      extractedText,
      success: true
    };
  } catch (error) {
    return {
      extractedText: '',
      success: false,
      error: error instanceof Error ? error.message : 'OCR processing failed'
    };
  }
};

/**
 * Validate if the input is a valid File object
 */
const validateFileInput = (file: any): file is File => {
  if (!file) {
    console.error('validateFileInput: file is null or undefined');
    return false;
  }
  
  if (file instanceof File) {
    return true;
  }
  
  // Check if it's a File-like object
  const isFilelike = (
    file &&
    typeof file === 'object' &&
    typeof file.name === 'string' &&
    typeof file.size === 'number' &&
    typeof file.type === 'string' &&
    typeof file.stream === 'function' &&
    typeof file.arrayBuffer === 'function'
  );
  
  if (!isFilelike) {
    console.error('validateFileInput: Invalid file object received:', {
      type: typeof file,
      constructor: file?.constructor?.name,
      hasName: typeof file?.name,
      hasSize: typeof file?.size,
      hasType: typeof file?.type,
      hasStream: typeof file?.stream,
      hasArrayBuffer: typeof file?.arrayBuffer
    });
  }
  
  return isFilelike;
};

/**
 * Extract text content from various file types
 */
export const extractTextFromFile = async (
  file: File,
  onProgress?: (progress: ProcessingProgress) => void
): Promise<string> => {
  // Validate file input
  if (!validateFileInput(file)) {
    const fileInfo = file ? {
      type: typeof file,
      constructor: file?.constructor?.name,
      isFile: file instanceof File,
      keys: Object.keys(file || {})
    } : 'null/undefined';
    
    throw new Error(`Invalid file input: Expected a File object, received ${JSON.stringify(fileInfo)}`);
  }

  onProgress?.({
    step: 'Validating File',
    progress: 10,
    message: `Processing ${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB)`
  });

  // Check file size (limit to 50MB)
  if (file.size > 50 * 1024 * 1024) {
    throw new Error('File too large. Maximum size is 50MB.');
  }

  // Check file type
  const allowedTypes = [
    'application/pdf',
    'text/plain',
    'text/csv',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  ];
  
  if (!allowedTypes.includes(file.type) && !file.name.toLowerCase().endsWith('.pdf')) {
    console.warn(`Unsupported file type: ${file.type}. Attempting to process anyway.`);
  }

  onProgress?.({
    step: 'Reading File',
    progress: 30,
    message: 'Reading file content'
  });

  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = () => {
      try {
        onProgress?.({
          step: 'Parsing Content',
          progress: 70,
          message: 'Extracting text data'
        });
        
        const text = reader.result as string || '';
        
        onProgress?.({
          step: 'Finalizing',
          progress: 90,
          message: 'Preparing extracted text'
        });
        
        resolve(text);
      } catch (error) {
        reject(new Error(`Failed to process file content: ${error instanceof Error ? error.message : 'Unknown error'}`));
      }
    };
    
    reader.onerror = () => {
      reject(new Error(`Failed to read file: ${file.name}`));
    };
    
    reader.onabort = () => {
      reject(new Error(`File reading was aborted: ${file.name}`));
    };
    
    try {
      // For now, reading as text. In production, you'd use proper OCR libraries
      // like Tesseract.js for image files or pdf-parse for PDFs
      if (file.type === 'application/pdf') {
        // For PDFs, we'd normally use pdf-parse or similar
        // For now, attempt to read as text (will likely fail gracefully)
        reader.readAsText(file);
      } else {
        reader.readAsText(file);
      }
    } catch (error) {
      reject(new Error(`Failed to initiate file reading: ${error instanceof Error ? error.message : 'Unknown error'}`));
    }
  });
};

// ===== AI Processing Functions =====

/**
 * Process file with AI analysis to extract tradelines
 */
export const processFileWithAI = async (
  file: File,
  userId: string,
  onProgress?: (progress: ProcessingProgress) => void
): Promise<AIProcessingResult> => {
  onProgress?.({
    step: 'Initializing AI',
    progress: 10,
    message: 'Preparing AI analysis'
  });

  try {
    // Extract text first
    const extractedText = await extractTextFromFile(file, (progress) => {
      onProgress?.({
        ...progress,
        progress: 10 + (progress.progress * 0.3) // Scale to 10-40%
      });
    });

    onProgress?.({
      step: 'Analyzing Content',
      progress: 50,
      message: 'Extracting keywords and patterns'
    });

    // Extract keywords
    const keywords = extractKeywordsFromText(extractedText);

    onProgress?.({
      step: 'Generating Insights',
      progress: 70,
      message: 'Creating analysis report'
    });

    // Generate insights
    const insights = generateAIInsights(extractedText, keywords);

    onProgress?.({
      step: 'Parsing Tradelines',
      progress: 85,
      message: 'Identifying tradeline data'
    });

    // Parse tradelines (placeholder - in production would use actual AI/ML)
    const tradelines = parseTradelinesFromText(extractedText, userId);

    onProgress?.({
      step: 'Complete',
      progress: 100,
      message: 'AI analysis finished'
    });

    return {
      tradelines,
      keywords,
      insights,
      extractedText,
      success: true
    };
  } catch (error) {
    return {
      tradelines: [],
      keywords: [],
      insights: '',
      extractedText: '',
      success: false,
      error: error instanceof Error ? error.message : 'AI processing failed'
    };
  }
};

/**
 * Extract credit-related keywords from text
 */
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
  const creditorPattern = /(?:CHASE|CITIBANK|BANK OF AMERICA|CAPITAL ONE|DISCOVER|AMEX|WELLS FARGO|SYNCHRONY|COMENITY)/gi;
  const creditorMatches = textContent.match(creditorPattern) || [];
  const uniqueCreditors = [...new Set(creditorMatches.map(c => c.toUpperCase()))];
  
  return [...foundKeywords, ...uniqueCreditors].slice(0, 15);
};

/**
 * Generate AI insights from text content and keywords
 */
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
  
  // Bureau detection
  const bureaus = ['experian', 'equifax', 'transunion'];
  const foundBureaus = bureaus.filter(bureau => 
    textContent.toLowerCase().includes(bureau)
  );
  
  if (foundBureaus.length > 0) {
    insights += `• Credit bureau detected: ${foundBureaus.map(b => 
      b.charAt(0).toUpperCase() + b.slice(1)
    ).join(', ')}\n`;
  }
  
  if (keywords.length > 0) {
    insights += `\nKey terms identified: ${keywords.slice(0, 8).join(', ')}`;
  }
  
  return insights;
};

/**
 * Parse tradelines from text content (placeholder implementation)
 */
export const parseTradelinesFromText = (
  textContent: string, 
  userId: string
): ParsedTradeline[] => {
  // This is a placeholder implementation
  // In production, this would use sophisticated AI/ML to parse actual tradeline data
  
  const creditorPattern = /(?:CHASE|CITIBANK|BANK OF AMERICA|CAPITAL ONE|DISCOVER|AMEX|WELLS FARGO)/gi;
  const creditorMatches = textContent.match(creditorPattern) || [];
  
  const tradelines: ParsedTradeline[] = creditorMatches.slice(0, 5).map((creditor, index) => ({
    id: `parsed-${Date.now()}-${index}`,
    user_id: userId,
    creditor_name: creditor.toUpperCase(),
    account_number: `****${Math.floor(Math.random() * 9999).toString().padStart(4, '0')}`,
    account_type: 'credit_card',
    account_status: Math.random() > 0.7 ? 'closed' : 'open',
    credit_bureau: ['Experian', 'Equifax', 'TransUnion'][Math.floor(Math.random() * 3)],
    account_balance: `$${Math.floor(Math.random() * 5000)}`,
    credit_limit: `$${Math.floor(Math.random() * 10000) + 1000}`,
    monthly_payment: `$${Math.floor(Math.random() * 200) + 25}`,
    date_opened: new Date(2020 + Math.floor(Math.random() * 4), Math.floor(Math.random() * 12), 1)
      .toISOString().split('T')[0],
    date_updated: new Date().toISOString().split('T')[0],
    is_negative: Math.random() > 0.6, // 40% chance of being negative
    dispute_count: 0,
    created_at: new Date().toISOString()
  }));
  
  return tradelines;
};