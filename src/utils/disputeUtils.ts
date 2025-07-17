import jsPDF from 'jspdf';
import { type ParsedTradeline } from '@/utils/tradelineParser';

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
  profile: any
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
  profile: any,
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