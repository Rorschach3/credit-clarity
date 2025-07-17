import { useEffect, useCallback, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast as sonnerToast } from "sonner";
import { useAuth } from "@/hooks/use-auth";
import { saveTradelinesToDatabase, ParsedTradeline, loadAllTradelinesFromDatabase } from "@/utils/tradelineParser";
import { ManualTradelineModal } from "@/components/disputes/ManualTradelineModal";
import { FileUploadSection } from "@/components/credit-upload/FileUploadSection";
import { TradelinesList } from "@/components/credit-upload/TradelinesList";
import { UploadActions } from "@/components/credit-upload/UploadActions";
import PaginatedTradelinesList from "@/components/credit-upload/PaginatedTradelinesList";
import { useCreditReportProcessing } from "@/hooks/useCreditReportProcessing";
import { useCreditUploadState } from "@/hooks/useCreditUploadState";
import { useFileUploadHandler } from "@/components/credit-upload/FileUploadHandler";
import { usePersistentTradelines } from "@/hooks/usePersistentTradelines";
import { CreditNavbar } from "@/components/navbar/CreditNavbar";
import { TradelinesStatus } from "@/components/ui/tradelines-status";
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
  const testConfigs = [
    {
      baseUrl: 'http://localhost:8000',
      endpoint: '/health',
      needsAuth: false
    },
    {
      baseUrl: 'https://gywohmbqohytziwsjrps.supabase.co/functions/v1',
      endpoint: '/process-credit-report', // Supabase edge function endpoint
      needsAuth: true
    }
  ];

  for (const config of testConfigs) {
    try {
      const healthUrl = `${config.baseUrl}${config.endpoint}`;
      console.log(`🔍 Testing health endpoint: ${healthUrl}`);

      const headers: Record<string, string> = {
        'Accept': 'application/json',
      };

      // Add auth headers for Supabase endpoints
      if (config.needsAuth) {
        const authToken = localStorage.getItem('supabase.auth.token') || 
                         sessionStorage.getItem('supabase.auth.token');

        if (authToken) {
          headers['Authorization'] = `Bearer ${authToken}`;
        }

        const apiKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
        if (apiKey) {
          headers['apikey'] = apiKey;
        }
      }

      const response = await fetch(healthUrl, {
        method: 'GET',
        headers: headers,
      });

      if (response.ok) {
        let data: Record<string, unknown> = {};
        try {
          data = await response.json();
          console.log(`✅ Health check passed for ${config.baseUrl}:`, data);
          return { isHealthy: true, url: config.baseUrl, details: data };
        } catch (jsonError) {
          console.log(`❌ Invalid JSON response from ${config.baseUrl}:`, jsonError);
          continue;
        }
      } else {
        console.log(`❌ Health check failed for ${config.baseUrl}: ${response.status}`);
      }
    } catch (error) {
      console.log(`❌ Health check error for ${config.baseUrl}:`, error);
    }
  }

  return { isHealthy: false, url: '' };
};

const CreditReportUploadPage = () => {
  const { user } = useAuth();
  const saveTimeoutRef = useRef<number>();
  const [processingStep, setProcessingStep] = useState<string>("Waiting for upload...");
  const [showDebugInfo, setShowDebugInfo] = useState<boolean>(false);
  const [usePagination, setUsePagination] = useState<boolean>(false);
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

  // Use persistent tradelines hook
  const {
    tradelines: persistentTradelines,
    loading: tradelinesLoading,
    error: tradelinesError,
    addTradelines,
    updateTradeline: updatePersistentTradeline,
    deleteTradeline: deletePersistentTradeline,
    refreshTradelines
  } = usePersistentTradelines();

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
    cleanup,
    extractKeywordsFromText,
    generateAIInsights
  } = useCreditReportProcessing(user?.id || "");

  // Manage showAiResults locally since it's not in the hook
  // const [showAiResults, setShowAiResults] = useState<boolean>(false);

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
      console.log('[DEBUG] onUploadComplete - user.id:', user?.id);
      console.log('[DEBUG] onUploadComplete - tradelines user_ids:', newTradelines.map(t => t.user_id));
      
      // Ensure all required fields are present and properly typed
      const filledTradelines: ParsedTradeline[] = newTradelines.map(t => ({
        id: t.id ?? `auto-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`,
        user_id: user?.id ?? "",
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

      console.log('🔍 [DEBUG] After processing - user_ids:', filledTradelines.map(t => t.user_id));
      
      // Add new tradelines to persistent storage
      addTradelines(filledTradelines);
      console.log('[DEBUG] Added new tradelines to persistent storage:', filledTradelines.length);
      
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

  // Sync persistent tradelines with local state
  useEffect(() => {
    if (persistentTradelines.length > 0) {
      setTradelines(persistentTradelines);
      console.log('[DEBUG] Synced persistent tradelines to local state:', persistentTradelines.length);
    }
  }, [persistentTradelines, setTradelines]);

  // Show loading notification
  useEffect(() => {
    if (tradelinesLoading) {
      sonnerToast('Loading existing tradelines...', {
        description: 'Fetching from database'
      });
    }
  }, [tradelinesLoading]);

  // Show error notification
  useEffect(() => {
    if (tradelinesError) {
      sonnerToast('Failed to load existing tradelines', {
        description: tradelinesError
      });
    }
  }, [tradelinesError]);

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
    console.log('Debug Information:', debugInfo);
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
      console.log('[DEBUG] saveTradelines - user:', user);
      console.log('[DEBUG] saveTradelines - user.id:', user.id, typeof user.id);
      console.log('[DEBUG] tradelines.length:', tradelines.length);
      console.log('[DEBUG] tradelines array:', tradelines.map((t, i) => ({
        index: i,
        creditor: t.creditor_name,
        account: t.account_number,
        user_id: t.user_id
      })));

      // Ensure we have a valid user ID string
      const userId = typeof user.id === 'string' ? user.id : String(user.id);
      console.log('[DEBUG] saveTradelines - processed userId:', userId);
      console.log('[DEBUG] Calling saveTradelinesToDatabase with:', userId, typeof userId);

      await saveTradelinesToDatabase(tradelines, userId);

      sonnerToast(`Successfully saved ${tradelines.length} tradeline(s) to database.`, { description: "Success" });
    } catch (saveError) {
      const errorMessage = saveError instanceof Error ? saveError.message : 'Unknown error occurred';
      sonnerToast(`Failed to save tradelines: ${errorMessage}`, { description: "Save Failed" });
    }
  }, [user, tradelines]);

  useEffect(() => {
    if (tradelines.length > 0 && user?.id) {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
      saveTimeoutRef.current = setTimeout(() => {
        saveTradelines();
      }, CONSTANTS.SAVE_DELAY_MS) as unknown as number;
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
        id: `manual-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`,
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

              <Button
                variant="outline"
                size="sm"
                onClick={refreshTradelines}
                disabled={tradelinesLoading}
                className="text-xs"
              >
                {tradelinesLoading ? '🔄' : '📊'} Sync DB
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
          {/* Tradelines Status Component */}
          <TradelinesStatus
            loading={tradelinesLoading}
            error={tradelinesError}
            tradelinesCount={persistentTradelines.length}
            onRefresh={refreshTradelines}
          />

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

          {/* View Toggle */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Button
                variant={!usePagination ? "default" : "outline"}
                size="sm"
                onClick={() => setUsePagination(false)}
              >
                Simple View
              </Button>
              <Button
                variant={usePagination ? "default" : "outline"}
                size="sm"
                onClick={() => setUsePagination(true)}
              >
                Paginated View
              </Button>
            </div>
            {!usePagination && (
              <span className="text-sm text-muted-foreground">
                {tradelines.length} tradeline(s)
              </span>
            )}
          </div>

          {/* Tradelines list */}
          {usePagination ? (
            <PaginatedTradelinesList
              userId={user?.id || ""}
              onSelect={handleSelectTradeline}
              onUpdate={updateTradeline}
              onDelete={deleteTradeline}
              selectedIds={selectedTradelineIds}
            />
          ) : (
            <TradelinesList
              tradelines={tradelines}
              selectedTradelineIds={selectedTradelineIds}
              onUpdate={updateTradeline}
              onDelete={deleteTradeline}
              onSelect={handleSelectTradeline}
              onAddManual={() => setManualModalOpen(true)}
            />
          )}

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