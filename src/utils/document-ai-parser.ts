import { supabase } from "@/integrations/supabase/client";
import { ParsedTradeline } from "@/utils/tradeline/types";

export interface DocumentAIResult {
  text: string;
  pages: number;
  metadata?: Record<string, unknown>;
}

export interface TradelineMatch {
  creditor_name: string;
  account_number: string;
  account_balance: string;
  credit_limit: string;
  monthly_payment: string;
  date_opened: string;
  account_type: string;
  account_status: string;
  credit_bureau: string;
  is_negative: boolean;
  dispute_count: number;
}

// Enhanced patterns for credit report parsing
const CREDITOR_PATTERNS = [
  /(?:AMERICAN EXPRESS|AMEX|AM EX)\s*[\#\-\s]*(\d{4,15})/gi,
  /(?:CAPITAL ONE|CAP ONE|CAPITALONE)\s*[\#\-\s]*(\d{4,16})/gi,
  /(?:CHASE|JP MORGAN|JPMORGAN)\s*[\#\-\s]*(\d{4,16})/gi,
  /(?:DISCOVER|DISC)\s*[\#\-\s]*(\d{4,16})/gi,
  /(?:CITI|CITIBANK|CITIBK)\s*[\#\-\s]*(\d{4,16})/gi,
  /(?:WELLS FARGO|WF|WFNNB)\s*[\#\-\s]*(\d{4,16})/gi,
  /(?:BANK OF AMERICA|BOA|BOFA)\s*[\#\-\s]*(\d{4,16})/gi,
  /(?:SYNCHRONY|SYNC)\s*[\#\-\s]*(\d{4,16})/gi,
  /(?:BARCLAYS|BARC)\s*[\#\-\s]*(\d{4,16})/gi,
  /([A-Z\s&]{3,30})\s*(?:ACCT|ACCOUNT|#)\s*[\#\-\s]*(\d{4,16})/gi
];

const ACCOUNT_STATUS_PATTERNS = {
  'open': /(?:open|current|ok|good standing)/gi,
  'closed': /(?:closed|terminated|cancelled)/gi,
  'in_collection': /(?:collection|charged off and sold|sold)/gi,
  'charged_off': /(?:charge off|charged off|chargeoff)/gi,
  'disputed': /(?:disputed|dispute|under review)/gi
};

const NEGATIVE_INDICATORS = [
  /charge off/gi,
  /collection/gi,
  /delinquent/gi,
  /late payment/gi,
  /\b30\s*days?\s*late/gi,
  /\b60\s*days?\s*late/gi,
  /\b90\s*days?\s*late/gi,
  /\b120\s*days?\s*late/gi,
  /past due/gi,
  /default/gi,
  /foreclosure/gi,
  /repossession/gi,
  /bankruptcy/gi
];

const BUREAU_PATTERNS = {
  'experian': /experian|exp/gi,
  'equifax': /equifax|eqf|efx/gi,
  'transunion': /transunion|tuc|tu/gi
};

const ACCOUNT_TYPE_PATTERNS = {
  'credit_card': /credit card|revolving|visa|mastercard|amex|discover/gi,
  'mortgage': /mortgage|real estate|home loan|mtg/gi,
  'auto_loan': /auto|vehicle|car loan|automotive/gi,
  'student_loan': /student|education|educ/gi,
  'loan': /installment|personal loan|loan/gi,
  'collection': /collection|charged off and sold/gi
};

export async function processDocumentWithAI(file: File): Promise<DocumentAIResult> {
  try {
    console.log("🔍 Processing document with Google Document AI...");
    
    // Convert file to base64
    const arrayBuffer = await file.arrayBuffer();
    const base64Data = btoa(
      new Uint8Array(arrayBuffer).reduce((data, byte) => data + String.fromCharCode(byte), '')
    );
    
    // Call FastAPI backend with Document AI
    const response = await fetch('http://localhost:8000/document-ai', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ base64: base64Data }),
    });
    
    if (!response.ok) {
      throw new Error(`Document AI processing failed: ${response.status} ${response.statusText}`);
    }
    
    const result = await response.json();
    console.log("✅ Document AI processing complete");
    
    return {
      text: result.document?.text || '',
      pages: result.document?.pages?.length || 1,
      metadata: result
    };
  } catch (error) {
    console.error('❌ Document AI processing error:', error);
    throw new Error(`Failed to process document: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

export function parseTradelinesFromDocumentAI(documentText: string, creditBureau?: string): TradelineMatch[] {
  console.log("🔍 Parsing tradelines from Document AI text...");
  console.log("📄 Text length:", documentText.length);
  
  const tradelines: TradelineMatch[] = [];
  const lines = documentText.split('\n');
  
  // Process text line by line to find account information
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    
    // Try to match creditor patterns
    for (const pattern of CREDITOR_PATTERNS) {
      pattern.lastIndex = 0; // Reset regex
      const match = pattern.exec(line);
      
      if (match) {
        const creditorName = extractCreditorName(match[0]);
        const accountNumber = match[1] || extractAccountNumber(line);
        
        if (creditorName && accountNumber) {
          // Look for additional account details in surrounding lines
          const contextLines = lines.slice(Math.max(0, i - 2), Math.min(lines.length, i + 5)).join(' ');
          
          const tradeline: TradelineMatch = {
            creditor_name: creditorName,
            account_number: accountNumber,
            account_balance: extractBalance(contextLines),
            credit_limit: extractCreditLimit(contextLines),
            monthly_payment: extractMonthlyPayment(contextLines),
            date_opened: extractDateOpened(contextLines),
            account_type: determineAccountType(contextLines),
            account_status: determineAccountStatus(contextLines),
            credit_bureau: creditBureau || determineCreditBureau(contextLines),
            is_negative: isNegativeAccount(contextLines),
            dispute_count: extractDisputeCount(contextLines)
          };
          
          // Only add if we have minimum required data
          if (tradeline.creditor_name && tradeline.account_number) {
            tradelines.push(tradeline);
            console.log("✅ Found tradeline:", tradeline.creditor_name, tradeline.account_number);
          }
        }
      }
    }
  }
  
  console.log(`🎯 Extracted ${tradelines.length} tradelines from document`);
  return tradelines;
}

function extractCreditorName(text: string): string {
  // Clean up creditor name
  const cleaned = text
    .replace(/ACCT|ACCOUNT|#|\d+/gi, '')
    .replace(/[^\w\s&]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .toUpperCase();
  
  return cleaned.length > 2 ? cleaned : '';
}

function extractAccountNumber(text: string): string {
  const numbers = text.match(/\d{4,16}/g);
  return numbers ? numbers[numbers.length - 1] : '';
}

function extractBalance(text: string): string {
  const balanceMatch = text.match(/(?:balance|bal|owe[ds]?)\s*:?\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)/gi);
  if (balanceMatch) {
    const amount = balanceMatch[0].match(/\d{1,3}(?:,\d{3})*(?:\.\d{2})?/);
    return amount ? amount[0] : '';
  }
  return '';
}

function extractCreditLimit(text: string): string {
  const limitMatch = text.match(/(?:limit|credit limit|cl)\s*:?\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)/gi);
  if (limitMatch) {
    const amount = limitMatch[0].match(/\d{1,3}(?:,\d{3})*(?:\.\d{2})?/);
    return amount ? amount[0] : '';
  }
  return '';
}

function extractMonthlyPayment(text: string): string {
  const paymentMatch = text.match(/(?:payment|pmt|monthly)\s*:?\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)/gi);
  if (paymentMatch) {
    const amount = paymentMatch[0].match(/\d{1,3}(?:,\d{3})*(?:\.\d{2})?/);
    return amount ? amount[0] : '';
  }
  return '';
}

function extractDateOpened(text: string): string {
  const dateMatch = text.match(/(?:opened|open date|date opened)\s*:?\s*(\d{1,2}[-\/]\d{1,2}[-\/]\d{2,4})/gi);
  if (dateMatch) {
    const date = dateMatch[0].match(/\d{1,2}[-\/]\d{1,2}[-\/]\d{2,4}/);
    if (date) {
      // Convert to YYYY/MM/DD format
      const parts = date[0].split(/[-\/]/);
      if (parts.length === 3) {
        let [month, day, year] = parts;
        if (year.length === 2) {
          year = parseInt(year) > 50 ? `19${year}` : `20${year}`;
        }
        return `${year}/${month.padStart(2, '0')}/${day.padStart(2, '0')}`;
      }
    }
  }
  return '';
}

function determineAccountType(text: string): string {
  for (const [type, pattern] of Object.entries(ACCOUNT_TYPE_PATTERNS)) {
    if (pattern.test(text)) {
      return type;
    }
  }
  return '';
}

function determineAccountStatus(text: string): string {
  for (const [status, pattern] of Object.entries(ACCOUNT_STATUS_PATTERNS)) {
    if (pattern.test(text)) {
      return status;
    }
  }
  return 'open'; // Default to open if no status found
}

function determineCreditBureau(text: string): string {
  for (const [bureau, pattern] of Object.entries(BUREAU_PATTERNS)) {
    if (pattern.test(text)) {
      return bureau;
    }
  }
  return '';
}

function isNegativeAccount(text: string): boolean {
  return NEGATIVE_INDICATORS.some(pattern => pattern.test(text));
}

function extractDisputeCount(text: string): number {
  const disputeMatch = text.match(/dispute[ds]?\s*:?\s*(\d+)/gi);
  if (disputeMatch) {
    const count = disputeMatch[0].match(/\d+/);
    return count ? parseInt(count[0]) : 0;
  }
  return 0;
}

// Main function to process and save tradelines
export async function processAndSaveTradelines(
  file: File, 
  userId: string, 
  updateExisting: boolean = true
): Promise<ParsedTradeline[]> {
  try {
    console.log("🚀 Starting Document AI processing and tradeline extraction...");
    
    // Step 1: Process document with Google Document AI
    const documentResult = await processDocumentWithAI(file);
    
    if (!documentResult.text || documentResult.text.length < 100) {
      throw new Error("Insufficient text extracted from document. Please ensure the PDF contains readable text.");
    }
    
    // Step 2: Parse tradelines from extracted text
    const extractedTradelines = parseTradelinesFromDocumentAI(documentResult.text);
    
    if (extractedTradelines.length === 0) {
      throw new Error("No tradelines found in the document. Please verify this is a credit report.");
    }
    
    // Step 3: Convert to ParsedTradeline format with database schema
    const parsedTradelines: ParsedTradeline[] = extractedTradelines.map(tl => ({
      id: crypto.randomUUID(),
      user_id: userId,
      creditor_name: tl.creditor_name,
      account_number: tl.account_number,
      account_balance: tl.account_balance,
      credit_limit: tl.credit_limit,
      monthly_payment: tl.monthly_payment,
      date_opened: tl.date_opened,
      account_type: tl.account_type as any,
      account_status: tl.account_status as any,
      credit_bureau: tl.credit_bureau as any,
      is_negative: tl.is_negative,
      dispute_count: tl.dispute_count,
      created_at: new Date().toISOString()
    }));
    
    // Step 4: Save to database with upsert logic
    await saveTradelinesToDatabaseWithConstraints(parsedTradelines, userId, updateExisting);
    
    console.log(`✅ Successfully processed and saved ${parsedTradelines.length} tradelines`);
    return parsedTradelines;
    
  } catch (error) {
    console.error('❌ Error in processAndSaveTradelines:', error);
    throw error;
  }
}

async function saveTradelinesToDatabaseWithConstraints(
  tradelines: ParsedTradeline[], 
  userId: string, 
  updateExisting: boolean
): Promise<void> {
  try {
    console.log(`💾 Saving ${tradelines.length} tradelines to database...`);
    
    for (const tradeline of tradelines) {
      // Check if tradeline already exists (unique constraint: user_id, account_number, creditor_name)
      const { data: existing } = await supabase
        .from('tradelines')
        .select('id')
        .eq('user_id', userId)
        .eq('creditor_name', tradeline.creditor_name)
        .eq('account_number', tradeline.account_number)
        .single();
      
      if (existing) {
        if (updateExisting) {
          // Update existing record
          const { error } = await supabase
            .from('tradelines')
            .update({
              account_balance: tradeline.account_balance,
              credit_limit: tradeline.credit_limit,
              monthly_payment: tradeline.monthly_payment,
              date_opened: tradeline.date_opened,
              account_type: tradeline.account_type,
              account_status: tradeline.account_status,
              credit_bureau: tradeline.credit_bureau,
              is_negative: tradeline.is_negative,
              dispute_count: tradeline.dispute_count
            })
            .eq('id', existing.id);
          
          if (error) throw error;
          console.log(`✅ Updated existing tradeline: ${tradeline.creditor_name}`);
        } else {
          console.log(`⏭️ Skipped existing tradeline: ${tradeline.creditor_name}`);
        }
      } else {
        // Insert new record
        const { error } = await supabase
          .from('tradelines')
          .insert([tradeline]);
        
        if (error) throw error;
        console.log(`✅ Inserted new tradeline: ${tradeline.creditor_name}`);
      }
    }
    
  } catch (error) {
    console.error('❌ Database save error:', error);
    throw error;
  }
}