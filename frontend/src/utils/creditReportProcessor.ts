import { ParsedTradeline } from "./tradelineParser";

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Processing progress interface
export interface ProcessingProgress {
  step: string;
  progress: number;
  message: string;
}

// Extended return type for processWithAI
export interface ProcessingResult {
  tradelines: ParsedTradeline[];
  processingTime?: {
    start_time: string;
    end_time: string;
    duration_seconds: number;
    duration_formatted: string;
  };
  processingMethod?: string;
  stats: {
    found: number;
    saved: number;
    failed: number;
  };
  // Background job fields
  job_id?: string;
  status?: string;
  isBackgroundJob?: boolean;
}

// Shared file validation utility
const validateFile = (file: File): void => {
  if (!(file instanceof File)) {
    console.error('❌ NOT A FILE INSTANCE:', typeof file, file);
    throw new Error(`Expected File instance, got ${typeof file}`);
  }
  
  console.log('✅ File validation passed:', {
    name: file.name,
    type: file.type, 
    size: file.size,
    isFile: file instanceof File,
    constructor: file.constructor.name
  });
};

// Shared FormData creation utility
const createFormData = (file: File, userId?: string): FormData => {
  const formData = new FormData();
  formData.append('file', file); // Raw File object, no JSON, no toString()
  if (userId) {
    formData.append('user_id', userId);
  }
  
  // Debug FormData contents
  console.log('📦 FormData entries:');
  for (const [key, value] of formData.entries()) {
    console.log(`  ${key}:`, value instanceof File ? `File(${value.name})` : value);
  }
  
  return formData;
};

// Pure utility function for OCR processing (no hooks)
export const processWithOCR = async (file: File, userId?: string): Promise<string> => {
  // BULLETPROOF FILE VALIDATION
  validateFile(file);
  
  // BULLETPROOF FORMDATA
  const formData = createFormData(file, userId);
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/process-credit-report`, {
      method: 'POST',
      body: formData
      // NO HEADERS - Let browser set multipart/form-data with boundary
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ OCR Backend error:', response.status, errorText);
      throw new Error(`Backend error ${response.status}: ${errorText}`);
    }
    
    const result = await response.json();
    console.log('✅ OCR Processing Complete!', result);
    
    // 🎉 OCR completion indicators
    const extractedText = result.extracted_text || '';
    if (extractedText) {
      console.log('🎉 ===== OCR PROCESSING COMPLETED SUCCESSFULLY =====');
      console.log(`📝 Text extracted: ${extractedText.length} characters`);
      console.log('🏁 Ready for text analysis!');
    }
    
    return extractedText;
  } catch (error) {
    console.error('❌ OCR Request failed:', error);
    console.log('🏁 ===== OCR PROCESSING FAILED =====');
    throw error;
  }
};

// Enhanced AI processing function with progress callbacks and timeout handling
export const processWithAI = async (
  file: File, 
  userId?: string,
  onProgress?: (message: string) => void,
  retryCount: number = 0
): Promise<ProcessingResult> => {
  // BULLETPROOF FILE VALIDATION
  validateFile(file);
  
  // BULLETPROOF FORMDATA
  const formData = createFormData(file, userId);
  
  const controller = new AbortController();
  let timeoutId: NodeJS.Timeout | undefined;
  
  try {
    // Progress callback
    onProgress?.('📤 Uploading file...');
    
    // Set timeout based on file size (1 minute per MB, minimum 2 minutes, max 8 minutes)
    const fileSizeMB = file.size / (1024 * 1024);
    const timeoutMinutes = Math.max(2, Math.min(8, Math.ceil(fileSizeMB * 1)));
    
    timeoutId = setTimeout(() => {
      console.log(`⏰ Request timeout after ${timeoutMinutes} minutes`);
      onProgress?.('⏰ Request timed out');
      controller.abort();
    }, timeoutMinutes * 60 * 1000);
    
    console.log(`⏱️ Timeout set for ${timeoutMinutes} minutes based on file size (${fileSizeMB.toFixed(2)}MB)`);
    onProgress?.(`🧠 Processing PDF... (may take up to ${timeoutMinutes} minutes)`);
    
    console.log('🚀 Sending request to backend...');
    console.log('🔍 API_BASE_URL:', API_BASE_URL);
    console.log('📡 Full URL:', `${API_BASE_URL}/api/process-credit-report`);
    console.log('📦 File size:', `${fileSizeMB.toFixed(2)} MB`);
    
    const startTime = Date.now();
    
    console.log('🚀 Making fetch request...');
    const response = await fetch(`${API_BASE_URL}/api/process-credit-report`, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
      // Prevent browser extensions from interfering
      keepalive: false
    });
    console.log('📥 Fetch response received:', response.status, response.statusText);
    
    // Clear timeout on successful response
    clearTimeout(timeoutId);
    
    const requestTime = ((Date.now() - startTime) / 1000).toFixed(1);
    console.log(`📨 Response received in ${requestTime}s! Status: ${response.status}`);
    
    onProgress?.(`✅ Processing completed in ${requestTime}s`);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Backend error:', response.status, errorText);
      
      // Specific error handling
      if (response.status === 413) {
        throw new Error('File too large - please try a smaller PDF');
      } else if (response.status === 500) {
        throw new Error('Server error - please try again or contact support');
      } else if (response.status === 400) {
        throw new Error('Invalid file - please ensure you uploaded a valid PDF');
      } else {
        throw new Error(`Backend error ${response.status}: ${errorText}`);
      }
    }
    
    console.log('📥 Parsing response...');
    const result = await response.json();
    console.log('✅ Processing Complete!', result);
    
    // Check if this is a background job response
    if (result.success && result.job_id) {
      console.log('🔄 Background job submitted, returning job info');
      clearTimeout(timeoutId);
      
      return {
        tradelines: [],
        stats: { found: 0, saved: 0, failed: 0 },
        job_id: result.job_id,
        status: result.status,
        isBackgroundJob: true,
        processingMethod: result.processing_method
      };
    }
    
    // Success handling...
    if (result.success) {
      onProgress?.(`🎉 Found ${result.tradelines_found} tradelines!`);
      
      console.log('🎉 ===== PDF PROCESSING COMPLETED SUCCESSFULLY =====');
      console.log(`⏱️ Processing Time: ${result.processing_time?.duration_formatted || 'N/A'}`);
      console.log(`📈 Tradelines Found: ${result.tradelines_found || 0}`);
      console.log(`💾 Tradelines Saved: ${result.tradelines_saved || 0}`);
      console.log(`🔧 Processing Method: ${result.processing_method || 'Unknown'}`);
      console.log('🏁 Ready to view results!');
      
      // Check for save issues
      if (result.tradelines_saved === 0 && result.tradelines_found > 0) {
        console.warn('⚠️ Tradelines extracted but not saved to database');
        onProgress?.('⚠️ Data extracted but not saved to database');
      }
      
      // Show browser notification if supported
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Credit Report Processing Complete!', {
          body: `Found ${result.tradelines_found || 0} tradelines in ${result.processing_time?.duration_formatted || 'unknown time'}`,
          icon: '/favicon.ico'
        });
      }
    }
    
    // Filter out tradelines without valid account numbers
    const validTradelines = (result.tradelines || []).filter((tradeline: ParsedTradeline) => {
      // Exclude tradelines with no account number, empty account number, or default "UNKNOWN" value
      return tradeline.account_number && 
             tradeline.account_number.trim() !== '' && 
             tradeline.account_number.toUpperCase() !== 'UNKNOWN';
    });

    // Log filtering results
    const originalCount = result.tradelines?.length || 0;
    const filteredCount = validTradelines.length;
    const removedCount = originalCount - filteredCount;
    
    if (removedCount > 0) {
      console.log(`🔍 Filtered ${removedCount} tradelines without valid account numbers`);
      console.log(`📊 Tradelines: ${originalCount} found → ${filteredCount} valid`);
    }

    return { 
      tradelines: validTradelines,
      processingTime: result.processing_time,
      processingMethod: result.processing_method,
      stats: {
        found: originalCount,
        saved: result.tradelines_saved || 0,
        failed: result.tradelines_failed || removedCount
      }
    };
    
  } catch (error: unknown) {
    if (timeoutId) clearTimeout(timeoutId);

    console.error('❌ Request failed:', error);
    console.log('🏁 ===== PDF PROCESSING FAILED =====');

    // Type narrowing
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        if (retryCount < 1) {
          console.log(`🔄 Retrying request (attempt ${retryCount + 1}/2)...`);
          onProgress?.('🔄 Retrying request...');
          await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
          return processWithAI(file, userId, onProgress, retryCount + 1);
        }
        onProgress?.('❌ Request timed out');
        throw new Error('Processing timed out - the file may be too large or the server may be overloaded. Please try again.');
      } else if (error.message?.includes('Failed to fetch')) {
        onProgress?.('❌ Cannot connect to server');
        throw new Error('Cannot connect to server - please ensure the backend is running');
      } else if (error.message?.includes('NetworkError')) {
        onProgress?.('❌ Network error');
        throw new Error('Network error - please check your internet connection and try again');
      } else if (error.message?.includes('message channel closed')) {
        onProgress?.('❌ Browser extension conflict');
        throw new Error('Browser extension interference detected. Please disable extensions or try in incognito mode.');
      } else {
        onProgress?.('❌ Processing failed');
        throw error;
      }
    } else {
      onProgress?.('❌ Unknown error occurred');
      throw new Error('An unknown error occurred during PDF processing.');
    }
  }
}

// Test function for debugging backend connectivity
export const testBackendConnection = async (): Promise<void> => {
  try {
    console.log('🧪 Testing backend connection...');
    
    // Test 1: Simple health check
    const healthResponse = await fetch('/api/health');
    const healthData = await healthResponse.json();
    console.log('✅ Health check passed:', healthData);
    
    // Test 2: Try empty form data to test endpoint availability
    const emptyFormData = new FormData();
    emptyFormData.append('user_id', 'test-user');
    
    const emptyResponse = await fetch(`${API_BASE_URL}/api/process-credit-report`, {
      method: 'POST',
      body: emptyFormData
    });
    
    console.log('📨 Empty request response:', emptyResponse.status);
    const emptyResult = await emptyResponse.text();
    console.log('📄 Empty request result:', emptyResult.substring(0, 200) + '...');
    
  } catch (error) {
    console.error('❌ Backend test failed:', error);
    throw new Error('Backend connection test failed - ensure server is running');
  }
};

// Utility function to request notification permission
export const requestNotificationPermission = async (): Promise<boolean> => {
  if (!('Notification' in window)) {
    console.log('🔕 Notifications not supported in this browser');
    return false;
  }
  
  if (Notification.permission === 'granted') {
    return true;
  }
  
  if (Notification.permission === 'denied') {
    console.log('🔕 Notifications are blocked');
    return false;
  }
  
  try {
    const permission = await Notification.requestPermission();
    return permission === 'granted';
  } catch (error) {
    console.error('❌ Failed to request notification permission:', error);
    return false;
  }
};