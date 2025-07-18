// Layer 1: React Hook - Component interface only
// This hook provides React state management and calls Layer 2 functions

import { useState, useCallback } from 'react';
import { ParsedTradeline } from "@/utils/tradelineParser";
import { 
  processFileWithOCR as processOCR,
  processFileWithAI as processAI,
  extractKeywordsFromText as extractKeywords,
  generateAIInsights as generateInsights,
  type ProcessingProgress,
  type OCRResult,
  type AIProcessingResult
} from '@/utils/creditReportProcessing';

export interface CreditReportProcessingHook {
  // State
  isUploading: boolean;
  uploadProgress: number;
  extractedKeywords: string[];
  aiInsights: string;
  extractedText: string;
  
  // Actions
  processWithOCR: (file: File) => Promise<string>;
  processWithAI: (file: File) => Promise<{ tradelines: ParsedTradeline[] }>;
  
  // State setters (for external control)
  setIsUploading: (uploading: boolean) => void;
  setUploadProgress: (progress: number) => void;
  setExtractedKeywords: (keywords: string[]) => void;
  setAiInsights: (insights: string) => void;
  setExtractedText: (text: string) => void;
  
  // Utilities
  cleanup: () => void;
  extractKeywordsFromText: (text: string) => string[];
  generateAIInsights: (text: string, keywords: string[]) => string;
}

export const useCreditReportProcessing = (userId: string): CreditReportProcessingHook => {
  // React state management
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [extractedKeywords, setExtractedKeywords] = useState<string[]>([]);
  const [aiInsights, setAiInsights] = useState('');
  const [extractedText, setExtractedText] = useState('');

  // Progress callback for Layer 2 functions
  const handleProgress = useCallback((progress: ProcessingProgress) => {
    setUploadProgress(progress.progress);
  }, []);

  // OCR processing with React state updates
  const processWithOCR = useCallback(async (file: File): Promise<string> => {
    setIsUploading(true);
    setUploadProgress(0);
    setExtractedText('');
    
    try {
      const result: OCRResult = await processOCR(file, handleProgress);
      
      if (result.success) {
        setExtractedText(result.extractedText);
        setUploadProgress(100);
        return result.extractedText;
      } else {
        throw new Error(result.error || 'OCR processing failed');
      }
    } catch (error) {
      setUploadProgress(0);
      throw error;
    } finally {
      setIsUploading(false);
    }
  }, [handleProgress]);

  // AI processing with React state updates
  const processWithAI = useCallback(async (file: File): Promise<{ tradelines: ParsedTradeline[] }> => {
    setIsUploading(true);
    setUploadProgress(0);
    setExtractedKeywords([]);
    setAiInsights('');
    setExtractedText('');
    
    try {
      const result: AIProcessingResult = await processAI(file, userId, handleProgress);
      
      if (result.success) {
        setExtractedKeywords(result.keywords);
        setAiInsights(result.insights);
        setExtractedText(result.extractedText);
        setUploadProgress(100);
        
        return { tradelines: result.tradelines };
      } else {
        throw new Error(result.error || 'AI processing failed');
      }
    } catch (error) {
      setUploadProgress(0);
      throw error;
    } finally {
      setIsUploading(false);
    }
  }, [userId, handleProgress]);

  // Wrapper functions for Layer 2 utilities (maintain backward compatibility)
  const extractKeywordsFromText = useCallback((textContent: string): string[] => {
    return extractKeywords(textContent);
  }, []);

  const generateAIInsights = useCallback((textContent: string, keywords: string[]): string => {
    return generateInsights(textContent, keywords);
  }, []);

  // Cleanup function
  const cleanup = useCallback(() => {
    setIsUploading(false);
    setUploadProgress(0);
    setExtractedKeywords([]);
    setAiInsights('');
    setExtractedText('');
  }, []);

  return {
    // State
    isUploading,
    uploadProgress,
    extractedKeywords,
    aiInsights,
    extractedText,
    
    // Actions
    processWithOCR,
    processWithAI,
    
    // State setters
    setIsUploading,
    setUploadProgress,
    setExtractedKeywords,
    setAiInsights,
    setExtractedText,
    
    // Utilities
    cleanup,
    extractKeywordsFromText,
    generateAIInsights
  };
};
