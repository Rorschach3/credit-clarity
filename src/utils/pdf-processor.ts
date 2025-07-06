export interface PDFProcessingResult {
  text: string;
  pages: number;
  metadata?: Record<string, unknown>;
}

// Client-side PDF processing using pdf-parse
export async function processPdfFile(file: File): Promise<PDFProcessingResult> {
  try {
    console.log('Processing PDF file with client-side parser...');
    
    // Dynamic import with proper typing
    const pdfParse = await import('pdf-parse');
    
    const arrayBuffer = await file.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    
    const data = await pdfParse.default(buffer);
    
    console.log(`PDF parsed successfully: ${data.numpages} pages, ${data.text.length} characters`);
    
    return {
      text: data.text || '',
      pages: data.numpages || 1,
      metadata: {
        info: data.info,
        version: data.version
      }
    };
  } catch (error) {
    console.error('Client-side PDF processing error:', error);
    throw new Error('Failed to process PDF file. Please ensure the file is a valid, text-based PDF.');
  }
}
