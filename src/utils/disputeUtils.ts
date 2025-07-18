import jsPDF from 'jspdf';
import { PDFDocument, rgb } from 'pdf-lib';
import { type ParsedTradeline } from '@/utils/tradelineParser';
import { 
  DocumentBlob, 
  convertImageToPdfPage, 
  addPdfPages, 
  getDocumentTitle 
} from './documentPacketUtils';

// Credit Bureau Information
export const CREDIT_BUREAU_ADDRESSES = {
  'Experian': {
    name: 'Experian',
    address: 'P.O. Box 4000',
    city: 'Allen',
    state: 'TX',
    zip: '75013'
  },
  'Equifax': {
    name: 'Equifax Information Services LLC',
    address: 'P.O. Box 740256',
    city: 'Atlanta',
    state: 'GA',
    zip: '30374'
  },
  'TransUnion': {
    name: 'TransUnion LLC Consumer Dispute Center',
    address: 'P.O. Box 2000',
    city: 'Chester',
    state: 'PA',
    zip: '19016'
  }
};

export interface GeneratedDisputeLetter {
  id: string;
  creditBureau: string;
  tradelines: ParsedTradeline[];
  letterContent: string;
  disputeCount: number;
  isEdited?: boolean;
}

export interface PacketProgress {
  step: string;
  progress: number;
  message: string;
}

// Generate dispute reasons based on tradeline status
export const getDisputeReasons = (tradeline: ParsedTradeline): string[] => {
  const reasons: string[] = [];
  
  // Check common dispute reasons based on tradeline data
  if (!tradeline.account_number || tradeline.account_number.trim() === '') {
    reasons.push("Account number is missing or incomplete");
  }
  
  if (!tradeline.date_opened || tradeline.date_opened.trim() === '') {
    reasons.push("Date opened is inaccurate or missing");
  }
  
  if (!tradeline.account_status || tradeline.account_status.trim() === '') {
    reasons.push("Account status is inaccurate");
  }
  
  // Add default reason if no specific issues found
  if (reasons.length === 0) {
    reasons.push("This account does not belong to me");
    reasons.push("The information reported is inaccurate");
  }
  
  return reasons;
};

// Generate dispute letter content for multiple tradelines to one bureau
export const generateDisputeLetterContent = (
  tradelines: ParsedTradeline[], 
  creditBureau: string, 
  profile: {
    firstName: string;
    lastName: string;
    address: string;
    city: string;
    state: string;
    zipCode: string;
    dateOfBirth?: string;
    ssn?: string;
  }
): string => {
  const currentDate = new Date().toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  });
  
  const bureauInfo = CREDIT_BUREAU_ADDRESSES[creditBureau as keyof typeof CREDIT_BUREAU_ADDRESSES];
  
  // Create account table
  const accountRows = tradelines.map(tradeline => {
    const formattedAccountNumber = tradeline.account_number && tradeline.account_number.length > 4 
      ? `****${tradeline.account_number.slice(-4)}` 
      : tradeline.account_number || '[Account Number]';
    
    const formattedDateOpened = tradeline.date_opened || '[Date]';
    
    return `${tradeline.creditor_name || '[Creditor]'} | ${formattedAccountNumber} | ${formattedDateOpened} | Inaccurate Information`;
  });
  
  const accountTable = `Creditor Name | Account Number | Date Opened | Dispute Reason
${'='.repeat(70)}
${accountRows.join('\n')}`;

  return `${currentDate}

${profile.firstName} ${profile.lastName}
${profile.address}
${profile.city}, ${profile.state} ${profile.zipCode}

${bureauInfo.name}
${bureauInfo.address}
${bureauInfo.city}, ${bureauInfo.state} ${bureauInfo.zip}

Re: Request for Investigation of Credit Report Inaccuracies
Consumer Name: ${profile.firstName} ${profile.lastName}
Date of Birth: ${profile.dateOfBirth || '[Date of Birth]'}
Social Security Number: ${profile.ssn ? `***-**-${profile.ssn.slice(-4)}` : '[SSN]'}

Dear Sir or Madam,

I am writing to dispute inaccurate information on my credit report. Under the Fair Credit Reporting Act (FCRA), I have the right to request that you investigate and correct any inaccuracies.

The following accounts contain inaccurate information that must be investigated and corrected or removed:

${accountTable}

I am requesting that these items be investigated under Section 611 of the FCRA. Please conduct a reasonable investigation of these disputed items and provide me with the results of your investigation.

If you cannot verify the accuracy of these items, they must be deleted from my credit file immediately as required by law.

Please send me an updated copy of my credit report showing the corrections made, along with a list of everyone who has received my credit report in the past year (or two years for employment purposes).

I expect to receive a response within 30 days as required by the FCRA. Please contact me at the address above if you need additional information.

Thank you for your prompt attention to this matter.

Sincerely,

${profile.firstName} ${profile.lastName}

Enclosures: Copy of Driver's License, Copy of Social Security Card, Copy of Utility Bill`;
};

// Generate dispute letters grouped by credit bureau
export const generateDisputeLetters = async (
  selectedTradelines: string[],
  negativeTradelines: ParsedTradeline[],
  profile: {
    firstName: string;
    lastName: string;
    address: string;
    city: string;
    state: string;
    zipCode: string;
    dateOfBirth?: string;
    ssn?: string;
  },
  updateProgress: (progress: PacketProgress) => void
): Promise<GeneratedDisputeLetter[]> => {
  const letters: GeneratedDisputeLetter[] = [];
  
  updateProgress({
    step: 'Analyzing tradelines...',
    progress: 10,
    message: 'Grouping tradelines by credit bureau'
  });

  // Group selected tradelines by credit bureau
  const tradelinesByBureau: Record<string, ParsedTradeline[]> = {};
  
  selectedTradelines.forEach(id => {
    const tradeline = negativeTradelines.find(t => t.id === id);
    if (tradeline && tradeline.credit_bureau) {
      if (!tradelinesByBureau[tradeline.credit_bureau]) {
        tradelinesByBureau[tradeline.credit_bureau] = [];
      }
      tradelinesByBureau[tradeline.credit_bureau].push(tradeline);
    }
  });

  updateProgress({
    step: 'Generating letters...',
    progress: 30,
    message: `Found ${Object.keys(tradelinesByBureau).length} bureau(s) to dispute`
  });

  // Generate a letter for each bureau
  const bureaus = Object.keys(tradelinesByBureau);
  for (let i = 0; i < bureaus.length; i++) {
    const bureau = bureaus[i];
    const tradelines = tradelinesByBureau[bureau];
    
    updateProgress({
      step: `Creating ${bureau} letter...`,
      progress: 30 + (i / bureaus.length) * 50,
      message: `Generating letter for ${tradelines.length} tradeline(s)`
    });

    const letterContent = generateDisputeLetterContent(tradelines, bureau, profile);
    
    letters.push({
      id: `${bureau}-${Date.now()}`,
      creditBureau: bureau,
      tradelines: tradelines,
      letterContent: letterContent,
      disputeCount: tradelines.length
    });

    // Simulate processing time
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  updateProgress({
    step: 'Finalizing letters...',
    progress: 90,
    message: `Generated ${letters.length} dispute letter(s)`
  });

  return letters;
};

// Generate PDF packet
export const generatePDFPacket = async (
  letters: GeneratedDisputeLetter[],
  updateProgress: (progress: PacketProgress) => void
): Promise<Blob> => {
  updateProgress({
    step: 'Creating PDF...',
    progress: 85,
    message: 'Formatting dispute letters'
  });

  const pdf = new jsPDF();
  const pageHeight = pdf.internal.pageSize.height;
  const margin = 20;
  const lineHeight = 6;
  let currentY = margin;

  letters.forEach((letter, letterIndex) => {
    if (letterIndex > 0) {
      pdf.addPage();
      currentY = margin;
    }

    // Add letter title
    pdf.setFontSize(16);
    pdf.setFont('helvetica', 'bold');
    pdf.text(`Dispute Letter - ${letter.creditBureau}`, margin, currentY);
    currentY += lineHeight * 2;

    // Add letter content
    pdf.setFontSize(11);
    pdf.setFont('helvetica', 'normal');
    
    const lines = pdf.splitTextToSize(letter.letterContent, pdf.internal.pageSize.width - 2 * margin);
    
    lines.forEach((line: string) => {
      if (currentY > pageHeight - margin) {
        pdf.addPage();
        currentY = margin;
      }
      pdf.text(line, margin, currentY);
      currentY += lineHeight;
    });
  });

  updateProgress({
    step: 'Finalizing PDF...',
    progress: 95,
    message: 'Preparing download'
  });

  return pdf.output('blob');
};

// Generate complete PDF packet with letters and documents
export const generateCompletePacket = async (
  letters: GeneratedDisputeLetter[],
  documents: DocumentBlob[],
  updateProgress: (progress: PacketProgress) => void
): Promise<Blob> => {
  updateProgress({
    step: 'Creating complete packet...',
    progress: 50,
    message: 'Initializing PDF document'
  });

  try {
    // Create main PDF document using pdf-lib
    const mainPdf = await PDFDocument.create();
    
    // Add title page
    const titlePage = mainPdf.addPage();
    const { width, height } = titlePage.getSize();
    
    titlePage.drawText('Credit Dispute Packet', {
      x: 50,
      y: height - 100,
      size: 24,
      color: rgb(0, 0, 0),
    });
    
    titlePage.drawText('Generated by Credit Clarity', {
      x: 50,
      y: height - 140,
      size: 12,
      color: rgb(0.5, 0.5, 0.5),
    });
    
    titlePage.drawText(new Date().toLocaleDateString(), {
      x: 50,
      y: height - 160,
      size: 10,
      color: rgb(0.5, 0.5, 0.5),
    });

    // Add table of contents
    let yPos = height - 220;
    titlePage.drawText('Contents:', {
      x: 50,
      y: yPos,
      size: 16,
      color: rgb(0, 0, 0),
    });
    
    yPos -= 30;
    letters.forEach((letter, index) => {
      titlePage.drawText(`${index + 1}. Dispute Letter - ${letter.creditBureau}`, {
        x: 70,
        y: yPos,
        size: 12,
        color: rgb(0, 0, 0),
      });
      yPos -= 20;
    });
    
    documents.forEach((doc, index) => {
      titlePage.drawText(`${letters.length + index + 1}. ${getDocumentTitle(doc.document.document_type)}`, {
        x: 70,
        y: yPos,
        size: 12,
        color: rgb(0, 0, 0),
      });
      yPos -= 20;
    });

    updateProgress({
      step: 'Adding dispute letters...',
      progress: 60,
      message: 'Converting dispute letters to PDF'
    });

    // Convert jsPDF dispute letters to pdf-lib format
    for (let i = 0; i < letters.length; i++) {
      const letter = letters[i];
      
      // Create temporary jsPDF for this letter
      const tempPdf = new jsPDF();
      const pageHeight = tempPdf.internal.pageSize.height;
      const margin = 20;
      const lineHeight = 6;
      let currentY = margin;

      // Add letter title
      tempPdf.setFontSize(16);
      tempPdf.setFont('helvetica', 'bold');
      tempPdf.text(`Dispute Letter - ${letter.creditBureau}`, margin, currentY);
      currentY += lineHeight * 2;

      // Add letter content
      tempPdf.setFontSize(11);
      tempPdf.setFont('helvetica', 'normal');
      
      const lines = tempPdf.splitTextToSize(letter.letterContent, tempPdf.internal.pageSize.width - 2 * margin);
      
      lines.forEach((line: string) => {
        if (currentY > pageHeight - margin) {
          tempPdf.addPage();
          currentY = margin;
        }
        tempPdf.text(line, margin, currentY);
        currentY += lineHeight;
      });

      // Convert to blob and add to main PDF
      const letterBlob = new Blob([tempPdf.output('arraybuffer')], { type: 'application/pdf' });
      await addPdfPages(letterBlob, mainPdf, `Dispute Letter - ${letter.creditBureau}`);
    }

    updateProgress({
      step: 'Adding documents...',
      progress: 80,
      message: 'Processing uploaded documents'
    });

    // Add user documents
    for (let i = 0; i < documents.length; i++) {
      const docBlob = documents[i];
      const title = getDocumentTitle(docBlob.document.document_type);
      
      updateProgress({
        step: `Adding ${title}...`,
        progress: 80 + (i / documents.length) * 15,
        message: `Processing ${docBlob.document.file_name}`
      });

      if (docBlob.type === 'image') {
        await convertImageToPdfPage(docBlob.blob, mainPdf, title);
      } else if (docBlob.type === 'pdf') {
        await addPdfPages(docBlob.blob, mainPdf, title);
      }
    }

    updateProgress({
      step: 'Finalizing packet...',
      progress: 95,
      message: 'Preparing complete packet for download'
    });

    // Convert to blob
    const pdfBytes = await mainPdf.save();
    const finalBlob = new Blob([pdfBytes], { type: 'application/pdf' });

    updateProgress({
      step: 'Complete!',
      progress: 100,
      message: 'Dispute packet ready for download'
    });

    return finalBlob;

  } catch (error) {
    console.error('Error generating complete packet:', error);
    throw error;
  }
};