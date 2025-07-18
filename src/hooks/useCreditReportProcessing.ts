import { useState, useCallback } from 'react';
import {  ParsedTradeline } from "@/utils/tradelineParser";

export const useCreditReportProcessing = (userId: string) => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [extractedKeywords, setExtractedKeywords] = useState<string[]>([]);
  const [aiInsights, setAiInsights] = useState('');
  const [extractedText, setExtractedText] = useState('');

  const processWithOCR = useCallback(async (file: File): Promise<string> => {
    setUploadProgress(10);
    
    // Simple text extraction fallback
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = () => {
        setUploadProgress(50);
        const text = reader.result as string || '';
        setUploadProgress(80);
        resolve(text);
      };
      reader.readAsText(file);
    });
  }, []);

  const processWithAI = useCallback(async (file: File): Promise<{ tradelines: ParsedTradeline[] }> => {
    setUploadProgress(20);
    
    try {
      const reader = new FileReader();
      return new Promise((resolve, reject) => {
        reader.onload = async () => {
          try {
            const textContent = reader.result as string || '';
            setUploadProgress(40);
            
            // Extract keywords and generate insights
            const keywords = extractKeywordsFromText(textContent);
            setExtractedKeywords(keywords);
            setUploadProgress(60);
            
            const insights = generateAIInsights(textContent, keywords);
            setAiInsights(insights);
            setExtractedText(textContent);
            setUploadProgress(80);

            resolve({ tradelines: [] });
          } catch (error) {
            reject(error);
          }
        };
        reader.onerror = () => reject(new Error('Failed to read file'));
        reader.readAsText(file);
      });
    } catch (error) {
      console.error('AI processing error:', error);
      throw error;
    }
  }, [userId]);

  const extractKeywordsFromText = useCallback((textContent: string): string[] => {
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
  }, []);

  const generateAIInsights = useCallback((textContent: string, keywords: string[]): string => {
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
  }, []);

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
    cleanup,
    extractKeywordsFromText,
    generateAIInsights
  };
};
