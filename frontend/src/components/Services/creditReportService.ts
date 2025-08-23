// src/services/creditReportService.ts
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

export interface ProcessedTradeline {
  creditor_name: string;
  account_number: string;
  account_balance: string;
  credit_limit: string;
  monthly_payment: string;
  date_opened: string;
  account_status: string;
  account_type: string;
  credit_bureau: string;
  is_negative: boolean;
}

export async function processCreditReport(
  file: File, 
  userId: string
): Promise<ProcessedTradeline[]> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('user_id', userId);

  const authHeaders = await getAuthHeaders();
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const response = await fetch(`${apiUrl}/api/v1/processing/upload`, {
    method: 'POST',
    body: formData,
    headers: authHeaders,
  });

  if (!response.ok) {
    throw new Error('Failed to process credit report');
  }

  const result = await response.json();
  return result.tradelines;
}