import jsPDF from 'jspdf';
import { PDFDocument, rgb } from 'pdf-lib';
import { type ParsedTradeline } from '@/utils/tradelineParser';
import {
  DocumentBlob,
  convertImageToPdfPage,
  addPdfPages,
  getDocumentTitle
} from './documentPacketUtils';
import { supabase } from '@/integrations/supabase/client';

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
${profile.fullAddress}

${bureauInfo.name}
${bureauInfo.address}
${bureauInfo.city}, ${bureauInfo.state} ${bureauInfo.zip}

Re: Request for Investigation of Credit Report Inaccuracies
Consumer Name: ${profile.firstName} ${profile.lastName}
Date of Birth: ${profile.dateOfBirth || '[Date of Birth]'}
Social Security Number: ${profile.lastFourSSN ? `***-**-${profile.lastFourSSN}` : '[SSN]'}

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
const BUREAU_COLORS: Record<string, [number, number, number]> = {
  transunion: [37, 99, 235],   // blue
  experian:   [124, 58, 237],  // purple
  equifax:    [220, 38, 38],   // red
};

const BUREAU_ADDRESSES: Record<string, string[]> = {
  transunion: ['TransUnion LLC', 'Consumer Dispute Center', 'P.O. Box 2000', 'Chester, PA 19016'],
  experian:   ['Experian', 'P.O. Box 4500', 'Allen, TX 75013'],
  equifax:    ['Equifax Information Services LLC', 'P.O. Box 740256', 'Atlanta, GA 30374'],
};

const getBureauKey = (name: string): string =>
  Object.keys(BUREAU_COLORS).find(k => name.toLowerCase().includes(k)) ?? 'transunion';

const addCoverPage = (pdf: jsPDF, bureau: string, isFirstLetter: boolean) => {
  if (!isFirstLetter) pdf.addPage();

  const pageW = pdf.internal.pageSize.width;
  const pageH = pdf.internal.pageSize.height;
  const margin = 20;
  const key = getBureauKey(bureau);
  const [r, g, b] = BUREAU_COLORS[key] ?? [37, 99, 235];
  const address = BUREAU_ADDRESSES[key] ?? [];

  // Colored header bar
  pdf.setFillColor(r, g, b);
  pdf.rect(0, 0, pageW, 38, 'F');

  // "COVER LETTER" title in header
  pdf.setTextColor(255, 255, 255);
  pdf.setFontSize(20);
  pdf.setFont('helvetica', 'bold');
  pdf.text('COVER LETTER', margin, 16);

  // Bureau name in header
  pdf.setFontSize(13);
  pdf.setFont('helvetica', 'normal');
  pdf.text(bureau, margin, 28);

  // Reset text color
  pdf.setTextColor(0, 0, 0);

  // Warning box
  pdf.setFillColor(254, 242, 242);
  pdf.setDrawColor(220, 38, 38);
  pdf.setLineWidth(0.8);
  pdf.roundedRect(margin, 48, pageW - margin * 2, 22, 2, 2, 'FD');

  pdf.setTextColor(185, 28, 28);
  pdf.setFontSize(12);
  pdf.setFont('helvetica', 'bold');
  pdf.text('⚠  DO NOT MAIL THIS PAGE WITH YOUR DISPUTE', margin + 6, 58);
  pdf.setFontSize(9);
  pdf.setFont('helvetica', 'normal');
  pdf.text('This cover page is for your reference only. Remove it before mailing.', margin + 6, 66);

  pdf.setTextColor(0, 0, 0);

  // Instructions heading
  pdf.setFontSize(12);
  pdf.setFont('helvetica', 'bold');
  pdf.text('Instructions — What To Do:', margin, 86);

  const steps = [
    'Print all pages in this section (this cover page + the dispute letter following it).',
    'Read the dispute letter carefully and sign it at the bottom where indicated.',
    'Make a copy of the signed letter and keep it for your records.',
    `Mail ONLY the signed dispute letter (not this cover page) to ${bureau} at the address below.`,
    'Send via Certified Mail with Return Receipt Requested so you have proof of delivery.',
    'Write your tracking / confirmation number below and keep this page in your records.',
    'Wait 30–45 days for the bureau to investigate and respond.',
  ];

  pdf.setFontSize(10);
  pdf.setFont('helvetica', 'normal');
  let y = 96;
  steps.forEach((step, i) => {
    const lines = pdf.splitTextToSize(`${i + 1}.  ${step}`, pageW - margin * 2 - 10);
    lines.forEach((line: string, li: number) => {
      pdf.text(li === 0 ? line : `     ${line.trim()}`, margin + 4, y);
      y += 6;
    });
    y += 2;
  });

  // Mailing address box
  y += 4;
  pdf.setFillColor(245, 247, 255);
  pdf.setDrawColor(r, g, b);
  pdf.setLineWidth(0.5);
  pdf.roundedRect(margin, y, pageW - margin * 2, 8 + address.length * 7, 2, 2, 'FD');

  pdf.setFontSize(9);
  pdf.setFont('helvetica', 'bold');
  pdf.setTextColor(r, g, b);
  pdf.text('Mailing Address:', margin + 5, y + 7);
  pdf.setFont('helvetica', 'normal');
  pdf.setTextColor(0, 0, 0);
  address.forEach((line, i) => {
    pdf.text(line, margin + 5, y + 14 + i * 7);
  });

  // Tracking number line
  const trackY = pageH - 50;
  pdf.setDrawColor(180, 180, 180);
  pdf.setLineWidth(0.4);
  pdf.line(margin, trackY, pageW - margin, trackY);
  pdf.setFontSize(9);
  pdf.setTextColor(100, 100, 100);
  pdf.text('Certified Mail Tracking #: ___________________________________________   Date Mailed: ________________', margin, trackY + 6);

  // Footer
  pdf.setFontSize(8);
  pdf.setTextColor(150, 150, 150);
  pdf.text('Generated by Credit Clarity  •  For personal use only  •  Not legal advice', margin, pageH - 10);
};

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
  const margin = 20;
  const lineHeight = 6;

  letters.forEach((letter, letterIndex) => {
    // Cover page for this bureau
    addCoverPage(pdf, letter.creditBureau, letterIndex === 0);

    // Dispute letter starts on a new page
    pdf.addPage();
    let currentY = margin;
    const pageHeight = pdf.internal.pageSize.height;
    const pageW = pdf.internal.pageSize.width;

    // Letter content
    pdf.setFontSize(11);
    pdf.setFont('helvetica', 'normal');
    pdf.setTextColor(0, 0, 0);

    const lines = pdf.splitTextToSize(letter.letterContent, pageW - 2 * margin);
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

    updateProgress({
      step: 'Building packet...',
      progress: 60,
      message: 'Combining letters and supporting documents per bureau'
    });

    // For each bureau: cover page → dispute letter → supporting documents
    const totalSteps = letters.length * (1 + documents.length);
    let stepsDone = 0;

    for (let i = 0; i < letters.length; i++) {
      const letter = letters[i];

      // --- Cover page (jsPDF → pdf-lib) ---
      const coverPdf = new jsPDF();
      addCoverPage(coverPdf, letter.creditBureau, true);
      const coverBlob = new Blob([coverPdf.output('arraybuffer')], { type: 'application/pdf' });
      await addPdfPages(coverBlob, mainPdf, `Cover - ${letter.creditBureau}`);

      // --- Dispute letter ---
      const tempPdf = new jsPDF();
      const pageHeight = tempPdf.internal.pageSize.height;
      const margin = 20;
      const lineHeight = 6;
      let currentY = margin;

      tempPdf.setFontSize(11);
      tempPdf.setFont('helvetica', 'normal');
      tempPdf.setTextColor(0, 0, 0);

      const lines = tempPdf.splitTextToSize(letter.letterContent, tempPdf.internal.pageSize.width - 2 * margin);
      lines.forEach((line: string) => {
        if (currentY > pageHeight - margin) {
          tempPdf.addPage();
          currentY = margin;
        }
        tempPdf.text(line, margin, currentY);
        currentY += lineHeight;
      });

      const letterBlob = new Blob([tempPdf.output('arraybuffer')], { type: 'application/pdf' });
      await addPdfPages(letterBlob, mainPdf, `Dispute Letter - ${letter.creditBureau}`);

      stepsDone++;
      updateProgress({
        step: `Adding ${letter.creditBureau} section...`,
        progress: 60 + (stepsDone / totalSteps) * 35,
        message: `Letter added — appending supporting documents`
      });

      // --- Supporting documents after each letter ---
      for (let d = 0; d < documents.length; d++) {
        const docBlob = documents[d];
        const title = getDocumentTitle(docBlob.document.document_type);

        updateProgress({
          step: `Adding ${title} (${letter.creditBureau})...`,
          progress: 60 + (stepsDone / totalSteps) * 35,
          message: `Processing ${docBlob.document.file_name}`
        });

        if (docBlob.type === 'image') {
          await convertImageToPdfPage(docBlob.blob, mainPdf, title);
        } else if (docBlob.type === 'pdf') {
          await addPdfPages(docBlob.blob, mainPdf, title);
        }

        stepsDone++;
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

// ─────────────────────────────────────────────────────────────────────────────
// AI-Powered Dispute Letter Generation Pipeline
// ─────────────────────────────────────────────────────────────────────────────

/** Thrown when a duplicate dispute is found within 24 hours */
export class DuplicateDisputeError extends Error {
  constructor(message: string, public readonly existingDisputeId: string) {
    super(message);
    this.name = 'DuplicateDisputeError';
  }
}

export interface DisputePayload {
  userId: string;
  bureau: string;
  creditorName: string;
  accountNumberMasked: string;
  disputeReason: string;
}

export interface StoredDispute {
  id: string;
  user_id: string;
  creditor_name: string | null;
  account_number_masked: string | null;
  bureau: string | null;
  dispute_reason: string | null;
  letter_text: string | null;
  status: string;
  created_at: string | null;
  mailing_address: string;
}

/**
 * Returns the existing dispute ID if a duplicate was filed within the last 24 h, null otherwise.
 */
export const checkDuplicateDispute = async (
  userId: string,
  creditorName: string,
  accountNumberMasked: string,
  bureau: string
): Promise<string | null> => {
  const since = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
  const { data } = await supabase
    .from('disputes')
    .select('id')
    .eq('user_id', userId)
    .eq('creditor_name', creditorName)
    .eq('account_number_masked', accountNumberMasked)
    .eq('bureau', bureau)
    .gte('created_at', since)
    .maybeSingle();
  return data?.id ?? null;
};

/** Build a static fallback letter when the AI Edge Function is unavailable */
const buildFallbackSingleLetter = (
  pi: { firstName: string; lastName: string; address: string; address2?: string; city: string; state: string; zip: string; lastFourSSN: string },
  payload: DisputePayload,
  bureauAddress: string
): string => {
  const date = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  return `${pi.firstName} ${pi.lastName}
${pi.address}${pi.address2 ? '\n' + pi.address2 : ''}
${pi.city}, ${pi.state} ${pi.zip}

${date}

${bureauAddress}

Re: Dispute of Credit Report Information — FCRA Section 611

Dear Sir or Madam:

I am writing pursuant to the Fair Credit Reporting Act (FCRA), 15 U.S.C. § 1681i, to dispute the following item appearing on my credit report:

  Creditor Name:   ${payload.creditorName}
  Account Number:  ${payload.accountNumberMasked}
  Dispute Reason:  ${payload.disputeReason}

This information is inaccurate. I respectfully request that you investigate this matter within 30 days as required by law. If you cannot verify the accuracy of this information, it must be deleted from my credit file immediately.

Please send me written notification of the results of your investigation and a corrected copy of my credit report.

Sincerely,

${pi.firstName} ${pi.lastName}
SSN: XXX-XX-${pi.lastFourSSN}

Enclosures: Copy of identification, Copy of Social Security card`;
};

/**
 * Generate and persist a single dispute letter via the AI Edge Function.
 * Falls back to a static template if the Edge Function is unavailable.
 * Throws DuplicateDisputeError if a duplicate exists within 24 h.
 */
export const generateDisputeLetterViaAI = async (
  payload: DisputePayload
): Promise<StoredDispute> => {
  // 1. Duplicate check
  const duplicateId = await checkDuplicateDispute(
    payload.userId,
    payload.creditorName,
    payload.accountNumberMasked,
    payload.bureau
  );
  if (duplicateId) {
    throw new DuplicateDisputeError(
      'A dispute for this account was already generated in the last 24 hours.',
      duplicateId
    );
  }

  // 2. Fetch user profile
  const { data: profileData, error: profileError } = await supabase
    .from('profiles')
    .select('first_name, last_name, address1, address2, city, state, zip_code, phone_number, last_four_of_ssn')
    .eq('user_id', payload.userId)
    .single();

  if (profileError || !profileData) {
    console.error('[disputeUtils] Profile fetch failed:', profileError);
    throw new Error('Profile not found. Please complete your profile before generating letters.');
  }

  const pi = {
    firstName: profileData.first_name ?? '',
    lastName: profileData.last_name ?? '',
    address: profileData.address1 ?? '',
    address2: profileData.address2 ?? undefined,
    city: profileData.city ?? '',
    state: profileData.state ?? '',
    zip: profileData.zip_code ?? '',
    phone: profileData.phone_number ?? undefined,
    lastFourSSN: profileData.last_four_of_ssn ?? 'XXXX',
  };

  // 3. Resolve bureau mailing address (DB → hardcoded fallback)
  const { data: bureauRow } = await supabase
    .from('credit_bureaus')
    .select('address')
    .eq('name', payload.bureau)
    .maybeSingle();

  let mailingAddress = bureauRow?.address ?? '';
  if (!mailingAddress) {
    const bi = CREDIT_BUREAU_ADDRESSES[payload.bureau as keyof typeof CREDIT_BUREAU_ADDRESSES];
    mailingAddress = bi
      ? `${bi.name}\n${bi.address}\n${bi.city}, ${bi.state} ${bi.zip}`
      : payload.bureau;
  }

  // 4. Call Edge Function (with static fallback)
  let letterText: string;
  try {
    const { data: edgeData, error: edgeError } = await supabase.functions.invoke('generate-dispute-letter', {
      body: {
        personalInfo: {
          firstName: pi.firstName,
          lastName: pi.lastName,
          address: pi.address,
          address2: pi.address2,
          city: pi.city,
          state: pi.state,
          zip: pi.zip,
          phone: pi.phone,
          lastFourSSN: pi.lastFourSSN,
        },
        selectedTradelines: [{
          creditor_name: payload.creditorName,
          account_number: payload.accountNumberMasked,
          dispute_reason: payload.disputeReason,
        }],
        bureaus: [payload.bureau],
      },
    });

    if (edgeError) throw edgeError;
    letterText = (edgeData?.letters?.[payload.bureau] as string) ?? '';
    if (!letterText) throw new Error('AI service returned an empty letter');
  } catch (err) {
    console.warn('[disputeUtils] Edge function unavailable, using fallback template:', err);
    letterText = buildFallbackSingleLetter(pi, payload, mailingAddress);
  }

  // 5. Persist to disputes table
  const { data: saved, error: insertError } = await supabase
    .from('disputes')
    .insert({
      user_id: payload.userId,
      credit_report_id: `dispute-${Date.now()}`,
      creditor_name: payload.creditorName,
      account_number_masked: payload.accountNumberMasked,
      bureau: payload.bureau,
      dispute_reason: payload.disputeReason,
      letter_text: letterText,
      mailing_address: mailingAddress,
      status: 'generated',
    })
    .select()
    .single();

  if (insertError || !saved) {
    console.error('[disputeUtils] Failed to save dispute record:', insertError);
    throw new Error('Failed to save dispute letter. Please try again.');
  }

  return saved as StoredDispute;
};

/**
 * Persist batch-generated (static template) letters to the disputes table so
 * they appear in Dispute History. Non-throwing — logs errors internally.
 */
export const saveLettersToDisputesTable = async (
  letters: GeneratedDisputeLetter[],
  userId: string,
  tradelines: ParsedTradeline[]
): Promise<void> => {
  if (letters.length === 0 || !userId) return;

  const inserts = letters.flatMap((letter) => {
    const bureauTradelines = tradelines.filter(
      (t) => !t.credit_bureau || t.credit_bureau === letter.creditBureau
    );
    const targets = bureauTradelines.length > 0 ? bureauTradelines : tradelines;

    const bi = CREDIT_BUREAU_ADDRESSES[letter.creditBureau as keyof typeof CREDIT_BUREAU_ADDRESSES];
    const mailingAddress = bi
      ? `${bi.name}\n${bi.address}\n${bi.city}, ${bi.state} ${bi.zip}`
      : letter.creditBureau;

    return targets.map((t) => ({
      user_id: userId,
      credit_report_id: `batch-${Date.now()}-${t.id}`,
      creditor_name: t.creditor_name ?? null,
      account_number_masked: t.account_number
        ? t.account_number.length > 4
          ? `****${t.account_number.slice(-4)}`
          : t.account_number
        : null,
      bureau: letter.creditBureau,
      dispute_reason: 'Inaccurate or unverifiable information',
      letter_text: letter.letterContent,
      mailing_address: mailingAddress,
      status: 'generated',
    }));
  });

  if (inserts.length === 0) return;

  const { error } = await supabase.from('disputes').insert(inserts);
  if (error) {
    console.error('[disputeUtils] Failed to save batch disputes to history:', error);
  }
};