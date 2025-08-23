/**
 * Enhanced File Upload Handler with Real-time WebSocket Progress
 * Replaces polling with real-time WebSocket updates for better user experience
 */
import { ChangeEvent, useCallback, useEffect, useState } from 'react';
import { toast as sonnerToast } from "sonner";
import { ParsedTradeline, ParsedTradelineSchema } from "@/utils/tradelineParser";
import { useRealtime, useJobProgress } from "@/hooks/useRealtime";
import { useAuth } from "@/hooks/use-auth";
import { useUploadRetry } from "@/hooks/useRetry";
import { useErrorReporting } from "@/components/error/GlobalErrorHandler";
import { useMonitoring } from "@/hooks/useMonitoring";
import { v4 as uuidv4 } from 'uuid';

// Progress stages for real-time updates
const PROGRESS_STAGES = {
  VALIDATION: 5,
  CONNECTIVITY_CHECK: 10,
  UPLOADING: 20,
  PROCESSING: 30,
  PARSING: 80,
  SAVING: 90,
  COMPLETE: 100,
} as const;

// Enhanced progress interface
interface JobProgress {
  progress: number;
  message: string;
  stage?: string;
  tradelines_found?: number;
  estimated_time_remaining?: number;
}

interface RealtimeFileUploadHandlerProps {
  user: { id: string; email?: string } | null;
  processingMethod: 'ocr' | 'ai';
  onUploadStart: () => void;
  onUploadComplete: (tradelines: ParsedTradeline[]) => void;
  onUploadError: (error: string) => void;
  setUploadProgress: (progress: number) => void;
  setProgressMessage?: (message: string) => void;
  setEstimatedTime?: (timeMs: number | null) => void;
  setTradelinesFound?: (count: number) => void;
  setExtractedKeywords: (keywords: string[]) => void;
  setAiInsights: (insights: string) => void;
  setExtractedText: (text: string) => void;
  setShowAiResults?: (show: boolean) => void;
  extractKeywordsFromText: (text: string) => string[];
  generateAIInsights: (text: string, keywords: string[]) => string;
}

// Sanitize tradelines before validation
function sanitizeTradelines(tradelines: ParsedTradeline[]): ParsedTradeline[] {
  return tradelines.map((t) => {
    const credit_bureau = typeof t.credit_bureau === 'string' && t.credit_bureau.trim().length > 0
      ? t.credit_bureau.trim()
      : '';

    return {
      ...t,
      credit_bureau,
    };
  });
}

// File validation
const validateFile = (file: File): void => {
  const allowedTypes = ['application/pdf'];
  const maxSize = 50 * 1024 * 1024; // 50MB for better large file support
  const minSize = 100; // 100 bytes minimum

  console.log(`🔍 Validating file: ${file.name}, type: ${file.type}, size: ${file.size}`);

  if (!allowedTypes.includes(file.type)) {
    throw new Error('Only PDF files are supported.');
  }

  if (file.size > maxSize) {
    throw new Error(`File size exceeds 50MB limit.`);
  }

  if (file.size < minSize) {
    throw new Error('File appears to be empty.');
  }

  if (!file.name.toLowerCase().endsWith('.pdf')) {
    throw new Error('File must have a .pdf extension.');
  }

  console.log('✅ File validation passed');
};

// Enhanced API Response interface
interface ApiResponse {
  success: boolean;
  message?: string;
  data?: {
    job_id?: string;
    status: string;
    tradelines_found?: number;
    processing_method?: string;
    cost_estimate?: number;
    performance_metrics?: any;
  };
  tradelines?: Array<{
    user_id?: string;
    creditor_name?: string;
    account_balance?: string;
    credit_limit?: string;
    monthly_payment?: string;
    account_number?: string;
    date_opened?: string;
    account_type?: string;
    account_status?: string;
    credit_bureau?: string;
    is_negative?: boolean;
    dispute_count?: number;
  }>;
}

export function useRealtimeFileUploadHandler(props: RealtimeFileUploadHandlerProps) {
  const {
    user,
    processingMethod,
    onUploadStart,
    onUploadComplete,
    onUploadError,
    setUploadProgress,
    setProgressMessage,
    setEstimatedTime,
    setTradelinesFound,
    setExtractedKeywords,
    setAiInsights,
    setExtractedText,
    setShowAiResults,
    extractKeywordsFromText,
    generateAIInsights,
  } = props;

  const { getToken } = useAuth();
  const { isConnected } = useRealtime();
  const { executeWithRetry, retryState } = useUploadRetry({
    onRetry: (attempt, error) => {
      if (setProgressMessage) {
        setProgressMessage(`Upload failed, retrying... (${attempt}/2)`);
      }
      trackEvent('upload_retry', { attempt, error: error.message });
    },
    onFailure: (error, attempts) => {
      trackError(error, { 
        component: 'RealtimeFileUploadHandler',
        attempts,
        userId: user?.id 
      });
    }
  });
  const { reportAsyncError } = useErrorReporting();
  const { trackEvent, trackError, startTiming } = useMonitoring();
  
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  
  // Use job progress hook for real-time updates
  const jobProgress = useJobProgress(currentJobId || undefined);

  // Handle real-time progress updates
  useEffect(() => {
    if (jobProgress && currentJobId) {
      console.log(`📊 Real-time progress update:`, jobProgress);
      
      setUploadProgress(jobProgress.progress);
      
      if (setProgressMessage) {
        setProgressMessage(jobProgress.message);
      }
      
      if (setEstimatedTime && jobProgress.estimated_time_remaining) {
        setEstimatedTime(jobProgress.estimated_time_remaining);
      }
      
      if (setTradelinesFound && jobProgress.tradelines_found !== undefined) {
        setTradelinesFound(jobProgress.tradelines_found);
      }

      // Handle completion
      if (jobProgress.progress >= 100 && jobProgress.stage === 'completed') {
        handleJobCompletion();
      }
    }
  }, [jobProgress, currentJobId, setUploadProgress, setProgressMessage, setEstimatedTime, setTradelinesFound]);

  const handleJobCompletion = useCallback(async () => {
    if (!currentJobId) return;

    try {
      // Fetch final results
      const token = await getToken();
      const response = await fetch(`/api/v1/processing/job/${currentJobId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to get job results: ${response.statusText}`);
      }

      const result = await response.json();
      
      if (result.success && result.data?.result?.tradelines) {
        const tradelines = sanitizeTradelines(result.data.result.tradelines);
        onUploadComplete(tradelines);
        
        sonnerToast.success('Processing completed!', {
          description: `Found ${tradelines.length} tradelines`,
        });
      } else {
        throw new Error(result.message || 'No tradelines found in results');
      }
    } catch (error) {
      console.error('Failed to get job completion results:', error);
      onUploadError(error instanceof Error ? error.message : 'Failed to retrieve results');
    } finally {
      setIsProcessing(false);
      setCurrentJobId(null);
    }
  }, [currentJobId, getToken, onUploadComplete, onUploadError]);

  const processCreditReportWithRealtime = useCallback(async (file: File): Promise<void> => {
    if (!user?.id) {
      throw new Error('User authentication required');
    }

    const timer = startTiming('upload_process_duration');
    
    console.log(`🚀 Starting real-time processing for file: ${file.name}`);
    
    // Track upload start
    trackEvent('upload_started', {
      fileName: file.name,
      fileSize: file.size,
      processingMethod,
      userId: user.id
    });
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('save_to_database', 'true');
    formData.append('priority', file.size > 3 * 1024 * 1024 ? 'normal' : 'high'); // Large files use background processing

    // Get API endpoint
    const getApiEndpoint = () => {
      const envUrl = import.meta.env.VITE_API_URL;
      
      if (envUrl) {
        return `${envUrl}/api/v1/processing/upload`;
      }
      
      // Fallback logic
      const protocol = window.location.protocol;
      const host = window.location.hostname;
      const port = window.location.hostname === 'localhost' ? ':8000' : '';
      
      return `${protocol}//${host}${port}/api/v1/processing/upload`;
    };

    try {
      const token = await getToken();
      if (!token) {
        throw new Error('No authentication token available');
      }

      const apiTimer = startTiming('api_call_duration');
      const response = await fetch(getApiEndpoint(), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });
      
      const apiDuration = apiTimer.end({
        endpoint: 'upload',
        method: 'POST',
        status: response.status.toString()
      });

      if (!response.ok) {
        const error = new Error(`Upload failed: ${response.status} ${response.statusText}`);
        trackError(error, {
          component: 'RealtimeFileUploadHandler',
          action: 'upload_request',
          status: response.status,
          fileName: file.name
        });
        throw error;
      }

      const result: ApiResponse = await response.json();
      
      if (!result.success) {
        throw new Error(result.message || 'Upload failed');
      }

      // Handle different response types
      if (result.data?.job_id) {
        // Background processing - track with WebSocket
        console.log(`📋 Background job started: ${result.data.job_id}`);
        setCurrentJobId(result.data.job_id);
        
        trackEvent('upload_job_started', {
          jobId: result.data.job_id,
          fileName: file.name,
          processingMethod: result.data.processing_method,
          isBackground: true
        });
        
        sonnerToast.info('Processing started', {
          description: 'Your file is being processed. You\'ll receive real-time updates.',
        });
        
        // Initial progress update
        setUploadProgress(PROGRESS_STAGES.PROCESSING);
        if (setProgressMessage) {
          setProgressMessage('Processing in background...');
        }
        
      } else if (result.tradelines) {
        // Synchronous processing - immediate results
        console.log(`✅ Synchronous processing completed`);
        const tradelines = sanitizeTradelines(result.tradelines);
        
        const duration = timer.end({ 
          success: true, 
          tradelineCount: tradelines.length,
          processingType: 'synchronous'
        });
        
        trackEvent('upload_completed', {
          fileName: file.name,
          tradelineCount: tradelines.length,
          duration,
          processingType: 'synchronous',
          success: true
        });
        
        setUploadProgress(PROGRESS_STAGES.COMPLETE);
        onUploadComplete(tradelines);
        setIsProcessing(false);
        
        sonnerToast.success('Processing completed!', {
          description: `Found ${tradelines.length} tradelines`,
        });
      } else {
        throw new Error('Unexpected response format');
      }

    } catch (error) {
      console.error('❌ Credit report processing failed:', error);
      
      const duration = timer.end({ 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      
      trackEvent('upload_failed', {
        fileName: file.name,
        duration,
        error: error instanceof Error ? error.message : 'Unknown error',
        processingMethod
      });
      
      setIsProcessing(false);
      throw error;
    }
  }, [user, getToken, setUploadProgress, setProgressMessage, onUploadComplete]);

  const resetState = useCallback(() => {
    setUploadProgress(0);
    setCurrentJobId(null);
    setIsProcessing(false);
    
    if (setProgressMessage) setProgressMessage('');
    if (setEstimatedTime) setEstimatedTime(null);
    if (setTradelinesFound) setTradelinesFound(0);
    if (setShowAiResults) setShowAiResults(false);
    
    setExtractedKeywords([]);
    setAiInsights('');
    setExtractedText('');
  }, [setUploadProgress, setProgressMessage, setEstimatedTime, setTradelinesFound, setShowAiResults, setExtractedKeywords, setAiInsights, setExtractedText]);

  const handleFileUpload = useCallback(async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Reset state
    resetState();
    
    // Check WebSocket connection
    if (!isConnected) {
      sonnerToast.warning('Real-time connection unavailable', {
        description: 'Processing will work, but you won\'t receive live updates.',
      });
    }

    await reportAsyncError(async () => {
      await executeWithRetry(async () => {
      // Validation
      setUploadProgress(PROGRESS_STAGES.VALIDATION);
      if (setProgressMessage) setProgressMessage('Validating file...');
      
      validateFile(file);
      
      if (!user?.id) {
        throw new Error('Please log in to upload files.');
      }

      // Start processing
      onUploadStart();
      setIsProcessing(true);
      
      setUploadProgress(PROGRESS_STAGES.UPLOADING);
      if (setProgressMessage) setProgressMessage('Starting upload...');

        await processCreditReportWithRealtime(file);
      });
    }, {
      component: 'RealtimeFileUploadHandler',
      action: 'file_upload',
      fileName: file.name,
      userId: user?.id
    }).catch((error) => {
      console.error('Upload process failed:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      
      onUploadError(errorMessage);
      setIsProcessing(false);
      
      sonnerToast.error('Upload failed', {
        description: errorMessage,
      });
    });
  }, [user, isConnected, resetState, onUploadStart, setUploadProgress, setProgressMessage, processCreditReportWithRealtime, onUploadError, executeWithRetry, reportAsyncError, trackEvent]);

  return {
    handleFileUpload,
    isProcessing: isProcessing || retryState.isRetrying,
    currentJobId,
    isRealtimeConnected: isConnected,
    resetState,
    retryState,
  };
}

// Legacy compatibility wrapper
export function RealtimeFileUploadHandler(props: RealtimeFileUploadHandlerProps) {
  const { handleFileUpload } = useRealtimeFileUploadHandler(props);
  
  return (
    <input
      type="file"
      accept=".pdf"
      onChange={handleFileUpload}
      className="hidden"
      id="file-upload"
    />
  );
}