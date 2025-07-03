
import React, { useState, useEffect, useCallback, ChangeEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "@/components/ui/use-toast";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { saveTradelinesToDatabase, ParsedTradeline } from "@/utils/tradelineParser";
import { ManualTradelineModal } from "@/components/disputes/ManualTradelineModal";
import { ProcessingMethodSelector } from "@/components/credit-upload/ProcessingMethodSelector";
import { FileUploadSection } from "@/components/credit-upload/FileUploadSection";
import { AIAnalysisResults } from "@/components/credit-upload/AIAnalysisResults";
import { TradelinesList } from "@/components/credit-upload/TradelinesList";
import { useCreditReportProcessing } from "@/hooks/useCreditReportProcessing";

const CreditReportUploadPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [tradelines, setTradelines] = useState<ParsedTradeline[]>([]);
  const [selectedTradelineIds, setSelectedTradelineIds] = useState<Set<string>>(new Set());
  const [manualModalOpen, setManualModalOpen] = useState(false);
  const [processingMethod, setProcessingMethod] = useState<'ocr' | 'ai'>('ai');
  const [showAiResults, setShowAiResults] = useState(false);

  const {
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
  } = useCreditReportProcessing(user?.id || "");

  useEffect(() => {
    return cleanup;
  }, [cleanup]);

  const handleSelectTradeline = (id: string, isSelected: boolean) => {
    setSelectedTradelineIds(prev => {
      const newSet = new Set(prev);
      if (isSelected) {
        newSet.add(id);
      } else {
        newSet.delete(id);
      }
      return newSet;
    });
  };

  const saveTradelines = useCallback(async () => {
    if (user && tradelines.length > 0) {
      try {
        console.log('Saving tradelines to database:', tradelines);
        await saveTradelinesToDatabase(tradelines, user.id);
        console.log(`Saved ${tradelines.length} tradelines to database`);
      } catch (saveError) {
        console.error('Failed to save tradelines:', saveError);
        toast({
          title: "Save Warning",
          description: "Tradelines extracted but failed to save to database.",
          variant: "destructive"
        });
      }
    }
  }, [user, tradelines]);

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

      setIsUploading(true);
      setTradelines([]);
      setUploadProgress(0);
      setExtractedKeywords([]);
      setAiInsights('');
      setExtractedText('');
      setShowAiResults(true);

      if (processingMethod === 'ai') {
        const { tradelines: newTradelines } = await processWithAI(file);
        console.log("AI Processing result:", newTradelines);
        setTradelines(newTradelines);
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
          setTradelines(parsed);
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
      toast({
        title: "Error",
        description: "Failed to process PDF. Please try again or use a different processing method.",
        variant: "destructive"
      });
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  useEffect(() => {
    if (tradelines.length > 0 && user?.id) {
      const timeoutId = setTimeout(() => {
        saveTradelines();
      }, 1000);
      
      return () => clearTimeout(timeoutId);
    }
  }, [tradelines, user, saveTradelines]);

  const updateTradeline = (index: number, updated: Partial<ParsedTradeline>) => {
    setTradelines((prev) => {
      const newTradelines = [...prev];
      newTradelines[index] = { ...newTradelines[index], ...updated };
      console.log("Updated tradeline:", newTradelines[index]);
      return newTradelines;
    });
  };

  const deleteTradeline = (index: number) => {
    setTradelines((prev) => prev.filter((_, i) => i !== index));
  };

  const handleProceed = () => {
    const selectedTradelines = tradelines.filter(t => selectedTradelineIds.has(t.id || ''));
    console.log("Proceeding with selected tradelines:", selectedTradelines);
    
    navigate("/dispute-letter", {
      state: {
        selectedTradelineIds: Array.from(selectedTradelineIds),
        selectedTradelines: selectedTradelines
      }
    });
  };

  const handleAddManual = (newTradeline: ParsedTradeline) => {
    const tradelineWithUserId = {
      ...newTradeline,
      user_id: user?.id || ""
    };
    setTradelines(prev => [...prev, tradelineWithUserId]);
    setManualModalOpen(false);
    toast({
      title: "Success",
      description: "Manual tradeline added successfully."
    });
  };

  return (
    <div className="min-h-screen bg-background text-foreground py-10 px-4 md:px-10">
      <Card className="max-w-6xl mx-auto space-y-6">
        <CardHeader>
          <CardTitle className="text-2xl">Step 1: Upload or Add Tradelines</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <ProcessingMethodSelector
            processingMethod={processingMethod}
            onMethodChange={setProcessingMethod}
          />
          
          <FileUploadSection
            onFileUpload={handleFileUpload}
            isUploading={isUploading}
            uploadProgress={uploadProgress}
            processingMethod={processingMethod}
          />

          {showAiResults && (extractedKeywords.length > 0 || aiInsights || extractedText) && (
            <AIAnalysisResults
              keywords={extractedKeywords}
              insights={aiInsights}
              extractedText={extractedText}
            />
          )}

          <TradelinesList
            tradelines={tradelines}
            selectedTradelineIds={selectedTradelineIds}
            onUpdate={updateTradeline}
            onDelete={deleteTradeline}
            onSelect={handleSelectTradeline}
            onAddManual={() => setManualModalOpen(true)}
          />

          <div className="flex justify-end space-x-4">
            <Button onClick={handleProceed} disabled={selectedTradelineIds.size === 0}>
              Proceed to Step 2 ({selectedTradelineIds.size} selected)
            </Button>
          </div>

          {manualModalOpen && (
            <ManualTradelineModal
              onClose={() => setManualModalOpen(false)}
              onAdd={handleAddManual}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default CreditReportUploadPage;
