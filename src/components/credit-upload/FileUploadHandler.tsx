
import { ChangeEvent } from 'react';
import { toast } from "@/components/ui/use-toast";
import { ParsedTradeline } from "@/utils/tradelineParser";
import { processPdfFile } from "@/utils/pdf-processor";

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
  
  const handleFileUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    console.log("handleFileUpload triggered");
    try {
      const file = event.target.files?.[0];
      if (!file) {
        return;
      }

      // Validate file
      try {
        validateFile(file);
      } catch (validationError) {
        toast({ 
          title: "Invalid file", 
          description: validationError instanceof Error ? validationError.message : "Invalid file format",
          variant: "destructive"
        });
        return;
      }

      if (!user || !user.id) {
        toast({ title: "Error", description: "You must be logged in.", variant: "destructive" });
        return;
      }

      onUploadStart();
      setUploadProgress(10);
      setExtractedKeywords([]);
      setAiInsights('');
      setExtractedText('');
      setShowAiResults(true);

      // Process PDF file
      setUploadProgress(30);
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

      // Parse tradelines from extracted text
      try {
        const { parseTradelinesFromText } = await import("@/utils/tradelineParser");
        const parsed = parseTradelinesFromText(pdfResult.text, user.id);
        console.log("Parsed tradelines:", parsed);
        
        if (parsed.length === 0) {
          toast({
            title: "No tradelines found",
            description: "Could not identify any tradelines in this document. Try manual entry or a different document.",
            variant: "destructive"
          });
        }
        
        onUploadComplete(parsed);
      } catch (parseError) {
        console.error("Tradeline parsing failed:", parseError);
        toast({
          title: "Parsing Error",
          description: "Failed to parse tradelines from document. Try manual entry.",
          variant: "destructive"
        });
        onUploadComplete([]);
      }
      
      setUploadProgress(100);
      
      toast({
        title: "Upload complete",
        description: `Document processed successfully. Found ${pdfResult.pages} pages.`
      });
    } catch (error) {
      console.error("PDF processing error:", error instanceof Error ? error.message : String(error));
      const errorMessage = error instanceof Error ? error.message : "Failed to process PDF. Please try again.";
      onUploadError(errorMessage);
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
    }
  };

  return { handleFileUpload };
};
