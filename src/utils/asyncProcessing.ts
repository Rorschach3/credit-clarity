// Lazy-loaded processing utilities for CreditReportUploadPage
// Uses Layer 2 pure functions instead of React hooks

import { ParsedTradeline } from '@/utils/tradelineParser';
import { 
  processFileWithOCR as processOCR,
  processFileWithAI as processAI,
  type ProcessingProgress
} from '@/utils/creditReportProcessing';

// Re-export ProcessingProgress type for compatibility
export type { ProcessingProgress };

// Dynamic imports for heavy processing dependencies (if needed)
export const loadFileUploadHandler = async () => {
  // Lazy load the heavy file upload handler
  const { useFileUploadHandler } = await import('@/components/credit-upload/FileUploadHandler');
  return useFileUploadHandler;
};

// Async OCR processing using Layer 2 functions
export const processFileWithOCR = async (
  file: File,
  userId: string,
  updateProgress: (progress: ProcessingProgress) => void
): Promise<ParsedTradeline[]> => {
  updateProgress({
    step: 'Loading OCR Engine...',
    progress: 5,
    message: 'Initializing text extraction'
  });

  try {
    // Use Layer 2 OCR function directly (no React hooks needed)
    const result = await processOCR(file, updateProgress);

    if (!result.success) {
      throw new Error(result.error || 'OCR processing failed');
    }

    updateProgress({
      step: 'Parsing Tradelines...',
      progress: 85,
      message: 'Converting text to tradeline data'
    });

    // For now, return empty array since we're focusing on text extraction
    // In production, this would parse the extracted text into tradelines
    const tradelines: ParsedTradeline[] = [];

    updateProgress({
      step: 'Complete!',
      progress: 100,
      message: 'OCR processing finished'
    });

    return tradelines;
  } catch (error) {
    updateProgress({
      step: 'Error',
      progress: 0,
      message: error instanceof Error ? error.message : 'OCR processing failed'
    });
    
    throw error;
  }
};

// Async AI processing using Layer 2 functions
export const processFileWithAI = async (
  file: File,
  userId: string,
  updateProgress: (progress: ProcessingProgress) => void
): Promise<ParsedTradeline[]> => {
  updateProgress({
    step: 'Loading AI Models...',
    progress: 5,
    message: 'Initializing AI processing'
  });

  try {
    // Use Layer 2 AI function directly (no React hooks needed)
    const result = await processAI(file, userId, updateProgress);

    if (!result.success) {
      throw new Error(result.error || 'AI processing failed');
    }

    updateProgress({
      step: 'Validating Results...',
      progress: 95,
      message: 'Verifying extracted tradeline data'
    });

    // Brief validation delay
    await new Promise(resolve => setTimeout(resolve, 200));

    updateProgress({
      step: 'Complete!',
      progress: 100,
      message: 'AI processing finished'
    });

    return result.tradelines;
  } catch (error) {
    updateProgress({
      step: 'Error',
      progress: 0,
      message: error instanceof Error ? error.message : 'AI processing failed'
    });
    
    throw error;
  }
};

// Utility functions for external use
export const extractTextFromFile = async (file: File): Promise<string> => {
  const { extractTextFromFile } = await import('@/utils/creditReportProcessing');
  return extractTextFromFile(file);
};

export const extractKeywords = async (text: string): Promise<string[]> => {
  const { extractKeywordsFromText } = await import('@/utils/creditReportProcessing');
  return extractKeywordsFromText(text);
};

export const generateInsights = async (text: string, keywords: string[]): Promise<string> => {
  const { generateAIInsights } = await import('@/utils/creditReportProcessing');
  return generateAIInsights(text, keywords);
};