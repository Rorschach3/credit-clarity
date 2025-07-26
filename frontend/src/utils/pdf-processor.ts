// src/utils/pdf-processor.ts
export interface PDFProcessingResult {
  tradelines: any[];
  success: boolean;
  message?: string;
}

export async function processPdfFile(file: File, userId: string): Promise<PDFProcessingResult> {
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', userId);
    
    // Vite environment variable
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    
    const response = await fetch(`${apiUrl}/process-credit-report`, {
      method: 'POST',
      body: formData,
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