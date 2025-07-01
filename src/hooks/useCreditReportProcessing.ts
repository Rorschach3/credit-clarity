
import { useState, useRef, useCallback } from 'react';
import { createWorker, Worker } from "tesseract.js";
import { toast } from "@/components/ui/use-toast";
import { pdfToImages } from "@/utils/pdfToImage";
import { parseTradelinesFromText } from "@/utils/tradelineParser";
import { parseDocumentViaProxy, generateContent } from "@/services/llm-parser";
import { DocumentAIResponse } from "@/types";
import { fileToBase64, sanitizeAIResponse } from "@/utils/helpers";
import { v4 as uuidv4 } from 'uuid';
import { ParsedTradeline } from "@/utils/tradelineParser";

interface AIAnalysisResponse {
  tradelines?: Array<{
    creditor_name?: string;
    account_number?: string;
    account_balance?: string;
    account_status?: string;
    account_type?: string;
    credit_limit?: string;
    date_opened?: string;
    monthly_payment?: string;    
    credit_bureau?: string;
    is_negative?: boolean;
    dispute_count?: number;
    raw_text?: string;
  }>;
  keywords?: string[];
  insights?: string;
  negativeItems?: Array<{
    type: string;
    description: string;
    impact: string;
  }>;
}

export const useCreditReportProcessing = (userId: string) => {
  const workerRef = useRef<Worker | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [extractedKeywords, setExtractedKeywords] = useState<string[]>([]);
  const [aiInsights, setAiInsights] = useState<string>('');
  const [extractedText, setExtractedText] = useState<string>('');

  const extractKeywordsFromText = (text: string): string[] => {
    const creditKeywords = [
      'credit', 'debt', 'payment', 'balance', 'collection', 'charge-off', 'charge off',
      'bankruptcy', 'foreclosure', 'late', 'delinquent', 'dispute', 'inquiry',
      'account', 'tradeline', 'bureau', 'experian', 'equifax', 'transunion',
      'score', 'report', 'limit', 'utilization', 'negative', 'positive'
    ];
    
    const foundKeywords = new Set<string>();
    const lowerText = text.toLowerCase();
    
    creditKeywords.forEach(keyword => {
      if (lowerText.includes(keyword)) {
        foundKeywords.add(keyword);
      }
    });
    
    return Array.from(foundKeywords);
  };

  const generateAIInsights = (text: string, keywords: string[]): string => {
    const insights = [];
    
    if (keywords.includes('collection') || keywords.includes('charge-off')) {
      insights.push("⚠️ Negative items detected that may be affecting your credit score.");
    }
    
    if (keywords.includes('late') || keywords.includes('delinquent')) {
      insights.push("📉 Payment history issues found - these can be disputed if inaccurate.");
    }
    
    if (keywords.includes('inquiry')) {
      insights.push("🔍 Credit inquiries found - too many can lower your score.");
    }
    
    if (keywords.includes('utilization')) {
      insights.push("💳 Credit utilization information detected - keeping it below 30% is recommended.");
    }
    
    if (insights.length === 0) {
      insights.push("✅ Initial analysis complete. Review the extracted tradelines below.");
    }
    
    return insights.join('\n\n');
  };

  const processWithOCR = async (file: File): Promise<string> => {
    if (!workerRef.current) {
      workerRef.current = await createWorker('eng');
    }

    const buffer = await file.arrayBuffer();
    const images = await pdfToImages(buffer);
    let textContent = "";
    
    for (let i = 0; i < images.length; i++) {
      const { data } = await workerRef.current.recognize(images[i]);
      textContent += data.text + "\n";
      setUploadProgress(((i + 1) / images.length) * 70);
    }
    
    return textContent;
  };

  const processAIResponse = async (aiResponse: string, extractedText: string): Promise<ParsedTradeline[]> => {
    if (!aiResponse.trim()) {
      console.warn('AI returned empty response, using fallback analysis');
      
      const keywords = extractKeywordsFromText(extractedText);
      setExtractedKeywords(keywords);
      setAiInsights(generateAIInsights(extractedText, keywords));
      
      try {
        const fallbackTradelines = await parseTradelinesFromText(extractedText, userId);
        return fallbackTradelines;
      } catch (parseError) {
        console.error('Fallback tradeline parsing failed:', parseError);
        return [];
      }
    }

    try {
      let cleanedResponse = aiResponse.trim();
      if (cleanedResponse.startsWith('```json')) {
        cleanedResponse = cleanedResponse.replace(/```json\n?/, '').replace(/\n?```$/, '');
      } else if (cleanedResponse.startsWith('```')) {
        cleanedResponse = cleanedResponse.replace(/```\n?/, '').replace(/\n?```$/, '');
      }

      const sanitizedResponse = sanitizeAIResponse(cleanedResponse);
      const parsedAI: AIAnalysisResponse = JSON.parse(sanitizedResponse);
      
      setExtractedKeywords(parsedAI.keywords || extractKeywordsFromText(extractedText));
      setAiInsights(parsedAI.insights || generateAIInsights(extractedText, parsedAI.keywords || []));
      
      if (parsedAI.tradelines && parsedAI.tradelines.length > 0) {
        const convertedTradelines: ParsedTradeline[] = parsedAI.tradelines.map((item) => ({
          id: uuidv4(),
          creditor_name: item.creditor_name || '',
          account_number: item.account_number || '',
          account_balance: item.account_balance || '$0',
          account_status: (item.account_status as "" | "open" | "closed" | "in_collection" | "charged_off" | "disputed") || "",
          account_type: (item.account_type as "" | "credit_card" | "loan" | "mortgage" | "auto_loan" | "student_loan" | "collection") || "credit_card",
          credit_limit: item.credit_limit || '$0',
          date_opened: item.date_opened || '',
          monthly_payment: item.monthly_payment || '$0',
          is_negative: Boolean(item.is_negative),
          dispute_count: Number(item.dispute_count) || 0,
          credit_bureau: (item.credit_bureau as "equifax" | "transunion" | "experian") || "",
          created_at: new Date().toISOString(),
          raw_text: extractedText,
          user_id: userId
        }));

        return convertedTradelines;
      }
      return [];
    } catch (jsonError) {
      console.error('Failed to parse AI response as JSON:', jsonError);
      
      const keywords = extractKeywordsFromText(extractedText);
      setExtractedKeywords(keywords);
      setAiInsights(generateAIInsights(extractedText, keywords));
      
      try {
        const fallbackTradelines = await parseTradelinesFromText(extractedText, userId);
        return fallbackTradelines;
      } catch (parseError) {
        console.error('Traditional parser also failed:', parseError);
        return [];
      }
    }
  };

  const processWithAI = async (file: File): Promise<{ tradelines: ParsedTradeline[], textContent: string }> => {
    try {
      console.log("Starting AI processing...");
      setUploadProgress(10);

      let textContent = '';
      
      try {
        textContent = await processWithOCR(file);
        setUploadProgress(50);
        console.log("OCR extraction completed, text length:", textContent.length);
      } catch (ocrError) {
        console.error('OCR failed, trying Document AI:', ocrError);
        
        const base64Content = await fileToBase64(file);
        const documentData = await parseDocumentViaProxy(base64Content) as DocumentAIResponse | undefined;
        
        if (documentData?.document?.text) {
          textContent = documentData.document.text;
          setUploadProgress(50);
        } else {
          throw new Error('Both OCR and Document AI failed to extract text');
        }
      }

      setExtractedText(textContent);

      if (textContent.trim()) {
        try {
          const prompt = `
            Analyze this credit report text and extract key information. Return a JSON object with this structure:
            {
              "keywords": ["array", "of", "credit", "related", "terms", "found"],
              "insights": "Brief analysis of the credit report findings and recommendations",
              "tradelines": [
                {
                  "creditor_name": "Company Name",
                  "account_number": "Account Number",
                  "account_balance": "$Amount",
                  "account_status": "open|closed|in_collection|charged_off|disputed",
                  "account_type": "credit_card|loan|mortgage|auto_loan|student_loan|collection",
                  "credit_limit": "$Amount",
                  "date_opened": "YYYY-MM-DD",
                  "monthly_payment": "$Amount",
                  "credit_bureau": "experian|equifax|transunion",
                  "is_negative": true/false
                }
              ]
            }

            Focus on finding negative items, payment history issues, and accounts that could be disputed.
          `;

          let aiResponse = '';
          
          await generateContent(
            [
              {
                role: "user",
                parts: [
                  {
                    text: `${prompt}\n\nCredit Report Content:\n${textContent.substring(0, 4000)}`
                  }
                ]
              }
            ],
            (chunk: string) => {
              aiResponse += chunk;
            }
          );

          setUploadProgress(80);
          console.log("AI analysis completed");
          
          const tradelines = await processAIResponse(aiResponse, textContent);
          setUploadProgress(100);
          
          return { tradelines, textContent };
          
        } catch (aiError) {
          console.error('AI analysis failed, using basic analysis:', aiError);
          
          const keywords = extractKeywordsFromText(textContent);
          setExtractedKeywords(keywords);
          setAiInsights(generateAIInsights(textContent, keywords));
          
          try {
            const basicTradelines = await parseTradelinesFromText(textContent, userId);
            return { tradelines: basicTradelines, textContent };
          } catch (parseError) {
            console.error('Basic parsing also failed:', parseError);
            return { tradelines: [], textContent };
          }
        }
      }
      
      setUploadProgress(100);
      return { tradelines: [], textContent };
      
    } catch (error) {
      console.error('AI processing error:', error);
      toast({ 
        title: "Processing Failed", 
        description: "Failed to process document. Please try OCR method.",
        variant: "destructive"
      });
      
      throw error;
    }
  };

  const cleanup = useCallback(() => {
    if (workerRef.current) {
      workerRef.current.terminate();
      workerRef.current = null;
    }
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
