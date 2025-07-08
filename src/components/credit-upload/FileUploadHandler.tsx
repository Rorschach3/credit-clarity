
import { ChangeEvent } from 'react';
import { toast } from "sonner";
import { ParsedTradeline } from "@/utils/tradelineParser";
import { processPdfFile } from "@/utils/pdf-processor";
import { processAndSaveTradelines } from "@/utils/document-ai-parser";
import { useAuthGuard } from "@/hooks/useAuthGuard";
import { useMemoryCleanup } from "@/hooks/useMemoryCleanup";

interface FileUploadHandlerProps {
  user: { id: string; email?: string } | null;
  processingMethod: 'ocr' | 'ai';
  onUploadStart: () => void;
  onUploadComplete: (tradelines: ParsedTradeline[]) => void;
  onUploadError: (error: string) => void;
  setUploadProgress: (progress: number) => void;
  setExtractedKeywords: (keywords: string[]) => void;
  setAiInsights: (insights: string) => void;
  setExtractedText: (text: string) => void;
  setShowAiResults: (show: boolean) => void;
  extractKeywordsFromText: (text: string) => string[];
  generateAIInsights: (text: string, keywords: string[]) => string;
}

// File validation utility
const validateFile = (file: File): void => {
  const allowedTypes = ['application/pdf'];
  const maxSize = 10 * 1024 * 1024; // 10MB

  if (!allowedTypes.includes(file.type)) {
    throw new Error('Only PDF files are allowed');
  }

  if (file.size > maxSize) {
    throw new Error('File size must be less than 10MB');
  }

  if (file.size === 0) {
    throw new Error('File is empty');
  }
};

export const useFileUploadHandler = ({
  user,
  onUploadStart,
  onUploadComplete,
  onUploadError,
  setUploadProgress,
  setExtractedKeywords,
  setAiInsights,
  setExtractedText,
  setShowAiResults,
  extractKeywordsFromText,
  generateAIInsights
}: FileUploadHandlerProps) => {
  const { requireAuth } = useAuthGuard();
  const { addCleanup, cleanup } = useMemoryCleanup();
  
  const handleFileUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    console.log("handleFileUpload triggered");
    
    // Clean up any previous operations
    cleanup();
    
    try {
      const file = event.target.files?.[0];
      if (!file) {
        return;
      }

      // Validate file
      try {
        validateFile(file);
      } catch (validationError) {
        toast.error(validationError instanceof Error ? validationError.message : "Invalid file format");
        return;
      }

      // Auth guard
      if (!requireAuth("upload and process files")) {
        return;
      }

      if (!user || !user.id) {
        toast.error("You must be logged in.");
        return;
      }

      onUploadStart();
      setUploadProgress(10);
      setExtractedKeywords([]);
      setAiInsights('');
      setExtractedText('');
      setShowAiResults(true);

      // Process PDF with Google Document AI for enhanced tradeline extraction
      setUploadProgress(30);
      console.log("🔍 Processing PDF with Google Document AI...");
      
      try {
        // Use Google Document AI for enhanced processing and automatic tradeline extraction
        const parsedTradelines = await processAndSaveTradelines(
          file, 
          user.id, 
          true // Update existing records
        );
        
        console.log("✅ Successfully processed with Document AI:", parsedTradelines.length);
        
        setUploadProgress(70);
        setExtractedText(`Document processed successfully with Google Document AI. Found ${parsedTradelines.length} tradelines.`);
        
        // Extract keywords and generate insights from the first few tradelines for display
        const tradelineText = parsedTradelines.map(t => 
          `${t.creditor_name} ${t.account_type} ${t.account_status}`
        ).join(' ');
        
        const keywords = extractKeywordsFromText(tradelineText);
        setExtractedKeywords(keywords);
        
        const insights = generateAIInsights(tradelineText, keywords);
        setAiInsights(insights);
        
        setUploadProgress(90);
        onUploadComplete(parsedTradelines);
        
        setUploadProgress(100);
        
        toast.success(`Document processed successfully with Google Document AI. Found ${parsedTradelines.length} tradelines.`);
        
      } catch (documentAIError) {
        console.warn("Document AI processing failed, falling back to basic PDF processing:", documentAIError);
        
        try {
          // Fallback to basic PDF processing with proper error boundaries
          const pdfResult = await processPdfFile(file);
          console.log(`PDF processed: ${pdfResult.pages} pages, ${pdfResult.text.length} characters`);
          
          setUploadProgress(50);
          setExtractedText(pdfResult.text);

          // Extract keywords and generate insights
          const keywords = extractKeywordsFromText(pdfResult.text);
          setExtractedKeywords(keywords);
          
          const insights = generateAIInsights(pdfResult.text, keywords);
          setAiInsights(insights);
          
          setUploadProgress(70);

          // Parse tradelines from extracted text using fallback method
          try {
            const { parseTradelinesFromText } = await import("@/utils/tradelineParser");
            const parsed = parseTradelinesFromText(pdfResult.text, user.id);
            console.log("Parsed tradelines (fallback):", parsed);
            
            if (parsed.length === 0) {
              toast.error("Could not identify any tradelines in this document. Try manual entry or a different document.");
            }
            
            onUploadComplete(parsed);
          } catch (parseError) {
            console.error("Tradeline parsing failed:", parseError);
            toast.error("We couldn't extract data. Please upload a clearer PDF with text or scanned OCR-supported format.");
            onUploadComplete([]);
          }
          
          setUploadProgress(100);
          
          toast.success(`Document processed with fallback method. Found ${pdfResult.pages} pages.`);
        } catch (fallbackError) {
          console.error("Both Document AI and PDF fallback failed:", fallbackError);
          const errorMessage = "Failed to process document with both AI and fallback methods. Please try a different file or contact support.";
          onUploadError(errorMessage);
          toast.error(errorMessage);
        }
      }
    } catch (error) {
      console.error("PDF processing error:", error instanceof Error ? error.message : String(error));
      const errorMessage = error instanceof Error ? error.message : "Failed to process PDF. Please try again.";
      onUploadError(errorMessage);
      toast.error(errorMessage);
    } finally {
      // Clean up resources after processing
      addCleanup(() => {
        setUploadProgress(0);
        setExtractedKeywords([]);
        setAiInsights('');
        setExtractedText('');
      });
    }
  };

  return { handleFileUpload, cleanup };
};
