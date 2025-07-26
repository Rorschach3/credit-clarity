import React, { useEffect, useCallback, useState, Suspense } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { toast as sonnerToast } from "sonner";

// Hooks
import { useAuth } from "@/hooks/use-auth";
import { usePersistentTradelines } from "@/hooks/usePersistentTradelines";

// Utils
import { saveTradelinesToDatabase } from "@/utils/tradeline/enhanced-database";
import { ParsedTradeline, loadAllTradelinesFromDatabase } from "@/utils/tradelineParser";
import { 
  processFileWithOCR, 
  processFileWithAI, 
  type ProcessingProgress as ProcessingProgressType 
} from '@/utils/asyncProcessing';

// Components
import { CreditNavbar } from "@/components/navbar/CreditNavbar";
import { TradelinesStatus } from "@/components/ui/tradelines-status";
import { ComponentLoading } from "@/components/ui/loading";
import { CreditUploadHeader } from '@/components/credit-upload/CreditUploadHeader';
import { UploadMethodSelector } from '@/components/credit-upload/UploadMethodSelector';
import { ProcessingProgress } from '@/components/credit-upload/ProcessingProgress';

// Lazy loaded components with proper syntax
const FileUploadSection = React.lazy(() => 
  import('@/components/credit-upload/FileUploadSection').then(module => ({
    default: module.FileUploadSection || module.default
  }))
);

const DisplayTradelinesList = React.lazy(() => 
  import('@/components/credit-upload/DisplayTradelinesList').then(module => ({
    default: module.DisplayTradelinesList || module.default
  }))
);

const PaginatedTradelinesList = React.lazy(() => 
  import('@/components/credit-upload/PaginatedTradelinesList')
);

// Error Boundary Component
interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

class ComponentErrorBoundary extends React.Component<
  React.PropsWithChildren<{ fallback?: React.ReactNode; componentName?: string }>,
  ErrorBoundaryState
> {
  constructor(props: React.PropsWithChildren<{ fallback?: React.ReactNode; componentName?: string }>) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error(`Error in ${this.props.componentName || 'Component'}:`, error, errorInfo);
    sonnerToast.error(`Failed to load ${this.props.componentName || 'component'}`, {
      description: "Please refresh the page or try again"
    });
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <p className="text-muted-foreground mb-4">
                Failed to load {this.props.componentName || 'component'}
              </p>
              <Button 
                variant="outline" 
                onClick={() => window.location.reload()}
              >
                Refresh Page
              </Button>
            </div>
          </CardContent>
        </Card>
      );
    }

    return this.props.children;
  }
}

// Enhanced Loading Components
const LoadingCard: React.FC<{ message?: string; height?: string }> = ({ 
  message = "Loading...", 
  height = "h-32" 
}) => (
  <Card>
    <CardContent className={`flex items-center justify-center ${height}`}>
      <ComponentLoading message={message} />
    </CardContent>
  </Card>
);

const SuspenseWrapper: React.FC<{
  children: React.ReactNode;
  fallback?: React.ReactNode;
  errorBoundaryName?: string;
}> = ({ children, fallback, errorBoundaryName }) => (
  <ComponentErrorBoundary componentName={errorBoundaryName}>
    <Suspense fallback={fallback || <LoadingCard />}>
      {children}
    </Suspense>
  </ComponentErrorBoundary>
);

const CreditReportUploadPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  
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
  const [usePagination, setUsePagination] = useState(false);
  const [isLoadingTradelines, setIsLoadingTradelines] = useState(false);
  
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

  // Auto-enable pagination for large datasets
  useEffect(() => {
    setUsePagination(extractedTradelines.length > 20);
  }, [extractedTradelines.length]);

  const loadExistingTradelines = useCallback(async () => {
    if (!user?.id) return;
    
    setIsLoadingTradelines(true);
    try {
      const existing = await loadAllTradelinesFromDatabase(user.id);
      setExtractedTradelines(existing);
    } catch (error) {
      console.error('Error loading existing tradelines:', error);
      sonnerToast.error("Failed to load existing tradelines");
    } finally {
      setIsLoadingTradelines(false);
    }
  }, [user?.id]);

  // Handle file upload and processing
  const handleFileUpload = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    
    if (!file) {
      sonnerToast.error("Please select a file");
      return;
    }
    
    if (!user?.id) {
      sonnerToast.error("Please log in to upload files");
      return;
    }

    // Validate file type and size
    if (!file.type.includes('pdf')) {
      sonnerToast.error("Please upload a PDF file");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      sonnerToast.error("File size must be less than 10MB");
      return;
    }

    setIsProcessing(true);
    setProcessingProgress({ 
      step: 'Starting...', 
      progress: 0, 
      message: 'Preparing to process file' 
    });

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
        description: error instanceof Error ? error.message : "Please try again or contact support"
      });
    } finally {
      setIsProcessing(false);
      // Reset file input
      if (event.target) {
        event.target.value = '';
      }
    }
  }, [user?.id, processingMethod, refreshTradelines]);

  // Handle tradeline deletion
  const handleTradelineDelete = useCallback((tradelineId: string) => {
    setExtractedTradelines(prev => prev.filter(t => t.id !== tradelineId));
    sonnerToast.success("Tradeline removed");
  }, []);

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
          loading={tradelinesLoading || isLoadingTradelines}
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
        <SuspenseWrapper
          fallback={<LoadingCard message="Loading upload interface..." />}
          errorBoundaryName="File Upload"
        >
          <FileUploadSection
            onFileUpload={handleFileUpload}
            isProcessing={isProcessing}
            acceptedFileTypes=".pdf"
            maxFileSize={10 * 1024 * 1024} // 10MB
          />
        </SuspenseWrapper>

        {/* Tradelines Display */}
        {(extractedTradelines.length > 0 || isLoadingTradelines) && (
          <SuspenseWrapper
            fallback={<LoadingCard message="Loading tradelines..." height="h-48" />}
            errorBoundaryName="Tradelines List"
          >
            {isLoadingTradelines ? (
              <LoadingCard message="Loading existing tradelines..." height="h-48" />
            ) : usePagination ? (
              <PaginatedTradelinesList
                userId={user?.id || ""}
                onDelete={handleTradelineDelete}
              />
            ) : (
              <DisplayTradelinesList
                tradelines={extractedTradelines}
              />
            )}
          </SuspenseWrapper>
        )}

        {/* Navigation Buttons */}
        {extractedTradelines.length > 0 && (
          <Card>
            <CardContent className="pt-6">
              <div className="flex justify-between items-center">
                <Button variant="outline" onClick={() => navigate(-1)}>
                  <ChevronLeft className="w-4 h-4 mr-2" />
                  Previous Step
                </Button>
                
                <p className="text-sm text-muted-foreground">
                  Ready to proceed to dispute selection
                </p>
                
                <Button onClick={() => navigate('/disputes')}>
                  Next Step
                  <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

      </div>
    </div>
  );
};

export default CreditReportUploadPage;