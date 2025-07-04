
import React, { useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "@/components/ui/use-toast";
import { useAuth } from "@/hooks/use-auth";
import { saveTradelinesToDatabase } from "@/utils/tradelineParser";
import { ManualTradelineModal } from "@/components/disputes/ManualTradelineModal";
import { ProcessingMethodSelector } from "@/components/credit-upload/ProcessingMethodSelector";
import { FileUploadSection } from "@/components/credit-upload/FileUploadSection";
import { AIAnalysisResults } from "@/components/credit-upload/AIAnalysisResults";
import { TradelinesList } from "@/components/credit-upload/TradelinesList";
import { UploadActions } from "@/components/credit-upload/UploadActions";
import { useCreditReportProcessing } from "@/hooks/useCreditReportProcessing";
import { useCreditUploadState } from "@/hooks/useCreditUploadState";
import { useFileUploadHandler } from "@/components/credit-upload/FileUploadHandler";
import { CreditNavbar } from "@/components/navbar/CreditNavbar";

const CreditReportUploadPage = () => {
  const { user } = useAuth();

  const {
    tradelines,
    setTradelines,
    selectedTradelineIds,
    manualModalOpen,
    setManualModalOpen,
    processingMethod,
    setProcessingMethod,
    showAiResults,
    setShowAiResults,
    handleSelectTradeline,
    updateTradeline,
    deleteTradeline,
    handleAddManual
  } = useCreditUploadState();

  const {
    isUploading,
    uploadProgress,
    extractedKeywords,
    aiInsights,
    extractedText,
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

  const { handleFileUpload } = useFileUploadHandler({
    user,
    processingMethod,
    onUploadStart: () => {
      setIsUploading(true);
      setTradelines([]);
    },
    onUploadComplete: (newTradelines) => {
      setTradelines(newTradelines);
      setIsUploading(false);
      setUploadProgress(0);
    },
    onUploadError: () => {
      setIsUploading(false);
      setUploadProgress(0);
    },
    setUploadProgress,
    setExtractedKeywords,
    setAiInsights,
    setExtractedText,
    setShowAiResults,
    extractKeywordsFromText,
    generateAIInsights
  });

  useEffect(() => {
    if (tradelines.length > 0 && user?.id) {
      const timeoutId = setTimeout(() => {
        saveTradelines();
      }, 1000);
      
      return () => clearTimeout(timeoutId);
    }
  }, [tradelines, user, saveTradelines]);

  const handleManualAdd = (newTradeline: any) => {
    handleAddManual(newTradeline, user?.id || "");
    toast({
      title: "Success",
      description: "Manual tradeline added successfully."
    });
  };

  return (
    <div className="min-h-screen bg-background text-foreground py-10 px-4 md:px-10">
      <CreditNavbar />
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

          <UploadActions
            selectedTradelineIds={selectedTradelineIds}
            tradelines={tradelines}
          />

          {manualModalOpen && (
            <ManualTradelineModal
              onClose={() => setManualModalOpen(false)}
              onAdd={handleManualAdd}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default CreditReportUploadPage;
