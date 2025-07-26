import { useState, useCallback } from 'react';
import { ParsedTradeline } from "@/utils/tradelineParser";
import { 
  processWithOCR as processOCRUtil, 
  processWithAI as processAIUtil,
  extractKeywordsFromText as extractKeywords,
  generateAIInsights as generateInsights
} from '@/utils/creditReportProcessor';

export const useCreditReportProcessing = (userId: string) => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [extractedKeywords, setExtractedKeywords] = useState<string[]>([]);
  const [aiInsights, setAiInsights] = useState('');
  const [extractedText, setExtractedText] = useState('');

  const processWithOCR = useCallback(async (file: File): Promise<string> => {
    setUploadProgress(10);
    
    try {
      const text = await processOCRUtil(file, userId);
      setUploadProgress(80);
      return text;
    } catch (error) {
      console.error('OCR processing error:', error);
      throw error;
    }
  }, [userId]);

  const processWithAI = useCallback(async (file: File): Promise<{ tradelines: ParsedTradeline[] }> => {
    setUploadProgress(20);
    
    try {
      // Use the utility function for processing
      const result = await processAIUtil(file, userId);
      setUploadProgress(60);
      
      // The backend should return extracted_text, so we don't need to call OCR again
      // But if we need the text for keywords/insights, we can get it from the result
      if (result.tradelines && result.tradelines.length > 0) {
        // Use a simple text extraction for insights if we have tradelines
        const textContent = result.tradelines.map(t => 
          `${t.creditor_name} ${t.account_status} ${t.account_type}`
        ).join(' ');
        
        setExtractedText(textContent);
        
        // Extract keywords and generate insights
        const keywords = extractKeywords(textContent);
        setExtractedKeywords(keywords);
        
        const insights = generateInsights(textContent, keywords);
        setAiInsights(insights);
      }
      
      setUploadProgress(80);

      return result;
    } catch (error) {
      console.error('AI processing error:', error);
      throw error;
    }
  }, [userId]);


  const cleanup = useCallback(() => {
    setIsUploading(false);
    setUploadProgress(0);
    setExtractedKeywords([]);
    setAiInsights('');
    setExtractedText('');
  }, []);

  return {
    isUploading,
    uploadProgress,
    extractedKeywords,
    aiInsights,
    extractedText,
    processWithOCR,
    processWithAI,
    setIsUploading,
    setUploadProgress,
    setExtractedKeywords,
    setAiInsights,
    setExtractedText,
    cleanup
  };
};
