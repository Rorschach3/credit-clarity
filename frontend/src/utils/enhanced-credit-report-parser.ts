import { ParsedTradeline, ParsedTradelineSchema } from './tradeline/types';

// 1. Section Anchors for Credit Report Segmentation
export const SECTION_ANCHORS = {
  negativeItems: [
    /potentially\s+negative\s+items/i,
    /negative\s+accounts/i,
    /accounts\s+with\s+negative\s+payment\s+history/i,
    /charge\s+offs?\s+and\s+collections/i,
    /delinquent\s+accounts/i
  ],
  goodStanding: [
    /accounts\s+in\s+good\s+standing/i,
    /satisfactory\s+accounts/i,
    /accounts\s+current/i,
    /positive\s+accounts/i
  ],
  inquiries: [
    /requests?\s+for\s+your\s+credit\s+history/i,
    /credit\s+inquir(?:y|ies)/i,
    /hard\s+inquir(?:y|ies)/i,
    /who\s+has\s+accessed\s+your\s+credit/i
  ],
  personalInfo: [
    /personal\s+information/i,
    /consumer\s+identification/i,
    /your\s+identification/i
  ]
};

// 2. Enhanced Regex-Driven Account Block Parsing
export const ACCOUNT_PATTERNS = {
  // Account header - company name with address pattern
  accountHeader: /([A-Z0-9 ]{3,})\s+(?:Address:\s+)?(?:PO BOX|P\.?O\.?\s+BOX|\d+\s+[A-Z\s]+(?:ST|AVE|RD|BLVD|DR|LN|CT|WAY))/im,
  
  // Alternative header patterns for different formats
  headerPatterns: [
    /^([A-Z][A-Z\s&'-]+(?:BANK|CARD|CREDIT|FINANCIAL|CORP|INC|LLC|CO|CAPITAL|CHASE|WELLS|CITI|DISCOVER|AMEX|AMERICAN\s+EXPRESS))/gim,
    /^([A-Z\s&'-]{4,})\s+Account/gim,
    /Company:\s*([A-Z][A-Z\s&'-]+)/gi,
    /Creditor:\s*([A-Z][A-Z\s&'-]+)/gi
  ],
  
  // Account details with optional capture groups
  accountNumber: [
    /Account\s*(?:Number|#):\s*(\*{4}\d{4}|\d{4,16}|[X*]{4,12}\d{4})/gi,
    /Acct\s*(?:Number|#):\s*(\*{4}\d{4}|\d{4,16}|[X*]{4,12}\d{4})/gi,
    /ending\s+in\s+(\d{4})/gi,
    /last\s+4:\s*(\d{4})/gi,
    /\*{4,}(\d{4})/g
  ],
  
  status: [
    /(?:Account\s+)?Status:\s*(Open|Closed|Charged?\s*Off?|Collection|Current|Delinquent|Past\s*Due|Disputed)/gi,
    /Payment\s+Status:\s*(Current|Late|Delinquent|Charged?\s*Off?|Collection)/gi,
    /(Charged?\s*Off?|Collection|Delinquent|Past\s*Due)/gi
  ],
  
  dateOpened: [
    /Date\s+Opened:\s*(\d{1,2}\/\d{1,2}\/(?:\d{2}|\d{4}))/gi,
    /Opened:\s*(\d{1,2}\/\d{1,2}\/(?:\d{2}|\d{4}))/gi,
    /Open\s+Date:\s*(\d{1,2}\/\d{1,2}\/(?:\d{2}|\d{4}))/gi,
    /Date\s+of\s+First\s+Activity:\s*(\d{1,2}\/\d{1,2}\/(?:\d{2}|\d{4}))/gi
  ],
  
  creditLimit: [
    /Credit\s+Limit:\s*\$?([\d,]+\.?\d*)/gi,
    /High\s+Credit:\s*\$?([\d,]+\.?\d*)/gi,
    /Limit:\s*\$?([\d,]+\.?\d*)/gi,
    /Maximum\s+Credit:\s*\$?([\d,]+\.?\d*)/gi
  ],
  
  balance: [
    /Balance:\s*\$?([\d,]+\.?\d*)/gi,
    /Current\s+Balance:\s*\$?([\d,]+\.?\d*)/gi,
    /Outstanding:\s*\$?([\d,]+\.?\d*)/gi,
    /Amount\s+Owed:\s*\$?([\d,]+\.?\d*)/gi,
    /Principal\s+Balance:\s*\$?([\d,]+\.?\d*)/gi
  ],
  
  monthlyPayment: [
    /Monthly\s+Payment:\s*\$?([\d,]+\.?\d*)/gi,
    /Payment\s+Amount:\s*\$?([\d,]+\.?\d*)/gi,
    /Scheduled\s+Payment:\s*\$?([\d,]+\.?\d*)/gi,
    /Min\s+Payment:\s*\$?([\d,]+\.?\d*)/gi
  ]
};

// 3. Payment History Normalization
export const PAYMENT_STATUS_LOOKUP = {
  // Standard abbreviations
  'OK': 'On-time',
  'CO': 'Charge Off',
  'CLS': 'Closed',
  'CUR': 'Current',
  'DEF': 'Deferred',
  'DEL': 'Delinquent',
  'DIS': 'Disputed',
  'FOR': 'Foreclosure',
  'INC': 'Included in Bankruptcy',
  'LSS': 'Loss',
  'MLA': 'Make Lender Arrangement',
  'NR': 'Not Reported',
  'PD': 'Paid',
  'PPD': 'Paid as Previously Described',
  'REP': 'Repossession',
  'SET': 'Settled',
  'VOL': 'Voluntary Surrender',
  'XPN': 'No Payment History Available',
  
  // Numeric codes for days late
  '30': '30 Days Late',
  '60': '60 Days Late',
  '90': '90 Days Late',
  '120': '120+ Days Late',
  
  // Extended patterns
  'LATE': 'Late Payment',
  'SLOW': 'Slow Payment',
  'PAST DUE': 'Past Due',
  'CHARGE OFF': 'Charge Off',
  'COLLECTION': 'Collection'
};

// 4. Account Delimiter Heuristic
export const ACCOUNT_DELIMITERS = {
  patterns: [
    // All caps line with company name followed by address
    /^([A-Z\s&'-]{8,}(?:BANK|CARD|CREDIT|FINANCIAL|CORP|INC|LLC|CO|CAPITAL|CHASE|WELLS|CITI|DISCOVER|AMEX|AMERICAN\s+EXPRESS))\s*\n.*(?:Address:|PO BOX|\d+\s+[A-Z\s]+(?:ST|AVE|RD|BLVD))/gim,
    
    // Account number pattern as delimiter
    /Account\s*(?:Number|#):\s*[*X\d]{4,}/gi,
    
    // Status line as delimiter
    /(?:Account\s+)?Status:\s*[A-Za-z\s]+/gi,
    
    // Credit limit or balance as section marker
    /(?:Credit\s+Limit|Balance):\s*\$[\d,]+/gi
  ],
  
  // Minimum content requirements for valid account block
  minContentLength: 100,
  requiredFields: ['creditor_name', 'account_number']
};

/**
 * Enhanced Credit Report Parser with Section Anchors, Regex Patterns, 
 * Payment History Normalization, and Account Delimiter Heuristics
 */
export class EnhancedCreditReportParser {
  
  /**
   * Step 1: Segment raw OCR text by high-level section anchors
   */
  public segmentBySectionAnchors(rawText: string): {
    negativeItems: string;
    goodStanding: string;
    inquiries: string;
    personalInfo: string;
    other: string;
  } {
    const segments = {
      negativeItems: '',
      goodStanding: '',
      inquiries: '',
      personalInfo: '',
      other: rawText
    };
    
    // Find section boundaries
    const sectionBoundaries: Array<{type: string, start: number, end: number}> = [];
    
    // Look for each section type
    Object.entries(SECTION_ANCHORS).forEach(([sectionType, patterns]) => {
      patterns.forEach(pattern => {
        const matches = [...rawText.matchAll(new RegExp(pattern.source, 'gi'))];
        matches.forEach(match => {
          if (match.index !== undefined) {
            sectionBoundaries.push({
              type: sectionType,
              start: match.index,
              end: match.index + match[0].length
            });
          }
        });
      });
    });
    
    // Sort boundaries by position
    sectionBoundaries.sort((a, b) => a.start - b.start);
    
    // Extract sections based on boundaries
    for (let i = 0; i < sectionBoundaries.length; i++) {
      const current = sectionBoundaries[i];
      const next = sectionBoundaries[i + 1];
      
      const sectionEnd = next ? next.start : rawText.length;
      const sectionText = rawText.slice(current.start, sectionEnd);
      
      switch (current.type) {
        case 'negativeItems':
          segments.negativeItems += sectionText + '\\n';
          break;
        case 'goodStanding':
          segments.goodStanding += sectionText + '\\n';
          break;
        case 'inquiries':
          segments.inquiries += sectionText + '\\n';
          break;
        case 'personalInfo':
          segments.personalInfo += sectionText + '\\n';
          break;
      }
    }
    
    console.log('🔍 Section segmentation results:', {
      negativeItems: segments.negativeItems.length,
      goodStanding: segments.goodStanding.length,
      inquiries: segments.inquiries.length,
      personalInfo: segments.personalInfo.length
    });
    
    return segments;
  }
  
  /**
   * Step 2: Parse account blocks using regex-driven extraction
   */
  public parseAccountBlocks(sectionText: string): string[] {
    if (!sectionText || sectionText.trim().length < 50) {
      return [];
    }
    
    // Use account delimiter heuristic to split text into account blocks
    const accountBlocks: string[] = [];
    const lines = sectionText.split('\\n');
    let currentBlock = '';
    let inAccountBlock = false;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;
      
      // Check if this line starts a new account block
      const isAccountStart = this.isAccountDelimiter(line);
      
      if (isAccountStart) {
        // Save previous block if it exists and meets minimum requirements
        if (currentBlock.length > ACCOUNT_DELIMITERS.minContentLength) {
          accountBlocks.push(currentBlock.trim());
        }
        
        // Start new block
        currentBlock = line + '\\n';
        inAccountBlock = true;
      } else if (inAccountBlock) {
        // Continue building current block
        currentBlock += line + '\\n';
      }
    }
    
    // Don't forget the last block
    if (currentBlock.length > ACCOUNT_DELIMITERS.minContentLength) {
      accountBlocks.push(currentBlock.trim());
    }
    
    console.log(`📊 Found ${accountBlocks.length} account blocks in section`);
    return accountBlocks;
  }
  
  /**
   * Step 3: Extract account details using enhanced regex patterns
   */
  public extractAccountDetails(accountBlock: string): Partial<ParsedTradeline> {
    const details: Partial<ParsedTradeline> = {
      id: crypto.randomUUID(),
      created_at: new Date().toISOString(),
      dispute_count: 0,
      is_negative: false
    };
    
    // Extract creditor name using header patterns
    details.creditor_name = this.extractCreditorName(accountBlock);
    
    // Extract account number
    details.account_number = this.extractWithPatterns(accountBlock, ACCOUNT_PATTERNS.accountNumber);
    
    // Extract status and determine if negative
    details.account_status = this.extractWithPatterns(accountBlock, ACCOUNT_PATTERNS.status);
    details.is_negative = this.isNegativeAccount(details.account_status || '', accountBlock);
    
    // Extract dates
    details.date_opened = this.extractWithPatterns(accountBlock, ACCOUNT_PATTERNS.dateOpened);
    
    // Extract financial details
    const creditLimit = this.extractWithPatterns(accountBlock, ACCOUNT_PATTERNS.creditLimit);
    details.credit_limit = creditLimit ? `$${creditLimit}` : '';
    
    const balance = this.extractWithPatterns(accountBlock, ACCOUNT_PATTERNS.balance);
    details.account_balance = balance ? `$${balance}` : '';
    
    const payment = this.extractWithPatterns(accountBlock, ACCOUNT_PATTERNS.monthlyPayment);
    details.monthly_payment = payment ? `$${payment}` : '';
    
    // Determine account type
    details.account_type = this.determineAccountType(details.creditor_name || '', accountBlock);
    
    // Set credit bureau (could be determined from context or filename)
    details.credit_bureau = this.determineCreditBureau(accountBlock);
    
    console.log('✅ Extracted account details:', {
      creditor: details.creditor_name,
      account: details.account_number,
      status: details.account_status,
      negative: details.is_negative
    });
    
    return details;
  }
  
  /**
   * Step 4: Normalize payment history data
   */
  public normalizePaymentHistory(paymentHistoryText: string): Array<{month: string, status: string}> {
    const history: Array<{month: string, status: string}> = [];
    
    // Look for payment history patterns like:
    // 2015
    // AUG CO
    // JUL CO  
    // JUN OK
    
    const yearPattern = /\\b(20\\d{2})\\b/g;
    const monthStatusPattern = /(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\\s+([A-Z]{2,4}|\\d{2,3})/gi;
    
    let currentYear = '';
    const yearMatches = [...paymentHistoryText.matchAll(yearPattern)];
    
    for (const yearMatch of yearMatches) {
      currentYear = yearMatch[1];
      
      // Find all month/status pairs after this year
      const textAfterYear = paymentHistoryText.slice(yearMatch.index! + yearMatch[0].length);
      const monthMatches = [...textAfterYear.matchAll(monthStatusPattern)];
      
      for (const monthMatch of monthMatches) {
        const month = monthMatch[1];
        const statusCode = monthMatch[2];
        
        // Normalize the status using lookup table
        const normalizedStatus = PAYMENT_STATUS_LOOKUP[statusCode.toUpperCase()] || statusCode;
        
        // Convert month to ISO format
        const monthNum = this.monthNameToNumber(month);
        const isoMonth = `${currentYear}-${monthNum.toString().padStart(2, '0')}`;
        
        history.push({
          month: isoMonth,
          status: normalizedStatus
        });
      }
    }
    
    console.log(`📅 Normalized ${history.length} payment history entries`);
    return history;
  }
  
  /**
   * Main parsing function that combines all strategies
   */
  public parseEnhancedCreditReport(rawText: string, userId?: string): ParsedTradeline[] {
    console.log('🚀 Starting enhanced credit report parsing...');
    
    const tradelines: ParsedTradeline[] = [];
    
    try {
      // Step 1: Segment by section anchors
      const segments = this.segmentBySectionAnchors(rawText);
      
      // Step 2 & 3: Process negative items section
      if (segments.negativeItems) {
        const negativeBlocks = this.parseAccountBlocks(segments.negativeItems);
        for (const block of negativeBlocks) {
          const details = this.extractAccountDetails(block);
          if (this.isValidTradeline(details)) {
            const tradeline = this.createTradeline(details, userId, true);
            if (tradeline) tradelines.push(tradeline);
          }
        }
      }
      
      // Process good standing accounts
      if (segments.goodStanding) {
        const goodBlocks = this.parseAccountBlocks(segments.goodStanding);
        for (const block of goodBlocks) {
          const details = this.extractAccountDetails(block);
          if (this.isValidTradeline(details)) {
            const tradeline = this.createTradeline(details, userId, false);
            if (tradeline) tradelines.push(tradeline);
          }
        }
      }
      
      // If no section-specific content found, parse the entire text
      if (tradelines.length === 0) {
        console.log('📄 No section anchors found, parsing entire document...');
        const allBlocks = this.parseAccountBlocks(rawText);
        for (const block of allBlocks) {
          const details = this.extractAccountDetails(block);
          if (this.isValidTradeline(details)) {
            const tradeline = this.createTradeline(details, userId);
            if (tradeline) tradelines.push(tradeline);
          }
        }
      }
      
      console.log(`🎯 Enhanced parsing completed: ${tradelines.length} tradelines extracted`);
      return tradelines;
      
    } catch (error) {
      console.error('❌ Enhanced parsing failed:', error);
      return [];
    }
  }
  
  // Helper methods
  
  private isAccountDelimiter(line: string): boolean {
    return ACCOUNT_DELIMITERS.patterns.some(pattern => pattern.test(line));
  }
  
  private extractCreditorName(text: string): string {
    // Try account header pattern first
    const headerMatch = text.match(ACCOUNT_PATTERNS.accountHeader);
    if (headerMatch) {
      return this.cleanCreditorName(headerMatch[1]);
    }
    
    // Try alternative header patterns
    for (const pattern of ACCOUNT_PATTERNS.headerPatterns) {
      const match = text.match(pattern);
      if (match) {
        return this.cleanCreditorName(match[1]);
      }
    }
    
    return '';
  }
  
  private cleanCreditorName(name: string): string {
    return name
      .replace(/[^A-Za-z0-9\\s&'-]/g, ' ')
      .replace(/\\s+/g, ' ')
      .trim()
      .toUpperCase();
  }
  
  private extractWithPatterns(text: string, patterns: RegExp[]): string {
    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match && match[1]) {
        return match[1].replace(/[^\\d.,]/g, '');
      }
    }
    return '';
  }
  
  private isNegativeAccount(status: string, context: string): boolean {
    const statusLower = status.toLowerCase();
    const contextLower = context.toLowerCase();
    
    const negativeIndicators = [
      'charge', 'collection', 'delinquent', 'late', 'past due', 
      'default', 'foreclosure', 'repossession', 'bankruptcy'
    ];
    
    return negativeIndicators.some(indicator => 
      statusLower.includes(indicator) || contextLower.includes(indicator)
    );
  }
  
  private determineAccountType(creditorName: string, context: string): string {
    const fullText = (creditorName + ' ' + context).toLowerCase();
    
    if (fullText.includes('mortgage') || fullText.includes('home')) return 'mortgage';
    if (fullText.includes('auto') || fullText.includes('car')) return 'auto_loan';
    if (fullText.includes('student')) return 'student_loan';
    if (fullText.includes('collection')) return 'collection';
    if (fullText.includes('card') || fullText.includes('credit')) return 'credit_card';
    if (fullText.includes('loan')) return 'loan';
    
    return '';
  }
  
  private determineCreditBureau(text: string): string {
    const textLower = text.toLowerCase();
    if (textLower.includes('experian')) return 'experian';
    if (textLower.includes('equifax')) return 'equifax';
    if (textLower.includes('transunion')) return 'transunion';
    return '';
  }
  
  private monthNameToNumber(monthName: string): number {
    const months = {
      'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
      'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
    };
    return months[monthName.toUpperCase() as keyof typeof months] || 1;
  }
  
  private isValidTradeline(details: Partial<ParsedTradeline>): boolean {
    return Boolean(
      details.creditor_name && 
      details.creditor_name.length > 2 &&
      details.account_number &&
      details.account_number.trim() !== ''
    );
  }
  
  private createTradeline(details: Partial<ParsedTradeline>, userId?: string, forceNegative?: boolean): ParsedTradeline | null {
    try {
      const tradelineData = {
        id: details.id || crypto.randomUUID(),
        user_id: userId || '',
        creditor_name: details.creditor_name || '',
        account_number: details.account_number || '',
        account_balance: details.account_balance || '',
        created_at: details.created_at || new Date().toISOString(),
        credit_limit: details.credit_limit || '',
        monthly_payment: details.monthly_payment || '',
        date_opened: details.date_opened || '',
        is_negative: forceNegative !== undefined ? forceNegative : (details.is_negative || false),
        account_type: details.account_type || '',
        account_status: details.account_status || '',
        credit_bureau: details.credit_bureau || '',
        dispute_count: details.dispute_count || 0,
      };
      
      return ParsedTradelineSchema.parse(tradelineData);
    } catch (error) {
      console.warn('Failed to create valid tradeline:', error);
      return null;
    }
  }
}