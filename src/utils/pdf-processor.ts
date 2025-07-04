
import pdfParse from 'pdf-parse';

export interface PDFProcessingResult {
  text: string;
  pages: number;
  metadata?: any;
}

export async function processPdfFile(file: File): Promise<PDFProcessingResult> {
  try {
    const arrayBuffer = await file.arrayBuffer();
    const data = await pdfParse(arrayBuffer);
    
    return {
      text: data.text,
      pages: data.numpages,
      metadata: data.metadata
    };
  } catch (error) {
    console.error('PDF processing error:', error);
    throw new Error('Failed to process PDF file. Please ensure it is a valid PDF document.');
  }
}

export function validatePdfFile(file: File): boolean {
  if (!file) {
    throw new Error('No file provided');
  }
  
  if (file.type !== 'application/pdf') {
    throw new Error('Please upload a PDF file only');
  }
  
  if (file.size > 10 * 1024 * 1024) { // 10MB limit
    throw new Error('File size must be less than 10MB');
  }
  
  return true;
}
