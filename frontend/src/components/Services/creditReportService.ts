// src/services/creditReportService.ts
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

  const response = await fetch('/api/process-credit-report', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error('Failed to process credit report');
  }

  const result = await response.json();
  return result.tradelines;
}