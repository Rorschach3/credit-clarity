/**
 * Experian-Specific Enhanced Parser
 * 
 * Based on analysis of the actual Experian report format from PDF
 * Addresses the specific parsing failures in the current system
 */

import { ParsedTradeline, ParsedTradelineSchema } from './tradeline/types';

// Enhanced patterns specifically for Experian format
export const EXPERIAN_PATTERNS = {
  // Section anchors - exact text from PDF
  sectionAnchors: {
    negativeItems: /Potentially\s+Negative\s+Items\s+or\s+items\s+for\s+further\s+review/i,
    goodStanding: /Accounts\s+in\s+Good\s+Standing/i,
    inquiries: /Record\s+of\s+Requests\s+for\s+Your\s+Credit\s+History/i,
    personalInfo: /Personal\s+Information/i
  },
  
  // Account delimiter - company name followed by address block
  accountDelimiter: /^([A-Z][A-Z\s&'-]+(?:BANK|CARD|CREDIT|UNION|FINANCIAL|CORP|INC|LLC|CO|CAPITAL|CHASE|WELLS|CITI|DISCOVER|AMEX|AMERICAN\s+EXPRESS))\s*\n.*Address:/gim,
  
  // Alternative account patterns
  creditorPatterns: [
    // Standard format: COMPANY NAME on its own line
    /^([A-Z\s&'-]{4,}(?:BANK|CARD|CREDIT|UNION|FINANCIAL|CORP|INC|LLC|CO|CAPITAL|CHASE|WELLS|CITI|DISCOVER|AMEX|AMERICAN\s+EXPRESS))\s*$/gim,
    // Company name followed by Address:
    /^([A-Z\s&'-]+(?:BANK|CARD|CREDIT|UNION|FINANCIAL|CORP|INC|LLC|CO|CAPITAL|CHASE|WELLS|CITI|DISCOVER|AMEX|AMERICAN\s+EXPRESS))\s*\nAddress:/gim,
    // Generic all caps company name
    /^([A-Z\s&'-]{8,})\s*\nAddress:/gim
  ],
  
  // Account number - Experian specific format
  accountNumber: [
    /Account\s+Number:\s*(\d{4,16}\.{3,4})/gi,
    /Account\s+Number:\s*([*X]{4,12}\d{4,8})/gi,
    /Account\s+Number:\s*(\d{4,16})/gi
  ],
  
  // Financial fields with exact Experian labels
  creditLimit: [
    /Credit\s+Limit\/Original\s+Amount:\s*\$?([\d,]+\.?\d*)/gi,
    /Credit\s+Limit:\s*\$?([\d,]+\.?\d*)/gi,
    /Original\s+Amount:\s*\$?([\d,]+\.?\d*)/gi
  ],
  
  balance: [
    /Recent\s+Balance:\s*\$?([\d,]+\.?\d*)/gi,
    /High\s+Balance:\s*\$?([\d,]+\.?\d*)/gi,
    /Balance:\s*\$?([\d,]+\.?\d*)/gi
  ],
  
  monthlyPayment: [
    /Monthly\s+Payment:\s*\$?([\d,]+\.?\d*)/gi,
    /Recent\s+Payment:\s*\$?([\d,]+\.?\d*)/gi
  ],
  
  dateOpened: [
    /Date\s+Opened:\s*(\d{1,2}\/\d{4})/gi,
    /Date\s+Opened:\s*(\d{1,2}\/\d{1,2}\/\d{2,4})/gi
  ],
  
  status: [
    /Status:\s*([^\.]+)/gi,
    /Account\s+Status:\s*([^\.]+)/gi
  ],
  
  accountType: [
    /Type:\s*(Credit\s+card|Secured\s+Card|Auto\s+Loan|Mortgage|Unsecured|Student\s+Loan)/gi
  ]
};

// Payment history patterns specific to Experian
export const EXPERIAN_PAYMENT_PATTERNS = {
  yearLine: /^\s*(20\d{2})\s*$/gm,
  monthStatusLine: /(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+(CO|CLS|OK|ND|\d{2,3}|R|VS|PBC|IC|G|D|C)/gi,
  paymentHistorySection: /Payment\s+History:\s*([\s\S]*?)(?=Account\s+History:|Balance\s+History:|$)/gi
};

export class ExperianSpecificParser {
  
  /**
   * Parse Experian credit report using specific patterns from the PDF format
   */
  public parseExperianCreditReport(rawText: string, userId?: string): ParsedTradeline[] {
    console.log('🎯 Starting Experian-specific parsing...');
    
    const tradelines: ParsedTradeline[] = [];
    
    try {
      // Step 1: Split by major sections
      const sections = this.splitIntoSections(rawText);
      
      // Step 2: Process each section
      for (const [sectionType, sectionText] of Object.entries(sections)) {
        if (sectionText && sectionText.trim().length > 100) {
          console.log(`📋 Processing ${sectionType} section (${sectionText.length} chars)`);
          
          const sectionTradelines = this.parseAccountsInSection(
            sectionText, 
            sectionType === 'negativeItems',
            userId
          );
          
          tradelines.push(...sectionTradelines);
        }
      }
      
      console.log(`✅ Experian parsing completed: ${tradelines.length} tradelines extracted`);
      return tradelines;
      
    } catch (error) {
      console.error('❌ Experian parsing failed:', error);
      return [];
    }
  }
  
  /**
   * Split text into major sections using Experian-specific anchors
   */
  private splitIntoSections(rawText: string): Record<string, string> {
    const sections = {
      negativeItems: '',
      goodStanding: '',
      inquiries: '',
      personalInfo: '',
      other: rawText
    };
    
    // Find section positions
    const sectionPositions: Array<{type: string, start: number, header: string}> = [];
    
    Object.entries(EXPERIAN_PATTERNS.sectionAnchors).forEach(([sectionType, pattern]) => {
      const match = rawText.match(pattern);
      if (match && match.index !== undefined) {
        sectionPositions.push({
          type: sectionType,
          start: match.index,
          header: match[0]
        });
      }
    });
    
    // Sort by position
    sectionPositions.sort((a, b) => a.start - b.start);
    
    // Extract sections
    for (let i = 0; i < sectionPositions.length; i++) {
      const current = sectionPositions[i];
      const next = sectionPositions[i + 1];
      
      const sectionEnd = next ? next.start : rawText.length;
      const sectionContent = rawText.slice(current.start, sectionEnd);
      
      sections[current.type as keyof typeof sections] = sectionContent;
      console.log(`🔍 Found ${current.type}: ${current.header}`);
    }
    
    return sections;
  }
  
  /**
   * Parse individual accounts within a section
   */
  private parseAccountsInSection(sectionText: string, isNegativeSection: boolean, userId?: string): ParsedTradeline[] {
    const accounts: ParsedTradeline[] = [];
    
    // Split into account blocks using company name patterns
    const accountBlocks = this.splitIntoAccountBlocks(sectionText);
    
    console.log(`📊 Found ${accountBlocks.length} account blocks in section`);
    
    for (const block of accountBlocks) {
      try {
        const tradeline = this.parseAccountBlock(block, isNegativeSection, userId);
        if (tradeline && this.isValidTradeline(tradeline)) {
          accounts.push(tradeline);
          console.log(`✅ Parsed: ${tradeline.creditor_name} (${tradeline.account_number})`);
        }
      } catch (error) {
        console.warn('⚠️ Failed to parse account block:', error);
      }
    }
    
    return accounts;
  }
  
  /**
   * Split section text into individual account blocks
   */
  private splitIntoAccountBlocks(sectionText: string): string[] {
    const blocks: string[] = [];
    const lines = sectionText.split('\\n');
    
    let currentBlock = '';
    let inAccountBlock = false;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;
      
      // Check if this line starts a new account
      const isAccountStart = this.isAccountHeaderLine(line);
      
      if (isAccountStart) {
        // Save previous block
        if (currentBlock.length > 200) { // Minimum size for valid account
          blocks.push(currentBlock.trim());
        }
        
        // Start new block
        currentBlock = line + '\\n';
        inAccountBlock = true;
      } else if (inAccountBlock) {
        currentBlock += line + '\\n';
      }
    }
    
    // Don't forget the last block
    if (currentBlock.length > 200) {
      blocks.push(currentBlock.trim());
    }
    
    return blocks;
  }
  
  /**
   * Check if a line is an account header (company name)
   */
  private isAccountHeaderLine(line: string): boolean {
    // Must be all caps and contain bank/financial keywords
    const financialKeywords = [
      'BANK', 'CARD', 'CREDIT', 'UNION', 'FINANCIAL', 'CORP', 'INC', 'LLC', 'CO',
      'CAPITAL', 'CHASE', 'WELLS', 'CITI', 'DISCOVER', 'AMEX', 'AMERICAN', 'FIRST'
    ];
    
    const isAllCaps = line === line.toUpperCase();
    const hasFinancialKeyword = financialKeywords.some(keyword => line.includes(keyword));
    const isLongEnough = line.length >= 4;
    const noSpecialChars = !/[()@#$%^&*+={}[\]|\\:";'<>?,./]/.test(line);
    
    return isAllCaps && hasFinancialKeyword && isLongEnough && noSpecialChars;
  }
  
  /**
   * Parse individual account block
   */
  private parseAccountBlock(blockText: string, forceNegative: boolean, userId?: string): ParsedTradeline | null {
    try {
      // Extract creditor name (first line that looks like a company)
      const creditorName = this.extractCreditorName(blockText);
      if (!creditorName) return null;
      
      // Extract other fields
      const accountNumber = this.extractWithPatterns(blockText, EXPERIAN_PATTERNS.accountNumber);
      const creditLimit = this.extractWithPatterns(blockText, EXPERIAN_PATTERNS.creditLimit);
      const balance = this.extractWithPatterns(blockText, EXPERIAN_PATTERNS.balance);
      const monthlyPayment = this.extractWithPatterns(blockText, EXPERIAN_PATTERNS.monthlyPayment);
      const dateOpened = this.extractWithPatterns(blockText, EXPERIAN_PATTERNS.dateOpened);
      const status = this.extractWithPatterns(blockText, EXPERIAN_PATTERNS.status);
      const accountType = this.extractWithPatterns(blockText, EXPERIAN_PATTERNS.accountType);
      
      // Determine if negative
      const isNegative = forceNegative || this.isNegativeAccount(status, blockText);
      
      const tradeline: ParsedTradeline = {
        id: crypto.randomUUID(),
        user_id: userId || '',
        creditor_name: creditorName,
        account_number: accountNumber || '',
        account_balance: balance ? `$${balance}` : '',
        account_status: this.normalizeStatus(status),
        account_type: this.normalizeAccountType(accountType, creditorName),
        date_opened: this.normalizeDateFormat(dateOpened),
        is_negative: isNegative,
        dispute_count: 0,
        created_at: new Date().toISOString(),
        credit_limit: creditLimit ? `$${creditLimit}` : '',
        credit_bureau: 'experian',
        monthly_payment: monthlyPayment ? `$${monthlyPayment}` : ''
      };
      
      return ParsedTradelineSchema.parse(tradeline);
      
    } catch (error) {
      console.warn('Failed to parse account block:', error);
      return null;
    }
  }
  
  /**
   * Extract creditor name from account block
   */
  private extractCreditorName(blockText: string): string {
    const lines = blockText.split('\\n');
    
    // Try each creditor pattern
    for (const pattern of EXPERIAN_PATTERNS.creditorPatterns) {
      const match = blockText.match(pattern);
      if (match && match[1]) {
        return this.cleanCreditorName(match[1]);
      }
    }
    
    // Fallback: look for first all-caps line with financial keywords
    for (const line of lines) {
      const trimmed = line.trim();
      if (this.isAccountHeaderLine(trimmed)) {
        return this.cleanCreditorName(trimmed);
      }
    }
    
    return '';
  }
  
  /**
   * Extract value using multiple patterns
   */
  private extractWithPatterns(text: string, patterns: RegExp[]): string {
    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match && match[1]) {
        return match[1].replace(/[^\\d.,]/g, '').replace(/,/g, '');
      }
    }
    return '';
  }
  
  /**
   * Clean creditor name
   */
  private cleanCreditorName(name: string): string {
    return name
      .replace(/[^A-Za-z0-9\\s&'-]/g, ' ')
      .replace(/\\s+/g, ' ')
      .trim()
      .toUpperCase();
  }
  
  /**
   * Check if account is negative
   */
  private isNegativeAccount(status: string, context: string): boolean {
    const negativeKeywords = [
      'charged off', 'charge off', 'collection', 'past due', 'delinquent',
      'late', 'default', 'foreclosure', 'repossession', 'bankruptcy'
    ];
    
    const fullText = (status + ' ' + context).toLowerCase();
    return negativeKeywords.some(keyword => fullText.includes(keyword));
  }
  
  /**
   * Normalize status text
   */
  private normalizeStatus(status: string): string {
    if (!status) return '';
    
    const statusMap: Record<string, string> = {
      'account charged off': 'charged_off',
      'closed': 'closed',
      'open': 'open',
      'current': 'current',
      'never late': 'current'
    };
    
    const statusLower = status.toLowerCase();
    for (const [key, value] of Object.entries(statusMap)) {
      if (statusLower.includes(key)) {
        return value;
      }
    }
    
    return status;
  }
  
  /**
   * Normalize account type
   */
  private normalizeAccountType(accountType: string, creditorName: string): string {
    if (accountType) {
      const typeMap: Record<string, string> = {
        'credit card': 'credit_card',
        'secured card': 'credit_card',
        'auto loan': 'auto_loan',
        'mortgage': 'mortgage',
        'unsecured': 'loan',
        'student loan': 'student_loan'
      };
      
      const typeLower = accountType.toLowerCase();
      for (const [key, value] of Object.entries(typeMap)) {
        if (typeLower.includes(key)) {
          return value;
        }
      }
    }
    
    // Infer from creditor name
    const nameLower = creditorName.toLowerCase();
    if (nameLower.includes('card')) return 'credit_card';
    if (nameLower.includes('auto')) return 'auto_loan';
    if (nameLower.includes('mortgage')) return 'mortgage';
    if (nameLower.includes('student')) return 'student_loan';
    if (nameLower.includes('union')) return 'credit_card'; // Credit unions often issue cards
    
    return '';
  }
  
  /**
   * Normalize date format
   */
  private normalizeDateFormat(dateStr: string): string {
    if (!dateStr) return '';
    
    // Handle MM/YYYY format from Experian
    const mmYYYYMatch = dateStr.match(/^(\\d{1,2})\\/(\\d{4})$/);
    if (mmYYYYMatch) {
      const month = mmYYYYMatch[1].padStart(2, '0');
      const year = mmYYYYMatch[2];
      return `${year}-${month}-01`; // Use first of month as default
    }
    
    // Handle standard MM/DD/YYYY format
    const mmDDYYYYMatch = dateStr.match(/^(\\d{1,2})\\/(\\d{1,2})\\/(\\d{2,4})$/);
    if (mmDDYYYYMatch) {
      const month = mmDDYYYYMatch[1].padStart(2, '0');
      const day = mmDDYYYYMatch[2].padStart(2, '0');
      let year = mmDDYYYYMatch[3];
      
      if (year.length === 2) {
        year = parseInt(year) > 50 ? `19${year}` : `20${year}`;
      }
      
      return `${year}-${month}-${day}`;
    }
    
    return dateStr;
  }
  
  /**
   * Validate tradeline completeness
   */
  private isValidTradeline(tradeline: ParsedTradeline): boolean {
    return Boolean(
      tradeline.creditor_name &&
      tradeline.creditor_name.length > 3 &&
      tradeline.account_number &&
      tradeline.account_number.trim() !== '' &&
      !tradeline.creditor_name.includes('\\n') &&
      !tradeline.creditor_name.includes('Address:')
    );
  }
  
  /**
   * Parse payment history from Experian format
   */
  public parsePaymentHistory(text: string): Array<{month: string, status: string}> {
    const history: Array<{month: string, status: string}> = [];
    
    const paymentSection = text.match(EXPERIAN_PAYMENT_PATTERNS.paymentHistorySection);
    if (!paymentSection) return history;
    
    const sectionText = paymentSection[1];
    const yearMatches = [...sectionText.matchAll(EXPERIAN_PAYMENT_PATTERNS.yearLine)];
    
    for (const yearMatch of yearMatches) {
      const year = yearMatch[1];
      const yearIndex = yearMatch.index || 0;
      
      // Look for month/status pairs after this year
      const afterYear = sectionText.slice(yearIndex + yearMatch[0].length);
      const monthMatches = [...afterYear.matchAll(EXPERIAN_PAYMENT_PATTERNS.monthStatusLine)];
      
      for (const monthMatch of monthMatches) {
        const month = monthMatch[1];
        const status = monthMatch[2];
        
        const monthNum = this.monthNameToNumber(month);
        const isoMonth = `${year}-${monthNum.toString().padStart(2, '0')}`;
        
        history.push({
          month: isoMonth,
          status: this.normalizePaymentStatus(status)
        });
      }
    }
    
    return history;
  }
  
  /**
   * Convert month abbreviation to number
   */
  private monthNameToNumber(monthName: string): number {
    const months: Record<string, number> = {
      'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
      'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
    };
    return months[monthName.toUpperCase()] || 1;
  }
  
  /**
   * Normalize payment status codes
   */
  private normalizePaymentStatus(statusCode: string): string {
    const statusMap: Record<string, string> = {
      'OK': 'On-time',
      'CO': 'Charge Off',
      'CLS': 'Closed',
      'ND': 'No Data',
      'R': 'Repossession',
      'VS': 'Voluntary Surrender',
      'PBC': 'Paid by Creditor',
      'IC': 'Insurance Claim',
      'G': 'Government Claim',
      'D': 'Default',
      'C': 'Collection',
      '30': '30 Days Late',
      '60': '60 Days Late',
      '90': '90+ Days Late',
      '120': '120+ Days Late',
      '150': '150+ Days Late',
      '180': '180+ Days Late'
    };
    
    return statusMap[statusCode.toUpperCase()] || statusCode;
  }
}

// Export singleton instance
export const experianParser = new ExperianSpecificParser();