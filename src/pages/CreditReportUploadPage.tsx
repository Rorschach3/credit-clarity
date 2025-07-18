import React, { useEffect, useCallback, useState, Suspense } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { toast as sonnerToast } from "sonner";
import { useAuth } from "@/hooks/use-auth";
import { saveTradelinesToDatabase, ParsedTradeline, loadAllTradelinesFromDatabase } from "@/utils/tradelineParser";
import { usePersistentTradelines } from "@/hooks/usePersistentTradelines";
import { CreditNavbar } from "@/components/navbar/CreditNavbar";
import { TradelinesStatus } from "@/components/ui/tradelines-status";
import { ComponentLoading } from "@/components/ui/loading";

// Import lightweight components
import { CreditUploadHeader } from '@/components/credit-upload/CreditUploadHeader';
import { UploadMethodSelector } from '@/components/credit-upload/UploadMethodSelector';
import { ProcessingProgress } from '@/components/credit-upload/ProcessingProgress';

// Lazy load heavy components
const FileUploadSection = React.lazy(() => import('@/components/credit-upload/FileUploadSection').then(module => ({ default: module.FileUploadSection })));
const TradelinesList = React.lazy(() => import('@/components/credit-upload/TradelinesList').then(module => ({ default: module.TradelinesList })));
const PaginatedTradelinesList = React.lazy(() => import('@/components/credit-upload/PaginatedTradelinesList'));
const ManualTradelineModal = React.lazy(() => import('@/components/disputes/ManualTradelineModal').then(module => ({ default: module.ManualTradelineModal })));

// Lazy load processing utilities
import { 
  processFileWithOCR, 
  processFileWithAI, 
  type ProcessingProgress as ProcessingProgressType 
} from '@/utils/asyncProcessing';

type ManualTradelineInput = Omit<ParsedTradeline, 'id' | 'user_id' | 'created_at'>;

const CreditReportUploadPage = () => {
  const { user } = useAuth();
  
  // Core state
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingMethod, setProcessingMethod] = useState<'ocr' | 'ai'>('ai');
  const [processingProgress, setProcessingProgress] = useState<ProcessingProgressType>({
    step: '',
    progress: 0,
    message: ''
  });
  
  // Tradelines state
  const [extractedTradelines, setExtractedTradelines] = useState<ParsedTradeline[]>([]);
  const [showManualModal, setShowManualModal] = useState(false);
  const [usePagination, setUsePagination] = useState(false);
  
  // Use persistent tradelines hook
  const {
    tradelines: persistentTradelines,
    loading: tradelinesLoading,
    error: tradelinesError,
    refreshTradelines
  } = usePersistentTradelines();

  // Load existing tradelines on mount
  useEffect(() => {
    if (user?.id) {
      loadExistingTradelines();
    }
  }, [user?.id]);

  const loadExistingTradelines = async () => {
    if (!user?.id) return;
    
    try {
      const existing = await loadAllTradelinesFromDatabase(user.id);
      setExtractedTradelines(existing);
    } catch (error) {
      console.error('Error loading existing tradelines:', error);
    }
  };

  // Handle file upload and processing
  const handleFileUpload = useCallback(async (file: File) => {
    if (!user?.id) {
      sonnerToast.error("Please log in to upload files");
      return;
    }

    setIsProcessing(true);
    setProcessingProgress({ step: 'Starting...', progress: 0, message: 'Preparing to process file' });

    try {
      let tradelines: ParsedTradeline[] = [];

      if (processingMethod === 'ocr') {
        tradelines = await processFileWithOCR(file, user.id, setProcessingProgress);
      } else {
        tradelines = await processFileWithAI(file, user.id, setProcessingProgress);
      }

      if (tradelines.length > 0) {
        setExtractedTradelines(prev => [...prev, ...tradelines]);
        
        // Auto-save to database
        await saveTradelinesToDatabase(tradelines, user.id);
        await refreshTradelines();
        
        sonnerToast.success(`Successfully extracted ${tradelines.length} tradeline(s)!`, {
          description: "Tradelines have been saved to your account"
        });
      } else {
        sonnerToast.warning("No tradelines found in the uploaded file", {
          description: "Try a different processing method or add tradelines manually"
        });
      }

    } catch (error) {
      console.error('Error processing file:', error);
      sonnerToast.error("Failed to process credit report", {
        description: "Please try again or contact support"
      });
    } finally {
      setIsProcessing(false);
    }
  }, [user?.id, processingMethod, refreshTradelines]);

  // Handle manual tradeline addition
  const handleManualTradelineAdd = useCallback(async (tradeline: ManualTradelineInput) => {
    if (!user?.id) return;

    try {
      const newTradeline: ParsedTradeline = {
        ...tradeline,
        id: crypto.randomUUID(),
        user_id: user.id,
        created_at: new Date().toISOString()
      };

      setExtractedTradelines(prev => [...prev, newTradeline]);
      
      // Save to database
      await saveTradelinesToDatabase([newTradeline], user.id);
      await refreshTradelines();
      
      setShowManualModal(false);
      sonnerToast.success("Tradeline added successfully!");
      
    } catch (error) {
      console.error('Error adding manual tradeline:', error);
      sonnerToast.error("Failed to add tradeline");
    }
  }, [user?.id, refreshTradelines]);

  // Handle tradeline deletion
  const handleTradelineDelete = useCallback((tradelineId: string) => {
    setExtractedTradelines(prev => prev.filter(t => t.id !== tradelineId));
    sonnerToast.success("Tradeline removed");
  }, []);

  // Handle save all tradelines
  const handleSaveAll = useCallback(async () => {
    if (!user?.id || extractedTradelines.length === 0) return;

    try {
      await saveTradelinesToDatabase(extractedTradelines, user.id);
      await refreshTradelines();
      sonnerToast.success("All tradelines saved successfully!");
    } catch (error) {
      console.error('Error saving tradelines:', error);
      sonnerToast.error("Failed to save tradelines");
    }
  }, [user?.id, extractedTradelines, refreshTradelines]);

  // Auto-enable pagination for large datasets
  useEffect(() => {
    setUsePagination(extractedTradelines.length > 20);
  }, [extractedTradelines.length]);

  return (
    <div className="min-h-screen bg-background text-foreground py-10 px-4 md:px-10">
      <CreditNavbar />
      
      <div className="max-w-6xl mx-auto space-y-6">
        
        {/* Header */}
        <Card>
          <CreditUploadHeader />
        </Card>

        {/* Tradelines Status */}
        <TradelinesStatus
          loading={tradelinesLoading}
          error={tradelinesError}
          tradelinesCount={persistentTradelines.length}
          onRefresh={refreshTradelines}
        />

        {/* Processing Method Selection */}
        <UploadMethodSelector
          selectedMethod={processingMethod}
          onMethodChange={setProcessingMethod}
          isProcessing={isProcessing}
        />

        {/* Processing Progress */}
        <ProcessingProgress
          isProcessing={isProcessing}
          progress={processingProgress}
          processingMethod={processingMethod}
        />

        {/* File Upload Section */}
        <Suspense fallback={<ComponentLoading message="Loading upload interface..." />}>
          <FileUploadSection
            onFileUpload={handleFileUpload}
            isProcessing={isProcessing}
            acceptedFileTypes=".pdf"
            maxFileSize={10 * 1024 * 1024} // 10MB
          />
        </Suspense>

        {/* Tradelines Display */}
        {extractedTradelines.length > 0 && (
          <Suspense fallback={<ComponentLoading message="Loading tradelines..." />}>
            {usePagination ? (
              <PaginatedTradelinesList
                tradelines={extractedTradelines}
                onDelete={handleTradelineDelete}
                onSaveAll={handleSaveAll}
                onAddManual={() => setShowManualModal(true)}
              />
            ) : (
              <TradelinesList
                tradelines={extractedTradelines}
                onDelete={handleTradelineDelete}
                onSaveAll={handleSaveAll}
                onAddManual={() => setShowManualModal(true)}
              />
            )}
          </Suspense>
        )}

        {/* Manual Tradeline Modal */}
        {showManualModal && (
          <Suspense fallback={<ComponentLoading message="Loading form..." />}>
            <ManualTradelineModal
              isOpen={showManualModal}
              onClose={() => setShowManualModal(false)}
              onSave={handleManualTradelineAdd}
            />
          </Suspense>
        )}
      </div>
    </div>
  );
};

export default CreditReportUploadPage;