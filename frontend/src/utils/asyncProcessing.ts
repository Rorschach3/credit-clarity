// Lazy-loaded processing utilities for CreditReportUploadPage
import { ParsedTradeline } from '@/utils/tradelineParser';
import { 
  processWithOCR as processOCR, 
  processWithAI as processAI,
  extractKeywordsFromText,
  generateAIInsights,
  testBackendConnection,
  type ProcessingProgress
} from '@/utils/creditReportProcessor';

// Dynamic imports for heavy processing dependencies
export const loadOCRProcessor = async () => {
  // Return the pure OCR processing function
  return processOCR;
};

export const loadAIProcessor = async () => {
  // Return the pure AI processing function
  return processAI;
};

export const loadFileUploadHandler = async () => {
  // Lazy load the heavy file upload handler
  const { useFileUploadHandler } = await import('@/components/credit-upload/FileUploadHandler');
  return useFileUploadHandler;
};

// Re-export the interface
export type { ProcessingProgress };

// Async OCR processing
export const processFileWithOCR = async (
  file: File,
  userId: string,
  updateProgress: (progress: ProcessingProgress) => void
): Promise<ParsedTradeline[]> => {
  updateProgress({
    step: 'Loading OCR Engine...',
    progress: 10,
    message: 'Initializing text extraction'
  });

  // Get the pure OCR processing function
  const processOCR = await loadOCRProcessor();

  updateProgress({
    step: 'Extracting Text...',
    progress: 30,
    message: 'Reading document content'
  });

  try {
    const extractedText = await processOCR(file, userId);

    updateProgress({
      step: 'Parsing Tradelines...',
      progress: 70,
      message: 'Identifying credit accounts'
    });

    // Since OCR only extracts text, we don't get tradelines directly
    // You might want to parse the text or send it to AI processing instead
    updateProgress({
      step: 'Finalizing...',
      progress: 90,
      message: 'Text extraction complete'
    });

    // Return empty array for OCR-only processing
    // In a real scenario, you'd want to parse tradelines from the extracted text
    return [];
  } catch (error) {
    console.error('OCR processing failed:', error);
    throw error;
  }
};

// Async AI processing
export const processFileWithAI = async (
  file: File,
  userId: string,
  updateProgress: (progress: ProcessingProgress) => void
): Promise<ParsedTradeline[]> => {
  updateProgress({
    step: 'Loading AI Models...',
    progress: 10,
    message: 'Initializing AI processing'
  });

  // Get the pure AI processing function
  const processAI = await loadAIProcessor();

  updateProgress({
    step: 'AI Analysis...',
    progress: 40,
    message: 'Analyzing credit report structure'
  });

  try {
    console.log('🚀 Starting AI processing via creditReportProcessor...');
    
    // Test backend connection first
    updateProgress({
      step: 'Testing Connection...',
      progress: 45,
      message: 'Verifying backend connectivity'
    });

    const isConnected = await testBackendConnection(file);
    if (!isConnected) {
      throw new Error('Unable to connect to the processing server. Please check your connection and try again.');
    }
    
    updateProgress({
      step: 'Sending to Backend...',
      progress: 50,
      message: 'Uploading file to processing server'
    });

    const result = await processAI(file, userId);
    console.log('✅ AI processing completed, received result:', result);

    updateProgress({
      step: 'Validating Results...',
      progress: 80,
      message: 'Verifying extracted data'
    });

    // Quick validation
    const tradelineCount = result.tradelines?.length || 0;
    console.log(`📊 Extracted ${tradelineCount} tradelines`);

    updateProgress({
      step: '🎉 Analysis Complete! 🎊',
      progress: 100,
      message: `✨ Successfully extracted ${tradelineCount} tradeline(s)! 🎈`
    });

    return result.tradelines;
  } catch (error) {
    console.error('❌ AI processing failed in asyncProcessing:', error);
    
    // Provide more helpful error messages
    if (error.message.includes('timeout')) {
      updateProgress({
        step: '⏰ Request Timed Out',
        progress: 0,
        message: 'The request took too long. Try with a smaller file.'
      });
    } else if (error.message.includes('network') || error.message.includes('fetch')) {
      updateProgress({
        step: '🌐 Connection Error',
        progress: 0,
        message: 'Unable to connect to the processing server.'
      });
    } else {
      updateProgress({
        step: '❌ Processing Failed',
        progress: 0,
        message: 'An error occurred during processing.'
      });
    }
    
    throw error;
  }
};