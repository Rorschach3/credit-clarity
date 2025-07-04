
import React, { ChangeEvent } from 'react';
import { toast } from "@/components/ui/use-toast";
import { ParsedTradeline } from "@/utils/tradelineParser";

interface FileUploadHandlerProps {
  user: any;
  processingMethod: 'ocr' | 'ai';
  onUploadStart: () => void;
  onUploadComplete: (tradelines: ParsedTradeline[]) => void;
  onUploadError: (error: string) => void;
  processWithOCR: (file: File) => Promise<string>;
  processWithAI: (file: File) => Promise<{ tradelines: ParsedTradeline[] }>;
  setUploadProgress: (progress: number) => void;
  setExtractedKeywords: (keywords: string[]) => void;
  setAiInsights: (insights: string) => void;
  setExtractedText: (text: string) => void;
  setShowAiResults: (show: boolean) => void;
  extractKeywordsFromText: (text: string) => string[];
  generateAIInsights: (text: string, keywords: string[]) => string;
}

export const useFileUploadHandler = ({
  user,
  processingMethod,
  onUploadStart,
  onUploadComplete,
  onUploadError,
  processWithOCR,
  processWithAI,
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
      if (!file || file.type !== "application/pdf") {
        toast({ title: "Invalid file", description: "Please upload a PDF file." });
        return;
      }
      if (!user || !user.id) {
        toast({ title: "Error", description: "You must be logged in.", variant: "destructive" });
        return;
      }

      onUploadStart();
      setUploadProgress(0);
      setExtractedKeywords([]);
      setAiInsights('');
      setExtractedText('');
      setShowAiResults(true);

      if (processingMethod === 'ai') {
        const { tradelines: newTradelines } = await processWithAI(file);
        console.log("AI Processing result:", newTradelines);
        onUploadComplete(newTradelines);
      } else {
        const textContent = await processWithOCR(file);
        console.log("OCR extracted text:", textContent);
        setUploadProgress(80);
        
        const keywords = extractKeywordsFromText(textContent);
        setExtractedKeywords(keywords);
        setAiInsights(generateAIInsights(textContent, keywords));
        setExtractedText(textContent);
        
        try {
          const { parseTradelinesFromText } = await import("@/utils/tradelineParser");
          const parsed = parseTradelinesFromText(textContent, user.id);
          console.log("OCR: Parsed tradelines:", parsed);
          onUploadComplete(parsed);
        } catch (parseError) {
          console.error("OCR tradeline parsing failed:", parseError);
          toast({
            title: "Parsing Error",
            description: "Failed to parse tradelines from text. Try manual entry.",
            variant: "destructive"
          });
        }
        setUploadProgress(100);
      }
      
      toast({
        title: "Upload complete",
        description: `Document processed using ${processingMethod.toUpperCase()}.`
      });
    } catch (error) {
      console.error("PDF processing error:", error instanceof Error ? error.message : String(error));
      const errorMessage = "Failed to process PDF. Please try again or use a different processing method.";
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
