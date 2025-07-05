export interface PDFProcessingResult {
  text: string;
  pages: number;
  metadata?: Record<string, unknown>;
}

// Update function signature to require API key
export async function processPdfFile(file: File): Promise<PDFProcessingResult> {
  try {
    const arrayBuffer = await file.arrayBuffer();
    const base64Data = btoa(
      new Uint8Array(arrayBuffer).reduce((data, byte) => data + String.fromCharCode(byte), '')
    );
    
    // Call your Document AI proxy server
    const response = await fetch('http://localhost:8000/document-ai', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ base64: base64Data }),
    });
    
    if (!response.ok) {
      throw new Error(`Document AI proxy returned ${response.status}: ${response.statusText}`);
    }
    
    const result = await response.json();
    
    return {
      text: result.document?.text || '',
      pages: result.document?.pages?.length || 1,
      metadata: result
    };
  } catch (error) {
    console.error('PDF processing error:', error);
    throw new Error('Failed to process PDF file with Document AI proxy.');
  }
}
