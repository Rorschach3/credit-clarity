// src/utils/pdf-processor.ts
import { z } from 'zod';
import { supabase } from "@/integrations/supabase/client";

// Utility function to get auth headers
async function getAuthHeaders(): Promise<Record<string, string>> {
  try {
    const { data: { session }, error } = await supabase.auth.getSession();
    
    if (error) {
      console.error('❌ Error getting auth session:', error);
      return {};
    }
    
    if (session?.access_token) {
      return {
        'Authorization': `Bearer ${session.access_token}`
      };
    }
    
    return {};
  } catch (error) {
    console.error('❌ Error getting auth headers:', error);
    return {};
  }
}

export const TradelineSchema = z.object({
  accountName: z.string(),
  accountNumber: z.string().optional(),
  balance: z.number(),
  creditorName: z.string().optional(),
  openedDate: z.string().optional(),
  status: z.string().optional(),
});

export type Tradeline = z.infer<typeof TradelineSchema>;


export async function processPdfFile(file: File, userId: string): Promise<PDFProcessingResult> {
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', userId);
    
    // Vite environment variable
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    
    const authHeaders = await getAuthHeaders();
    const response = await fetch(`${apiUrl}/api/v1/processing/upload`, {
      method: 'POST',
      body: formData,
      headers: authHeaders,
    });
    
    if (!response.ok) {
      throw new Error(`API returned ${response.status}: ${response.statusText}`);
    }
    
    const result = await response.json();
    
    return {
      tradelines: result.tradelines || [],
      success: result.success || false,
      message: `Processed ${result.tradelines_saved || 0} tradelines`
    };
  } catch (error) {
    console.error('PDF processing error:', error);
    throw new Error('Failed to process PDF file');
  }
}