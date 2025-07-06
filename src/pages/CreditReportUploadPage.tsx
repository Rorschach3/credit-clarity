import { useEffect, useCallback, useRef } from "react";
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
import { ParsedTradeline } from "@/utils/tradelineParser";

// Constants for better maintainability
const CONSTANTS = {
  SAVE_DELAY_MS: 1000,
  DEFAULT_VALUES: {
    ACCOUNT_BALANCE: '$0',
    CREDIT_LIMIT: '$0',
    MONTHLY_PAYMENT: '$0',
    ACCOUNT_TYPE: 'credit_card' as const,
    ACCOUNT_STATUS: 'open' as const,
    DISPUTE_COUNT: 0,
    IS_NEGATIVE: false,
  },
  VALIDATION: {
    MAX_CREDITOR_NAME_LENGTH: 100,
    MAX_ACCOUNT_NUMBER_LENGTH: 50,
    MIN_CREDITOR_NAME_LENGTH: 2,
  },
} as const;

// Enhanced type definitions
// Input type for manual tradeline creation (without raw_text)
type ManualTradelineInput = Omit<ParsedTradeline, 'id' | 'user_id' | 'created_at'>;

// Validation result type
interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

// Enhanced error type - removed unused
// interface ValidationError {
//   type: 'validation' | 'network' | 'auth' | 'unknown';
//   message: string;
//   details?: Record<string, unknown>;
// }

// Validation utilities
const validateTradelineInput = (tradeline: ManualTradelineInput): ValidationResult => {
  const errors: string[] = [];

  // Required field validation
  if (!tradeline.creditor_name || tradeline.creditor_name.trim().length < CONSTANTS.VALIDATION.MIN_CREDITOR_NAME_LENGTH) {
    errors.push('Creditor name is required and must be at least 2 characters long');
  }

  if (tradeline.creditor_name && tradeline.creditor_name.length > CONSTANTS.VALIDATION.MAX_CREDITOR_NAME_LENGTH) {
    errors.push(`Creditor name must not exceed ${CONSTANTS.VALIDATION.MAX_CREDITOR_NAME_LENGTH} characters`);
  }

  if (!tradeline.account_number || tradeline.account_number.trim().length === 0) {
    errors.push('Account number is required');
  }

  if (tradeline.account_number && tradeline.account_number.length > CONSTANTS.VALIDATION.MAX_ACCOUNT_NUMBER_LENGTH) {
    errors.push(`Account number must not exceed ${CONSTANTS.VALIDATION.MAX_ACCOUNT_NUMBER_LENGTH} characters`);
  }

  // Date validation
  if (tradeline.date_opened) {
    const dateOpened = new Date(tradeline.date_opened);
    const today = new Date();
    if (dateOpened > today) {
      errors.push('Date opened cannot be in the future');
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
};

// Sanitization utility
const sanitizeTradelineInput = (tradeline: ManualTradelineInput): ManualTradelineInput => {
  return {
    ...tradeline,
    creditor_name: tradeline.creditor_name?.trim() || '',
    account_number: tradeline.account_number?.trim() || '',
    account_balance: tradeline.account_balance?.trim() || CONSTANTS.DEFAULT_VALUES.ACCOUNT_BALANCE,
    credit_limit: tradeline.credit_limit?.trim() || CONSTANTS.DEFAULT_VALUES.CREDIT_LIMIT,
    monthly_payment: tradeline.monthly_payment?.trim() || CONSTANTS.DEFAULT_VALUES.MONTHLY_PAYMENT,
  };
};

const CreditReportUploadPage = () => {
  const { user } = useAuth();
  const saveTimeoutRef = useRef<NodeJS.Timeout>();

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

  // Cleanup effect with proper timeout management
  useEffect(() => {
    return () => {
      cleanup();
      const timeoutId = saveTimeoutRef.current;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [cleanup]);

  // Enhanced saveTradelines with better error handling
  const saveTradelines = useCallback(async () => {
    if (!user?.id || tradelines.length === 0) return;

    try {
      console.log('Saving tradelines to database:', tradelines);
      await saveTradelinesToDatabase(tradelines, user.id);
      console.log(`Saved ${tradelines.length} tradelines to database`);
      toast({
        title: "Success",
        description: `Successfully saved ${tradelines.length} tradeline(s) to database.`,
      });
    } catch (saveError) {
      console.error('Failed to save tradelines:', saveError);
      const errorMessage = saveError instanceof Error ? saveError.message : 'Unknown error occurred';
      toast({
        title: "Save Failed",
        description: `Failed to save tradelines: ${errorMessage}`,
        variant: "destructive"
      });
    }
  }, [user?.id, tradelines]);

  // Enhanced file upload handling with better error management
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
    onUploadError: (error) => {
      console.error('File upload error:', error);
      setIsUploading(false);
      setUploadProgress(0);
      toast({
        title: "Upload Failed",
        description: "Failed to process the uploaded file. Please try again.",
        variant: "destructive"
      });
    },
    setUploadProgress,
    setExtractedKeywords,
    setAiInsights,
    setExtractedText,
    setShowAiResults,
    extractKeywordsFromText,
    generateAIInsights
  });

  // Enhanced auto-save with timeout management
  useEffect(() => {
    if (tradelines.length > 0 && user?.id) {
      // Clear existing timeout
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
      
      // Set new timeout
      saveTimeoutRef.current = setTimeout(() => {
        saveTradelines();
      }, CONSTANTS.SAVE_DELAY_MS);
    }
    
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [tradelines, user?.id, saveTradelines]);

  // Enhanced manual add with validation and error handling
  const handleManualAdd = useCallback(async (newTradeline: ManualTradelineInput) => {
    try {
      // Sanitize input
      const sanitizedTradeline = sanitizeTradelineInput(newTradeline);
      
      // Validate input
      const validation = validateTradelineInput(sanitizedTradeline);
      if (!validation.isValid) {
        toast({
          title: "Validation Error",
          description: validation.errors.join(', '),
          variant: "destructive"
        });
        return;
      }

      // Create complete tradeline object
      const tradelineWithDefaults: ParsedTradeline = {
        ...sanitizedTradeline,
        id: `manual-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        user_id: user?.id || "",
        created_at: new Date().toISOString(),
        account_balance: sanitizedTradeline.account_balance || CONSTANTS.DEFAULT_VALUES.ACCOUNT_BALANCE,
        account_type: sanitizedTradeline.account_type || CONSTANTS.DEFAULT_VALUES.ACCOUNT_TYPE,
        account_status: sanitizedTradeline.account_status || CONSTANTS.DEFAULT_VALUES.ACCOUNT_STATUS,
        credit_limit: sanitizedTradeline.credit_limit || CONSTANTS.DEFAULT_VALUES.CREDIT_LIMIT,
        monthly_payment: sanitizedTradeline.monthly_payment || CONSTANTS.DEFAULT_VALUES.MONTHLY_PAYMENT,
        date_opened: sanitizedTradeline.date_opened || new Date().toISOString().split('T')[0],
        is_negative: sanitizedTradeline.is_negative ?? CONSTANTS.DEFAULT_VALUES.IS_NEGATIVE,
        dispute_count: sanitizedTradeline.dispute_count ?? CONSTANTS.DEFAULT_VALUES.DISPUTE_COUNT,
        creditor_name: sanitizedTradeline.creditor_name || '',
        account_number: sanitizedTradeline.account_number || '',
        credit_bureau: sanitizedTradeline.credit_bureau || "",
      };
      
      await handleAddManual(tradelineWithDefaults, user?.id || "");
      toast({
        title: "Success",
        description: "Manual tradeline added successfully."
      });
    } catch (error) {
      console.error('Failed to add manual tradeline:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to add tradeline';
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
    }
  }, [user?.id, handleAddManual]);

  // Early return for unauthenticated users (after all hooks)
  if (!user?.id) {
    return (
      <div className="min-h-screen bg-background text-foreground py-10 px-4 md:px-10">
        <Card className="max-w-2xl mx-auto">
          <CardContent className="p-6">
            <p className="text-center text-muted-foreground">
              Please log in to access the credit report upload feature.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

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
