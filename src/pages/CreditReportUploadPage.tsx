import { useEffect, useCallback, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast as sonnerToast } from "sonner";
import { useAuth } from "@/hooks/use-auth";
import { saveTradelinesToDatabase } from "@/utils/tradelineParser";
import { ManualTradelineModal } from "@/components/disputes/ManualTradelineModal";
import { FileUploadSection } from "@/components/credit-upload/FileUploadSection";
import { TradelinesList } from "@/components/credit-upload/TradelinesList";
import { UploadActions } from "@/components/credit-upload/UploadActions";
import { useCreditReportProcessing } from "@/hooks/useCreditReportProcessing";
import { useCreditUploadState } from "@/hooks/useCreditUploadState";
import { useFileUploadHandler, ParsedTradeline } from "@/components/credit-upload/FileUploadHandler";
import { CreditNavbar } from "@/components/navbar/CreditNavbar";
import { z } from "zod";

type ManualTradelineInput = Omit<ParsedTradeline, 'id' | 'user_id' | 'created_at'>;

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

interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

// Debug info interface
interface DebugInfo {
  apiConnectivity: boolean;
  lastApiUrl: string;
  environmentCheck: {
    viteApiUrl: string | undefined;
    userAgent: string;
    timestamp: string;
  };
  lastError: string | null;
  processingStats: {
    totalUploads: number;
    successfulUploads: number;
    failedUploads: number;
  };
}

interface HealthCheckResult {
  isHealthy: boolean;
  url: string;
  details?: Record<string, unknown>;
}

const ManualTradelineInputSchema = z.object({
  creditor_name: z.string().min(2).max(CONSTANTS.VALIDATION.MAX_CREDITOR_NAME_LENGTH),
  account_number: z.string().min(1).max(CONSTANTS.VALIDATION.MAX_ACCOUNT_NUMBER_LENGTH),
  account_balance: z.string().optional(),
  credit_limit: z.string().optional(),
  monthly_payment: z.string().optional(),
  account_type: z.string().optional(),
  account_status: z.string().optional(),
  date_opened: z.string().optional(),
  is_negative: z.boolean().optional(),
  dispute_count: z.number().optional(),
  credit_bureau: z.string().optional(),
});

const validateTradelineInput = (tradeline: ManualTradelineInput): ValidationResult => {
  const result = ManualTradelineInputSchema.safeParse(tradeline);
  return {
    isValid: result.success,
    errors: result.success ? [] : result.error.errors.map(e => e.message),
  };
};

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

// Test API connectivity function
const testApiHealth = async (): Promise<HealthCheckResult> => {
  const urls = [
    import.meta.env.VITE_API_URL || 'http://localhost:8000',
    'http://localhost:8000',
    'https://gywohmbqohytziwsjrps.supabase.co/functions/v1'
  ];

  for (const baseUrl of urls) {
    try {
      const healthUrl = `${baseUrl}/health`;
      console.log(`🔍 Testing health endpoint: ${healthUrl}`);
      
      const response = await fetch(healthUrl, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        console.log(`✅ Health check passed for ${baseUrl}:`, data);
        return { isHealthy: true, url: baseUrl, details: data };
      } else {
        console.log(`❌ Health check failed for ${baseUrl}: ${response.status}`);
      }
    } catch (error) {
      console.log(`❌ Health check error for ${baseUrl}:`, error);
    }
  }

  return { isHealthy: false, url: '' };
};

const CreditReportUploadPage = () => {
  const { user } = useAuthGuard();
  const { addCleanup } = useMemoryCleanup();
  const saveTimeoutRef = useRef<NodeJS.Timeout>();
  const [processingStep, setProcessingStep] = useState<string>("Waiting for upload...");
  const [showDebugInfo, setShowDebugInfo] = useState<boolean>(false);
  const [debugInfo, setDebugInfo] = useState<DebugInfo>({
    apiConnectivity: false,
    lastApiUrl: '',
    environmentCheck: {
      viteApiUrl: import.meta.env.VITE_API_URL,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
    },
    lastError: null,
    processingStats: {
      totalUploads: 0,
      successfulUploads: 0,
      failedUploads: 0,
    }
  });

  const {
    tradelines,
    setTradelines,
    selectedTradelineIds,
    manualModalOpen,
    setManualModalOpen,
    processingMethod,
    handleSelectTradeline,
    updateTradeline,
    deleteTradeline,
    handleAddManual
  } = useCreditUploadState();

  const {
    isUploading,
    uploadProgress,
    setIsUploading,
    setUploadProgress,
    setExtractedKeywords,
    setAiInsights,
    setExtractedText,
    cleanup: processingCleanup,
    extractKeywordsFromText,
    generateAIInsights
  } = useCreditReportProcessing(user?.id || "");

  // Enhanced upload handler with debug tracking
  const { handleFileUpload } = useFileUploadHandler({
    user,
    processingMethod,
    onUploadStart: () => {
      setIsUploading(true);
      setTradelines([]);
      setProcessingStep("Starting upload...");
      setDebugInfo(prev => ({
        ...prev,
        processingStats: {
          ...prev.processingStats,
          totalUploads: prev.processingStats.totalUploads + 1,
        }
      }));
    },
    onUploadComplete: (newTradelines: ParsedTradeline[]) => {
      // Ensure all required fields are present and properly typed
      const filledTradelines: ParsedTradeline[] = newTradelines.map(t => ({
        id: t.id ?? `auto-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        user_id: t.user_id ?? user?.id ?? "",
        creditor_name: t.creditor_name ?? "",
        account_number: t.account_number ?? "",
        account_balance: t.account_balance ?? CONSTANTS.DEFAULT_VALUES.ACCOUNT_BALANCE,
        created_at: t.created_at ?? new Date().toISOString(),
        credit_limit: t.credit_limit ?? CONSTANTS.DEFAULT_VALUES.CREDIT_LIMIT,
        monthly_payment: t.monthly_payment ?? CONSTANTS.DEFAULT_VALUES.MONTHLY_PAYMENT,
        date_opened: t.date_opened ?? new Date().toISOString().split('T')[0],
        is_negative: t.is_negative ?? CONSTANTS.DEFAULT_VALUES.IS_NEGATIVE,
        account_type: t.account_type ?? CONSTANTS.DEFAULT_VALUES.ACCOUNT_TYPE,
        account_status: t.account_status ?? CONSTANTS.DEFAULT_VALUES.ACCOUNT_STATUS,
        dispute_count: t.dispute_count ?? CONSTANTS.DEFAULT_VALUES.DISPUTE_COUNT,
        credit_bureau: t.credit_bureau ?? "",
      }));
      
      setTradelines(filledTradelines);
      setIsUploading(false);
      setUploadProgress(0);
      setProcessingStep("Upload completed successfully!");
      
      setDebugInfo(prev => ({
        ...prev,
        processingStats: {
          ...prev.processingStats,
          successfulUploads: prev.processingStats.successfulUploads + 1,
        },
        lastError: null,
      }));
    },
    onUploadError: (error: string) => {
      console.error('File upload error:', error);
      setIsUploading(false);
      setUploadProgress(0);
      setProcessingStep("Upload failed");
      sonnerToast("Upload Failed: Failed to process the uploaded file. Please try again.", { description: "Upload Error" });
      
      setDebugInfo(prev => ({
        ...prev,
        processingStats: {
          ...prev.processingStats,
          failedUploads: prev.processingStats.failedUploads + 1,
        },
        lastError: error,
      }));
    },
    setUploadProgress,
    setExtractedKeywords,
    setAiInsights,
    setExtractedText,
    extractKeywordsFromText,
    generateAIInsights
  });

  // Test API connectivity on component mount
  useEffect(() => {
    const checkApiHealth = async () => {
      const healthResult = await testApiHealth();
      setDebugInfo(prev => ({
        ...prev,
        apiConnectivity: healthResult.isHealthy,
        lastApiUrl: healthResult.url,
      }));
    };

    checkApiHealth();
  }, []);

  const displayProcessingSteps = () => {
    sonnerToast(`Processing Step: ${processingStep}`, { description: "Status" });
  };

  const displayDebugInfo = () => {
    console.log('🔍 Debug Information:', debugInfo);
    setShowDebugInfo(!showDebugInfo);
  };

  const runApiTest = async () => {
    sonnerToast("Testing API connectivity...", { description: "Running Tests" });
    
    const healthResult = await testApiHealth();
    setDebugInfo(prev => ({
      ...prev,
      apiConnectivity: healthResult.isHealthy,
      lastApiUrl: healthResult.url,
    }));

    if (healthResult.isHealthy) {
      sonnerToast(`✅ API is accessible at ${healthResult.url}`, { description: "Connection Test Passed" });
    } else {
      sonnerToast("❌ API is not accessible. Check if backend is running.", { description: "Connection Test Failed" });
    }
  };

  useEffect(() => {
    return () => {
      cleanup();
      const timeoutId = saveTimeoutRef.current;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [cleanup]);

  const saveTradelines = useCallback(async () => {
    if (!user?.id || tradelines.length === 0) return;
    try {
      await saveTradelinesToDatabase(tradelines, user.id);
      sonnerToast(`Successfully saved ${tradelines.length} tradeline(s) to database.`, { description: "Success" });
    } catch (saveError) {
      const errorMessage = saveError instanceof Error ? saveError.message : 'Unknown error occurred';
      sonnerToast(`Failed to save tradelines: ${errorMessage}`, { description: "Save Failed" });
    }
  }, [user?.id, tradelines]);

  useEffect(() => {
    if (tradelines.length > 0 && user?.id) {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
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

  const handleManualAdd = useCallback(async (newTradeline: ManualTradelineInput) => {
    try {
      const sanitizedTradeline = sanitizeTradelineInput(newTradeline);
      const validation = validateTradelineInput(sanitizedTradeline);
      if (!validation.isValid) {
        sonnerToast(validation.errors.join(', '), { description: "Validation Error" });
        return;
      }
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
      sonnerToast("Manual tradeline added successfully.", { description: "Success" });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to add tradeline';
      sonnerToast(errorMessage, { description: "Error" });
    }
  }, [user?.id, handleAddManual]);

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
          <CardTitle className="text-2xl flex items-center justify-between">
            Step 1: Upload or Add Tradelines
            
            {/* Debug Controls */}
            <div className="flex gap-2">
              <Badge 
                variant={debugInfo.apiConnectivity ? "default" : "destructive"}
                className="text-xs"
              >
                API: {debugInfo.apiConnectivity ? "✅ Connected" : "❌ Disconnected"}
              </Badge>
              
              <Button 
                variant="outline" 
                size="sm"
                onClick={runApiTest}
                className="text-xs"
              >
                🔍 Test API
              </Button>
              
              <Button 
                variant="outline" 
                size="sm"
                onClick={displayDebugInfo}
                className="text-xs"
              >
                🐛 Debug Info
              </Button>
            </div>
          </CardTitle>
          
          {/* Debug Information Panel */}
          {showDebugInfo && (
            <div className="mt-4 p-4 bg-muted rounded-lg text-sm">
              <h3 className="font-semibold mb-2">🔧 Debug Information</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <strong>Environment:</strong>
                  <ul className="mt-1 text-xs space-y-1">
                    <li>VITE_API_URL: {debugInfo.environmentCheck.viteApiUrl || 'Not set'}</li>
                    <li>User Agent: {debugInfo.environmentCheck.userAgent.slice(0, 50)}...</li>
                    <li>Timestamp: {new Date(debugInfo.environmentCheck.timestamp).toLocaleString()}</li>
                  </ul>
                </div>
                <div>
                  <strong>Processing Stats:</strong>
                  <ul className="mt-1 text-xs space-y-1">
                    <li>Total Uploads: {debugInfo.processingStats.totalUploads}</li>
                    <li>Successful: {debugInfo.processingStats.successfulUploads}</li>
                    <li>Failed: {debugInfo.processingStats.failedUploads}</li>
                  </ul>
                </div>
              </div>
              
              {debugInfo.lastApiUrl && (
                <div className="mt-2">
                  <strong>Last API URL:</strong> {debugInfo.lastApiUrl}
                </div>
              )}
              
              {debugInfo.lastError && (
                <div className="mt-2">
                  <strong>Last Error:</strong> 
                  <div className="bg-red-100 text-red-800 p-2 rounded mt-1 text-xs">
                    {debugInfo.lastError}
                  </div>
                </div>
              )}
            </div>
          )}
        </CardHeader>
        
        <CardContent className="space-y-6">
          <div className="flex gap-4 text-sm">
            <button onClick={displayProcessingSteps} className="underline text-blue-600">
              Show Status
            </button>
            <button onClick={() => console.log('Current tradelines:', tradelines)} className="underline text-green-600">
              Log Tradelines
            </button>
            <button onClick={() => window.open('http://localhost:8000/health', '_blank')} className="underline text-purple-600">
              Open Health Check
            </button>
          </div>
          
          {/* File upload section */}
          <FileUploadSection
            onFileUpload={handleFileUpload}
            isUploading={isUploading}
            uploadProgress={uploadProgress}
            processingMethod={processingMethod}
          />
          
          {/* Processing status */}
          {isUploading && (
            <Card className="bg-blue-50 border-blue-200">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Processing: {processingStep}</span>
                  <span className="text-xs text-muted-foreground">{uploadProgress}%</span>
                </div>
                <div className="w-full bg-blue-200 rounded-full h-2 mt-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
              </CardContent>
            </Card>
          )}
          
          {/* Tradelines list */}
          <TradelinesList
            tradelines={tradelines}
            selectedTradelineIds={selectedTradelineIds}
            onUpdate={updateTradeline}
            onDelete={deleteTradeline}
            onSelect={handleSelectTradeline}
            onAddManual={() => setManualModalOpen(true)}
          />
          
          {/* Upload actions */}
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
}

export default CreditReportUploadPage;