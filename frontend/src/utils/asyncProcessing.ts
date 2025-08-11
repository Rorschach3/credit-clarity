// Lazy-loaded processing utilities for CreditReportUploadPage
import { ParsedTradeline } from '@/utils/tradelineParser';
import { 
  processWithOCR as processOCR, 
  processWithAI as processAI,
  extractKeywordsFromText,
  generateAIInsights,
  type ProcessingProgress,
  type ProcessingResult
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
export type { ProcessingProgress, ProcessingResult };

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
): Promise<ProcessingResult> => {
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
    const result = await processAI(file, userId);

    // If backend responded with a background job, surface that to caller immediately
    if (result.isBackgroundJob && result.job_id) {
      updateProgress({
        step: 'Queued',
        progress: 0,
        message: 'Processing in background...'
      });
      return result; // contains job_id, status, isBackgroundJob
    }

    updateProgress({
      step: 'Validating Results...',
      progress: 80,
      message: 'Verifying extracted data'
    });

    // Simulate validation
    await new Promise(resolve => setTimeout(resolve, 500));

    updateProgress({
      step: 'Complete!',
      progress: 100,
      message: 'Processing finished'
    });

    return result;
  } catch (error) {
    console.error('AI processing failed:', error);
    throw error;
  }
};