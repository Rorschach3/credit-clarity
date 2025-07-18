import { supabase } from '@/integrations/supabase/client';
import { PDFDocument, rgb } from 'pdf-lib';
import { PacketProgress } from './disputeUtils';

export interface UserDocument {
  id: string;
  user_id: string;
  document_type: string;
  file_path: string;
  file_name: string;
  content_type: string;
  created_at: string;
}

export interface DocumentBlob {
  document: UserDocument;
  blob: Blob;
  type: 'image' | 'pdf';
}

// Required document types for dispute packet
export const REQUIRED_DOCUMENT_TYPES = ['photo_id', 'ssn_card', 'utility_bill'] as const;

/**
 * Fetch user documents from database
 */
export const fetchUserDocuments = async (userId: string): Promise<UserDocument[]> => {
  try {
    // Check session first
    const { data: session } = await supabase.auth.getSession();
    if (!session?.session) {
      throw new Error('No active session');
    }

    const { data, error } = await supabase
      .from('user_documents')
      .select('*')
      .eq('user_id', userId)
      .in('document_type', REQUIRED_DOCUMENT_TYPES);

    if (error) {
      console.error('Error fetching user documents:', error);
      throw error;
    }

    return data || [];
  } catch (error) {
    console.error('Failed to fetch user documents:', error);
    throw error;
  }
};

/**
 * Download document blobs from Supabase storage
 */
export const downloadDocumentBlobs = async (
  documents: UserDocument[],
  updateProgress?: (progress: PacketProgress) => void
): Promise<DocumentBlob[]> => {
  const documentBlobs: DocumentBlob[] = [];
  let successCount = 0;
  let failureCount = 0;
  
  for (let i = 0; i < documents.length; i++) {
    const document = documents[i];
    
    if (updateProgress) {
      updateProgress({
        step: `Downloading ${getDocumentTitle(document.document_type)}...`,
        progress: 20 + (i / documents.length) * 30,
        message: `Fetching ${document.file_name}`
      });
    }

    try {
      // Download from Supabase storage
      const { data: blob, error } = await supabase.storage
        .from('dispute_documents')
        .download(document.file_path);

      if (error) {
        console.error(`Error downloading ${document.file_path}:`, error);
        failureCount++;
        continue; // Skip this document but continue with others
      }

      if (!blob) {
        console.warn(`No blob data for ${document.file_path}`);
        failureCount++;
        continue;
      }

      // Determine document type
      const isImage = document.content_type.startsWith('image/');
      const isPdf = document.content_type === 'application/pdf';

      if (isImage || isPdf) {
        documentBlobs.push({
          document,
          blob,
          type: isImage ? 'image' : 'pdf'
        });
        successCount++;
      } else {
        console.warn(`Unsupported document type: ${document.content_type}`);
        failureCount++;
      }
    } catch (error) {
      console.error(`Failed to download ${document.file_name}:`, error);
      failureCount++;
      // Continue with other documents
    }
  }

  // Log summary
  console.log(`Document download summary: ${successCount} successful, ${failureCount} failed`);
  
  if (updateProgress && documents.length > 0) {
    updateProgress({
      step: 'Documents processed',
      progress: 50,
      message: `${successCount} documents downloaded successfully`
    });
  }

  return documentBlobs;
};

/**
 * Convert image to PDF page
 */
export const convertImageToPdfPage = async (
  imageBlob: Blob,
  pdfDoc: PDFDocument,
  title: string
): Promise<void> => {
  try {
    // Convert blob to array buffer
    const arrayBuffer = await imageBlob.arrayBuffer();
    
    // Embed image in PDF
    let image;
    if (imageBlob.type.includes('jpeg') || imageBlob.type.includes('jpg')) {
      image = await pdfDoc.embedJpg(arrayBuffer);
    } else if (imageBlob.type.includes('png')) {
      image = await pdfDoc.embedPng(arrayBuffer);
    } else {
      throw new Error(`Unsupported image format: ${imageBlob.type}`);
    }

    // Add a new page
    const page = pdfDoc.addPage();
    const { width, height } = page.getSize();
    
    // Add title
    page.drawText(title, {
      x: 50,
      y: height - 50,
      size: 16,
      color: rgb(0, 0, 0),
    });

    // Calculate image dimensions to fit page
    const imageWidth = image.width;
    const imageHeight = image.height;
    const aspectRatio = imageWidth / imageHeight;
    
    const maxWidth = width - 100; // 50px margin on each side
    const maxHeight = height - 150; // Space for title and margins
    
    let finalWidth = maxWidth;
    let finalHeight = maxWidth / aspectRatio;
    
    if (finalHeight > maxHeight) {
      finalHeight = maxHeight;
      finalWidth = maxHeight * aspectRatio;
    }

    // Center the image
    const x = (width - finalWidth) / 2;
    const y = (height - finalHeight) / 2 - 25; // Account for title

    // Draw image
    page.drawImage(image, {
      x,
      y,
      width: finalWidth,
      height: finalHeight,
    });

  } catch (error) {
    console.error('Error converting image to PDF:', error);
    throw error;
  }
};

/**
 * Add existing PDF pages to main document
 */
export const addPdfPages = async (
  pdfBlob: Blob,
  mainPdfDoc: PDFDocument,
  title: string
): Promise<void> => {
  try {
    const arrayBuffer = await pdfBlob.arrayBuffer();
    const sourcePdf = await PDFDocument.load(arrayBuffer);
    
    // Add title page
    const titlePage = mainPdfDoc.addPage();
    const { width, height } = titlePage.getSize();
    
    titlePage.drawText(title, {
      x: 50,
      y: height - 50,
      size: 16,
      color: rgb(0, 0, 0),
    });

    // Copy all pages from source PDF
    const pageIndices = sourcePdf.getPageIndices();
    const copiedPages = await mainPdfDoc.copyPages(sourcePdf, pageIndices);
    
    copiedPages.forEach((page) => {
      mainPdfDoc.addPage(page);
    });

  } catch (error) {
    console.error('Error adding PDF pages:', error);
    throw error;
  }
};

/**
 * Get document title for display
 */
export const getDocumentTitle = (documentType: string): string => {
  switch (documentType) {
    case 'photo_id':
      return 'Photo ID / Driver\'s License';
    case 'ssn_card':
      return 'Social Security Card';
    case 'utility_bill':
      return 'Utility Bill / Proof of Address';
    default:
      return documentType.replace('_', ' ').toUpperCase();
  }
};

/**
 * Check if user has uploaded all required documents
 */
export const hasRequiredDocuments = (documents: UserDocument[]): boolean => {
  const uploadedTypes = documents.map(doc => doc.document_type);
  return REQUIRED_DOCUMENT_TYPES.every(type => uploadedTypes.includes(type));
};

/**
 * Get missing document types
 */
export const getMissingDocuments = (documents: UserDocument[]): string[] => {
  const uploadedTypes = documents.map(doc => doc.document_type);
  return REQUIRED_DOCUMENT_TYPES.filter(type => !uploadedTypes.includes(type));
};