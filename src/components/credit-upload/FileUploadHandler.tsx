import { ChangeEvent, useCallback } from 'react';
import { toast as sonnerToast } from "sonner";
import { ParsedTradeline, ParsedTradelineSchema } from "@/utils/tradelineParser";
import { v4 as uuidv4 } from 'uuid';


// Sanitize tradelines before validation
function sanitizeTradelines(tradelines: ParsedTradeline[]): ParsedTradeline[] {
  return tradelines.map((t) => {

    // Ensure credit_bureau is a non-empty string
    const credit_bureau = typeof t.credit_bureau === 'string' && t.credit_bureau.trim().length > 0
      ? t.credit_bureau.trim()
      : ''; // You can change this default if desired

    return {
      ...t,
      credit_bureau,
    };
  });
}

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
  setShowAiResults?: (show: boolean) => void; // Made optional
  extractKeywordsFromText: (text: string) => string[];
  generateAIInsights: (text: string, keywords: string[]) => string;
}

// File validation
const validateFile = (file: File): void => {
  const allowedTypes = ['application/pdf'];
  const maxSize = 10 * 1024 * 1024; // 10MB
  const minSize = 100; // 100 bytes minimum

  console.log(`🔍 Validating file: ${file.name}, type: ${file.type}, size: ${file.size}`);

  if (!allowedTypes.includes(file.type)) {
    throw new Error('Only PDF files are supported.');
  }

  if (file.size > maxSize) {
    throw new Error(`File size exceeds 10MB limit.`);
  }

  if (file.size < minSize) {
    throw new Error('File appears to be empty.');
  }

  if (!file.name.toLowerCase().endsWith('.pdf')) {
    throw new Error('File must have a .pdf extension.');
  }

  console.log('✅ File validation passed');
};

// API Response interface to match backend response
interface ApiResponse {
  success: boolean;
  message?: string;
  tradelines: Array<{
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

// Enhanced API function with better auth debugging
const processCreditReportWithAPI = async (file: File, userId: string): Promise<ParsedTradeline[]> => {
  console.log(`🚀 Starting API call for file: ${file.name}, user: ${userId}`);
  
  const formData = new FormData();
  formData.append('file', file);
  formData.append('user_id', userId);

  // Enhanced URL handling with proper endpoint construction
  const getApiEndpoint = () => {
    const envUrl = import.meta.env.VITE_API_URL;
    
    if (envUrl) {
      console.log(`🌐 Using VITE_API_URL: ${envUrl}`);
      
      // Check if the URL already includes the endpoint
      if (envUrl.includes('/process-credit-report')) {
        // URL already has the endpoint, use as-is
        return envUrl;
      } else {
        // Add the endpoint to the base URL
        return `${envUrl}/process-credit-report`;
      }
    }

    // Fallback to localhost
    console.log(`🌐 Using localhost fallback`);
    return 'http://localhost:8000/process-credit-report';
  };

  const endpoint = getApiEndpoint();
  
  console.log(`📡 Making request to: ${endpoint}`);
  console.log(`📦 FormData contents:`, {
    file: file.name,
    user_id: userId,
    fileSize: file.size,
    fileType: file.type
  });

  // Prepare headers with enhanced auth debugging
  const headers: Record<string, string> = {};
  
  // Add Supabase auth headers if using Supabase endpoint
  if (endpoint.includes('supabase.co')) {
    console.log(`🔐 Supabase endpoint detected, adding authentication headers`);
    
    // Method 1: Try to get auth token from Supabase auth state
    let authToken = null;
    
    // Check multiple possible locations for auth token
    const possibleTokenSources = [
      () => localStorage.getItem('sb-gywohmbqohytziwsjrps-auth-token'),
      () => localStorage.getItem('supabase.auth.token'),
      () => sessionStorage.getItem('supabase.auth.token'),
      () => {
        // Try to get from Supabase auth state
        const authData = localStorage.getItem('sb-gywohmbqohytziwsjrps-auth-token');
        if (authData) {
          try {
            const parsed = JSON.parse(authData);
            return parsed.access_token || parsed.token;
          } catch (e) {
            return null;
          }
        }
        return null;
      }
    ];
    
    for (const getToken of possibleTokenSources) {
      try {
        authToken = getToken();
        if (authToken) {
          console.log(`✅ Found auth token from source, length: ${authToken.length}`);
          break;
        }
      } catch (e) {
        console.log(`⚠️ Error getting token from source:`, e);
      }
    }
    
    // Method 2: Fallback to environment variable anon key
    const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
    
    console.log(`🔍 Auth Debug Info:`);
    console.log(`  - User Auth Token: ${authToken ? `Found (${authToken.substring(0, 20)}...)` : 'Not found'}`);
    console.log(`  - Anon Key: ${anonKey ? `Found (${anonKey.substring(0, 20)}...)` : 'Not found'}`);
    
    // Set authorization header
    if (authToken) {
      headers['Authorization'] = `Bearer ${authToken}`;
      console.log(`✅ Using user auth token for Authorization header`);
    } else if (anonKey) {
      headers['Authorization'] = `Bearer ${anonKey}`;
      console.log(`✅ Using anon key for Authorization header`);
    } else {
      console.error(`❌ No auth token or anon key found! This will cause 401 error.`);
    }
    
    // Always add apikey header for Supabase
    if (anonKey) {
      headers['apikey'] = anonKey;
      console.log(`✅ Added apikey header`);
    }
    
    // Add content type hint for Supabase
    headers['Accept'] = 'application/json';
    
    console.log(`📋 Final headers for Supabase request:`, Object.keys(headers));
  } else {
    console.log(`🌐 Local endpoint detected, no auth headers needed`);
  }

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      body: formData,
      headers: headers,
    });

    console.log(`📨 Response status: ${response.status} ${response.statusText}`);
    console.log(`📨 Response headers:`, Object.fromEntries(response.headers.entries()));

    if (!response.ok) {
      let errorData: { detail?: string; message?: string; code?: number } = {};
      try {
        errorData = await response.json();
        console.error('❌ Error response data:', errorData);
      } catch (jsonError) {
        // If response isn't JSON, get text
        const errorText = await response.text();
        console.error('❌ Error response text:', errorText);
        throw new Error(`Server error: ${response.status} - ${errorText}`);
      }
      
      // Handle specific error cases with helpful suggestions
      if (response.status === 401) {
        console.error(`🔐 Authentication failed. Suggestions:`);
        console.error(`   1. Switch to local backend: Set VITE_API_URL=http://localhost:8000`);
        console.error(`   2. Add your Supabase anon key: VITE_SUPABASE_ANON_KEY=your-key`);
        console.error(`   3. Make sure you're logged in to your app`);
        throw new Error('Authentication failed. Try using the local backend or check your Supabase configuration.');
      }
      
      throw new Error(errorData?.detail || errorData?.message || `Server error: ${response.status}`);
    }

    const result: ApiResponse = await response.json();
    console.log('📦 Full API response:', result);
    
    if (!result.success) {
      throw new Error(result.message || 'Processing failed');
    }
    // In processCreditReportWithAPI function, after getting the result:
    console.log('🔍 [DEBUG] API returned tradelines with user_ids:', 
      result.tradelines.map(t => t.user_id || 'undefined'));
    console.log('🔍 [DEBUG] Expected user_id should be:', userId);
    
    // Convert API response to ParsedTradeline format with required fields
    const tradelines: ParsedTradeline[] = (result.tradelines || []).map(t => ({
      id: uuidv4(),
      user_id: userId,
      creditor_name: t.creditor_name || 'NULL',
      account_balance: t.account_balance || '',
      created_at: new Date().toISOString(),
      dispute_count: t.dispute_count || 0,
      credit_limit: t.credit_limit || '',
      monthly_payment: t.monthly_payment || '',
      account_number: t.account_number || '',
      date_opened: t.date_opened || 'xx/xx/xxxx',
      is_negative: t.is_negative || false,
      account_type: t.account_type || '',
      account_status: t.account_status || '',
      credit_bureau: t.credit_bureau || '',
    }));

    console.log(`✅ Successfully processed ${tradelines.length} tradelines`);
    return tradelines;

  } catch (error) {
    console.error('❌ API call failed:', error);
    
    // Enhanced error reporting with suggestions
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(`Network error: Unable to connect to ${endpoint}. Please check if the API is running.`);
    }
    
    if (error instanceof Error) {
      throw error;
    }
    
    throw new Error(`Unknown error occurred: ${String(error)}`);
  }
};



// Test API connectivity
const testApiConnectivity = async (): Promise<boolean> => {
  const testUrls = [
    { 
      url: 'http://localhost:8000/health',
      needsAuth: false 
    },
    { 
      url: 'https://gywohmbqohytziwsjrps.supabase.co/functions/v1/process-credit-report',
      needsAuth: true 
    }
  ];

  for (const { url, needsAuth } of testUrls) {
    try {
      console.log(`🔗 Testing connectivity to: ${url}`);
      
      const headers: Record<string, string> = {
        'Accept': 'application/json',
      };
      
      // Add auth headers for Supabase
      if (needsAuth) {
        const authToken = localStorage.getItem('supabase.auth.token') || 
                         sessionStorage.getItem('supabase.auth.token') ||
                         import.meta.env.VITE_SUPABASE_ANON_KEY;
                         
        if (authToken) {
          headers['Authorization'] = `Bearer ${authToken}`;
        }
        
        const apiKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
        if (apiKey) {
          headers['apikey'] = apiKey;
        }
      }
      
      const response = await fetch(url, {
        method: 'GET',
        headers: headers,
      });
      
      console.log(`📡 ${url} responded with status: ${response.status}`);
      if (response.ok) {
        const data = await response.json().catch(() => ({}));
        console.log(`✅ ${url} is accessible:`, data);
        return true;
      } else {
        console.log(`❌ ${url} failed with status: ${response.status}`);
      }
    } catch (error) {
      console.log(`❌ ${url} is not accessible:`, error);
    }
  }
  return false;
};

// Progress stages
const PROGRESS_STAGES = {
  VALIDATION: 10,
  CONNECTIVITY_CHECK: 20,
  UPLOADING: 40,
  PROCESSING: 70,
  PARSING: 90,
  COMPLETE: 100
} as const;

export const useFileUploadHandler = ({
  user,
  processingMethod,
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
  
  // Reset UI state
  const resetUploadState = useCallback(() => {
    setUploadProgress(0);
    setExtractedKeywords([]);
    setAiInsights('');
    setExtractedText('');
    setShowAiResults?.(false); // Use optional chaining
  }, [setUploadProgress, setExtractedKeywords, setAiInsights, setExtractedText, setShowAiResults]);

  // Enhanced upload handler with debugging
  const handleFileUpload = useCallback(async (event: ChangeEvent<HTMLInputElement>) => {
    console.log("🚀 ===== Starting file upload process =====");
    
    try {
      const file = event.target.files?.[0];
      if (!file) {
        console.log("❌ No file selected");
        return;
      }

      // Reset input to allow re-uploading same file (AFTER we get the file)
      event.target.value = '';

      console.log(`📄 Selected file: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB)`);

      // Step 1: Validate file
      setUploadProgress(PROGRESS_STAGES.VALIDATION);
      try {
        validateFile(file);
      } catch (validationError) {
        const errorMessage = validationError instanceof Error ? validationError.message : "Invalid file";
        console.error('❌ File validation failed:', errorMessage);
        sonnerToast(errorMessage, { description: "Invalid File" });
        return;
      }

      // Step 2: Check authentication
      if (!user?.id) {
        console.error('❌ User not authenticated');
        sonnerToast("Please log in to upload files.", { description: "Authentication Required" });
        return;
      }

      console.log(`👤 Authenticated user: ${user.id}`);

      // Step 3: Test API connectivity
      setUploadProgress(PROGRESS_STAGES.CONNECTIVITY_CHECK);
      sonnerToast("Testing API connectivity...", { description: "Connection Check" });
      
      const isConnected = await testApiConnectivity();
      if (!isConnected) {
        console.error('❌ API connectivity test failed');
        sonnerToast("Unable to connect to processing API. Please check your connection.", { 
          description: "Connection Failed" 
        });
        // Continue anyway - might still work
      }

      // Step 4: Start upload process
      onUploadStart();
      resetUploadState();
      setShowAiResults?.(true); // Use optional chaining

      console.log(`📄 Processing ${file.name} for user ${user.id}`);
      
      // Step 5: Upload and process
      setUploadProgress(PROGRESS_STAGES.UPLOADING);
      sonnerToast("Uploading to Document AI...", { description: "Processing" });

      const startTime = Date.now();
      const tradelinesRaw = await processCreditReportWithAPI(file, user.id);
      const tradelines = sanitizeTradelines(tradelinesRaw);
      const processingTime = Date.now() - startTime;
      
      console.log(`⏱️ Total processing time: ${processingTime}ms`);
      
      setUploadProgress(PROGRESS_STAGES.PROCESSING);

      // Step 6: Validate tradelines with Zod
      console.log(`🔍 Validating ${tradelines.length} tradelines with Zod schema`);
      const validTradelines = tradelines
        .map((t, index) => {
          try {
            const validated = ParsedTradelineSchema.parse(t);
            console.log(`✅ Tradeline ${index + 1} validated:`, validated.creditor_name);
            return validated;
          } catch (e) {
            console.warn(`⚠️ Invalid tradeline ${index + 1} skipped:`, e, t);
            return null;
          }
        })
        .filter((t): t is ParsedTradeline => t !== null);

      console.log(`✅ ${validTradelines.length} of ${tradelines.length} tradelines are valid`);

      setUploadProgress(PROGRESS_STAGES.PARSING);

      // Step 7: Generate UI insights for display
      if (validTradelines.length > 0) {
        const creditorNames = validTradelines.map(t => t.creditor_name).filter(Boolean);
        const accountTypes = validTradelines.map(t => t.account_type).filter(Boolean);
        
        console.log('📊 Extracted creditors:', creditorNames);
        console.log('📊 Extracted account types:', accountTypes);
        
        setExtractedKeywords([...new Set([...creditorNames, ...accountTypes])]);
        
        const insights = `Found ${validTradelines.length} tradelines. ` +
          `Creditors: ${creditorNames.slice(0, 3).join(', ')}${creditorNames.length > 3 ? '...' : ''}. ` +
          `Account types: ${[...new Set(accountTypes)].join(', ')}.`;
        
        setAiInsights(insights);
        setExtractedText(`Successfully processed ${validTradelines.length} tradelines from ${file.name} in ${processingTime}ms`);
      } else {
        console.log('⚠️ No valid tradelines found');
        setExtractedText(`Processed ${file.name} but found no valid tradelines`);
      }

      setUploadProgress(PROGRESS_STAGES.COMPLETE);
      
      // Step 8: Complete upload
      onUploadComplete(validTradelines);
      
      // Success message
      const message = validTradelines.length > 0 
        ? `✅ Successfully processed ${validTradelines.length} tradeline${validTradelines.length !== 1 ? 's' : ''}!`
        : "⚠️ Document processed but no tradelines found.";
      
      console.log('🎉 Upload completed successfully');
      sonnerToast(message, { description: "Upload Complete" });
      
    } catch (error) {
      console.error("❌ ===== Upload failed =====");
      console.error("Error details:", error);
      console.error("Error stack:", error instanceof Error ? error.stack : 'No stack trace');
      
      resetUploadState();
      
      const errorMessage = error instanceof Error ? error.message : "Unknown error occurred";
      onUploadError(errorMessage);
      sonnerToast(`Processing failed: ${errorMessage}`, { description: "Error" });
    }
  }, [
    user?.id,
    processingMethod,
    onUploadStart,
    onUploadComplete,
    onUploadError,
    setUploadProgress,
    setExtractedKeywords,
    setAiInsights,
    setExtractedText,
    setShowAiResults,
    extractKeywordsFromText,
    generateAIInsights,
    resetUploadState
  ]);

  return { 
    handleFileUpload,
    resetUploadState 
  };
};