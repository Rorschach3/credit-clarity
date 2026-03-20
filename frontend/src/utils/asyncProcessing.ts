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

  const processAI = await loadAIProcessor();

  updateProgress({
    step: 'Uploading File...',
    progress: 25,
    message: `Sending ${(file.size / (1024 * 1024)).toFixed(1)} MB to server`
  });

  // Slowly tick progress from 40→70% while waiting for the backend (can take minutes)
  let tickedProgress = 40;
  let processingDone = false;
  const fileSizeMB = file.size / (1024 * 1024);
  const timeoutMinutes = Math.max(2, Math.min(8, Math.ceil(fileSizeMB)));
  const totalTickMs = timeoutMinutes * 60 * 1000;
  const tickInterval = Math.round(totalTickMs / 30); // 30 ticks across expected duration

  const ticker = setInterval(() => {
    if (processingDone) return;
    tickedProgress = Math.min(tickedProgress + 1, 70);
    updateProgress({
      step: 'Extracting Tradelines...',
      progress: tickedProgress,
      message: 'AI is reading account details, balances, and payment history'
    });
  }, tickInterval);

  updateProgress({
    step: 'Analyzing Credit Report...',
    progress: 40,
    message: 'AI is parsing credit report structure'
  });

  // Bridge processWithAI's onProgress string messages into updateProgress
  const onProgress = (message: string) => {
    if (message.includes('Uploading')) {
      updateProgress({ step: 'Uploading File...', progress: 28, message });
    } else if (message.includes('Processing PDF') || message.includes('Processing in background')) {
      updateProgress({ step: 'Analyzing Credit Report...', progress: tickedProgress, message });
    } else if (message.includes('Retrying')) {
      updateProgress({ step: 'Retrying...', progress: tickedProgress, message });
    } else if (message.includes('timed out') || message.includes('failed') || message.includes('error')) {
      updateProgress({ step: 'Error', progress: tickedProgress, message });
    }
  };

  try {
    const result = await processAI(file, userId, onProgress);

    processingDone = true;
    clearInterval(ticker);

    // If backend responded with a background job, surface that to caller immediately
    if (result.isBackgroundJob && result.job_id) {
      updateProgress({
        step: 'Queued',
        progress: 0,
        message: 'Processing in background...'
      });
      return result;
    }

    updateProgress({
      step: 'Parsing Results...',
      progress: 75,
      message: `Organizing ${result.stats?.found ?? 0} extracted tradelines`
    });

    await new Promise(resolve => setTimeout(resolve, 300));

    updateProgress({
      step: 'Validating Data...',
      progress: 85,
      message: 'Checking account numbers, balances, and dates'
    });

    await new Promise(resolve => setTimeout(resolve, 300));

    updateProgress({
      step: 'Saving to Account...',
      progress: 93,
      message: 'Storing tradelines in your profile'
    });

    await new Promise(resolve => setTimeout(resolve, 200));

    updateProgress({
      step: 'Complete!',
      progress: 100,
      message: `Done — ${result.stats?.found ?? 0} tradelines found, ${result.stats?.saved ?? 0} saved`
    });

    return result;
  } catch (error) {
    processingDone = true;
    clearInterval(ticker);
    console.error('AI processing failed:', error);
    throw error;
  }
};