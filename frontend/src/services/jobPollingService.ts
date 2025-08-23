/**
 * Job Polling Service for real-time progress tracking
 * Handles background job status polling with exponential backoff
 */

import { supabase } from "@/integrations/supabase/client";

// Get API base URL
const getApiBaseUrl = () => {
  return import.meta.env.VITE_API_URL || 'http://localhost:8000';
};

// Utility function to get auth headers
async function getAuthHeaders(): Promise<Record<string, string>> {
  try {
    const { data: { session }, error } = await supabase.auth.getSession();
    
    if (error) {
      console.error('❌ Error getting auth session:', error);
      return { 'Content-Type': 'application/json' };
    }
    
    if (session?.access_token) {
      return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`
      };
    }
    
    return { 'Content-Type': 'application/json' };
  } catch (error) {
    console.error('❌ Error getting auth headers:', error);
    return { 'Content-Type': 'application/json' };
  }
}

export interface JobStatus {
  success: boolean;
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  message: string;
  result?: {
    success: boolean;
    tradelines_found: number;
    tradelines_saved: number;
    processing_time: number;
    method_used: string;
  };
  error?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface JobPollingOptions {
  /** Initial polling interval in milliseconds (default: 1000) */
  initialInterval?: number;
  /** Maximum polling interval in milliseconds (default: 10000) */
  maxInterval?: number;
  /** Maximum total polling time in milliseconds (default: 35 minutes) */
  maxDuration?: number;
  /** Exponential backoff multiplier (default: 1.5) */
  backoffMultiplier?: number;
}

export class JobPollingService {
  private pollingTimeouts = new Map<string, NodeJS.Timeout>();
  private pollingStartTimes = new Map<string, number>();

  /**
   * Start polling for job status updates
   */
  async pollJobStatus(
    jobId: string,
    onUpdate: (status: JobStatus) => void,
    onComplete: (status: JobStatus) => void,
    onError: (error: string) => void,
    options: JobPollingOptions = {}
  ): Promise<void> {
    const {
      initialInterval = 1000,
      maxInterval = 10000,
      maxDuration = 35 * 60 * 1000, // 35 minutes
      backoffMultiplier = 1.5
    } = options;

    // Clear any existing polling for this job
    this.stopPolling(jobId);

    const startTime = Date.now();
    this.pollingStartTimes.set(jobId, startTime);
    let currentInterval = initialInterval;

    const poll = async () => {
      try {
        // Check if we've exceeded maximum duration
        const elapsed = Date.now() - startTime;
        if (elapsed > maxDuration) {
          onError(`Polling timeout after ${Math.round(elapsed / 1000)}s`);
          this.stopPolling(jobId);
          return;
        }

        console.log(`🔄 Polling job ${jobId} (attempt ${Math.round(elapsed / 1000)}s elapsed)`);
        
        const status = await this.getJobStatus(jobId);
        
        if (!status.success) {
          onError(status.error || 'Failed to get job status');
          this.stopPolling(jobId);
          return;
        }

        // Call update callback
        onUpdate(status);

        // Check if job is complete
        if (status.status === 'completed') {
          console.log(`✅ Job ${jobId} completed successfully`);
          onComplete(status);
          this.stopPolling(jobId);
          return;
        } else if (status.status === 'failed') {
          console.log(`❌ Job ${jobId} failed: ${status.error}`);
          onError(status.error || 'Job failed');
          this.stopPolling(jobId);
          return;
        } else if (status.status === 'cancelled') {
          console.log(`🚫 Job ${jobId} was cancelled`);
          onError('Job was cancelled');
          this.stopPolling(jobId);
          return;
        }

        // Schedule next poll with exponential backoff
        currentInterval = Math.min(currentInterval * backoffMultiplier, maxInterval);
        
        const timeout = setTimeout(poll, currentInterval);
        this.pollingTimeouts.set(jobId, timeout);

      } catch (error) {
        console.error(`❌ Polling error for job ${jobId}:`, error);
        onError(error instanceof Error ? error.message : 'Polling failed');
        this.stopPolling(jobId);
      }
    };

    // Start polling immediately
    poll();
  }

  /**
   * Stop polling for a specific job
   */
  stopPolling(jobId: string): void {
    const timeout = this.pollingTimeouts.get(jobId);
    if (timeout) {
      clearTimeout(timeout);
      this.pollingTimeouts.delete(jobId);
    }
    this.pollingStartTimes.delete(jobId);
    console.log(`🛑 Stopped polling for job ${jobId}`);
  }

  /**
   * Stop all active polling
   */
  stopAllPolling(): void {
    this.pollingTimeouts.forEach((timeout) => clearTimeout(timeout));
    this.pollingTimeouts.clear();
    this.pollingStartTimes.clear();
    console.log('🛑 Stopped all job polling');
  }

  /**
   * Get current status of a job
   */
  async getJobStatus(jobId: string): Promise<JobStatus> {
    try {
      const headers = await getAuthHeaders();
      // Use relative URL to go through Vite proxy
      const response = await fetch(`${getApiBaseUrl()}/api/v1/processing/job/${jobId}`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Job status request failed:', response.status, errorText);
        return {
          success: false,
          job_id: jobId,
          status: 'failed',
          progress: 0,
          message: `HTTP ${response.status}: ${errorText}`,
          error: `Failed to get job status: ${response.status}`,
          created_at: new Date().toISOString()
        };
      }

      const result = await response.json();
      console.log(`📊 Job ${jobId} status:`, result.status, `${result.progress}%`, result.message);
      
      return result;
    } catch (error) {
      console.error('❌ Job status request failed:', error);
      return {
        success: false,
        job_id: jobId,
        status: 'failed',
        progress: 0,
        message: 'Network error',
        error: error instanceof Error ? error.message : 'Network error',
        created_at: new Date().toISOString()
      };
    }
  }

  /**
   * Cancel a background job
   */
  async cancelJob(jobId: string): Promise<{ success: boolean; message?: string; error?: string }> {
    try {
      const headers = await getAuthHeaders();
      // Use relative URL to go through Vite proxy
      const response = await fetch(`${getApiBaseUrl()}/api/v1/processing/job/${jobId}`, {
        method: 'DELETE',
        headers,
      });

      const result = await response.json();
      
      if (result.success) {
        this.stopPolling(jobId);
        console.log(`🚫 Job ${jobId} cancelled successfully`);
      }
      
      return result;
    } catch (error) {
      console.error('❌ Job cancellation failed:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error'
      };
    }
  }

  /**
   * Get user's recent jobs
   */
  async getUserJobs(userId: string, limit: number = 10): Promise<{
    success: boolean;
    jobs: Array<{
      job_id: string;
      status: string;
      progress: number;
      message: string;
      created_at: string;
      task_name: string;
    }>;
    total: number;
    error?: string;
  }> {
    try {
      const headers = await getAuthHeaders();
      // Use full API URL
      const response = await fetch(`${getApiBaseUrl()}/api/v1/processing/jobs?limit=${limit}`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        const errorText = await response.text();
        return {
          success: false,
          jobs: [],
          total: 0,
          error: `HTTP ${response.status}: ${errorText}`
        };
      }

      return await response.json();
    } catch (error) {
      console.error('❌ Failed to get user jobs:', error);
      return {
        success: false,
        jobs: [],
        total: 0,
        error: error instanceof Error ? error.message : 'Network error'
      };
    }
  }

  /**
   * Check if currently polling any jobs
   */
  isPolling(): boolean {
    return this.pollingTimeouts.size > 0;
  }

  /**
   * Get list of jobs currently being polled
   */
  getActivePollingJobs(): string[] {
    return Array.from(this.pollingTimeouts.keys());
  }
}

// Export singleton instance
export const jobPollingService = new JobPollingService();

// Standalone function for fetching jobs
export const fetchJobs = async (limit = 10) => {
  try {
    // Get auth headers
    const { data: { session }, error } = await supabase.auth.getSession();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    
    if (!error && session?.access_token) {
      headers['Authorization'] = `Bearer ${session.access_token}`;
    }
    
    // Use relative URL to go through Vite proxy
    const res = await fetch(`${getApiBaseUrl()}/api/v1/processing/jobs?limit=${limit}`, {
      method: "GET",
      headers,
    });

    if (!res.ok) {
      // Server responded but not with 2xx
      const errorText = await res.text();
      throw new Error(
        `Backend error ${res.status}: ${res.statusText} → ${errorText}`
      );
    }

    return await res.json();
  } catch (err) {
    if (err instanceof TypeError && err.message.includes("fetch")) {
      // Likely CORS or network error
      throw new Error(
        "Network request failed — possible CORS misconfiguration or server unreachable. Check backend headers."
      );
    }

    throw err; // Bubble up other errors
  }
};

// Cleanup on page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    jobPollingService.stopAllPolling();
  });
}