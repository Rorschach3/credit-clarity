import { EnhancedCreditReportParser, SECTION_ANCHORS, ACCOUNT_PATTERNS, PAYMENT_STATUS_LOOKUP } from '../enhanced-credit-report-parser';

describe('EnhancedCreditReportParser', () => {
  let parser: EnhancedCreditReportParser;
  
  beforeEach(() => {
    parser = new EnhancedCreditReportParser();
  });

  describe('Section Anchor Segmentation', () => {
    it('should identify negative items section', () => {
      const mockText = `
        Consumer Information
        John Doe
        123 Main St
        
        POTENTIALLY NEGATIVE ITEMS
        COLLECTION AGENCY XYZ
        Address: PO BOX 12345
        Account Number: ****1234
        Status: Collection
        
        ACCOUNTS IN GOOD STANDING
        CHASE BANK
        Address: PO BOX 56789
        Account Number: ****5678
        Status: Open
      `;
      
      const segments = parser.segmentBySectionAnchors(mockText);
      
      expect(segments.negativeItems).toContain('POTENTIALLY NEGATIVE ITEMS');
      expect(segments.negativeItems).toContain('COLLECTION AGENCY XYZ');
      expect(segments.goodStanding).toContain('ACCOUNTS IN GOOD STANDING');
      expect(segments.goodStanding).toContain('CHASE BANK');
    });

    it('should handle multiple section patterns', () => {
      const mockText = `
        NEGATIVE ACCOUNTS
        Bad Account 1
        
        ACCOUNTS WITH NEGATIVE PAYMENT HISTORY  
        Bad Account 2
        
        SATISFACTORY ACCOUNTS
        Good Account 1
      `;
      
      const segments = parser.segmentBySectionAnchors(mockText);
      
      expect(segments.negativeItems).toContain('NEGATIVE ACCOUNTS');
      expect(segments.negativeItems).toContain('ACCOUNTS WITH NEGATIVE PAYMENT HISTORY');
      expect(segments.goodStanding).toContain('SATISFACTORY ACCOUNTS');
    });
  });

  describe('Account Block Parsing', () => {
    it('should parse account blocks with company name and address pattern', () => {
      const sectionText = `
        AMERICAN EXPRESS CARD
        Address: PO BOX 981532
        Account Number: ****1234
        Status: Open
        Balance: $1,500
        
        CHASE MANHATTAN BANK
        Address: 123 MAIN STREET
        Account Number: ****5678
        Status: Closed
        Balance: $0
      `;
      
      const blocks = parser.parseAccountBlocks(sectionText);
      
      expect(blocks).toHaveLength(2);
      expect(blocks[0]).toContain('AMERICAN EXPRESS');
      expect(blocks[1]).toContain('CHASE MANHATTAN');
    });

    it('should handle various address formats', () => {
      const sectionText = `
        CAPITAL ONE BANK
        Address: P.O. BOX 30285
        Account Number: ****9999
        
        DISCOVER CARD
        Address: 1234 CORPORATE BLVD
        Account Number: ****1111
      `;
      
      const blocks = parser.parseAccountBlocks(sectionText);
      
      expect(blocks).toHaveLength(2);
      expect(blocks[0]).toContain('CAPITAL ONE');
      expect(blocks[1]).toContain('DISCOVER');
    });
  });

  describe('Regex-Driven Account Detail Extraction', () => {
    it('should extract creditor name from header pattern', () => {
      const accountBlock = `
        WELLS FARGO BANK
        Address: PO BOX 12345
        Account Number: ****1234
        Status: Open
      `;
      
      const details = parser.extractAccountDetails(accountBlock);
      
      expect(details.creditor_name).toBe('WELLS FARGO BANK');
    });

    it('should extract account number with various formats', () => {
      const testCases = [
        { text: 'Account Number: ****1234', expected: '1234' },
        { text: 'Acct #: XXXX5678', expected: '5678' },
        { text: 'ending in 9999', expected: '9999' },
        { text: 'last 4: 1111', expected: '1111' }
      ];
      
      testCases.forEach(({ text, expected }) => {
        const details = parser.extractAccountDetails(text);
        expect(details.account_number).toContain(expected);
      });
    });

    it('should extract financial details with currency formatting', () => {
      const accountBlock = `
        CREDIT CARD COMPANY
        Balance: $2,500.00
        Credit Limit: $10,000
        Monthly Payment: $50.00
        Status: Current
      `;
      
      const details = parser.extractAccountDetails(accountBlock);
      
      expect(details.account_balance).toBe('$2,500.00');
      expect(details.credit_limit).toBe('$10,000');
      expect(details.monthly_payment).toBe('$50.00');
    });

    it('should detect negative accounts', () => {
      const negativeBlocks = [
        'Status: Charged Off',
        'Status: Collection',
        'Account Status: Delinquent',
        'Payment Status: Past Due'
      ];
      
      negativeBlocks.forEach(block => {
        const details = parser.extractAccountDetails(block);
        expect(details.is_negative).toBe(true);
      });
    });

    it('should handle optional capture groups', () => {
      const incompleteBlock = `
        SOME BANK
        Account Number: ****1234
        // Missing other fields
      `;
      
      const details = parser.extractAccountDetails(incompleteBlock);
      
      expect(details.creditor_name).toBe('SOME BANK');
      expect(details.account_number).toContain('1234');
      expect(details.account_balance).toBe('');
      expect(details.credit_limit).toBe('');
    });
  });

  describe('Payment History Normalization', () => {
    it('should normalize standard payment history format', () => {
      const paymentText = `
        2015
        AUG CO
        JUL CO
        JUN OK
        MAY 30
        APR OK
        
        2014
        DEC CUR
        NOV DEL
      `;
      
      const history = parser.normalizePaymentHistory(paymentText);
      
      expect(history).toContainEqual({ month: '2015-08', status: 'Charge Off' });
      expect(history).toContainEqual({ month: '2015-07', status: 'Charge Off' });
      expect(history).toContainEqual({ month: '2015-06', status: 'On-time' });
      expect(history).toContainEqual({ month: '2015-05', status: '30 Days Late' });
      expect(history).toContainEqual({ month: '2014-12', status: 'Current' });
    });

    it('should handle various status codes', () => {
      const paymentText = `
        2023
        JAN CLS
        FEB REP
        MAR SET
        APR 120
      `;
      
      const history = parser.normalizePaymentHistory(paymentText);
      
      expect(history).toContainEqual({ month: '2023-01', status: 'Closed' });
      expect(history).toContainEqual({ month: '2023-02', status: 'Repossession' });
      expect(history).toContainEqual({ month: '2023-03', status: 'Settled' });
      expect(history).toContainEqual({ month: '2023-04', status: '120+ Days Late' });
    });

    it('should handle unknown status codes gracefully', () => {
      const paymentText = `
        2023
        JAN UNK
        FEB XYZ
      `;
      
      const history = parser.normalizePaymentHistory(paymentText);
      
      expect(history).toContainEqual({ month: '2023-01', status: 'UNK' });
      expect(history).toContainEqual({ month: '2023-02', status: 'XYZ' });
    });
  });

  describe('Account Delimiter Heuristic', () => {
    it('should identify account delimiters correctly', () => {
      const testLines = [
        'AMERICAN EXPRESS CARD',
        'Address: PO BOX 123',
        'Account Number: ****1234',
        'Status: Open'
      ];
      
      // Test private method through parser instance
      const parser = new EnhancedCreditReportParser();
      
      // The first line should be identified as an account delimiter
      expect(parser['isAccountDelimiter'](testLines[0])).toBe(true);
      expect(parser['isAccountDelimiter'](testLines[2])).toBe(true);
      expect(parser['isAccountDelimiter'](testLines[3])).toBe(true);
    });
  });

  describe('Full Integration Tests', () => {
    it('should parse a complete mock credit report', () => {
      const mockCreditReport = `
        EXPERIAN CREDIT REPORT
        Consumer: John Doe
        
        POTENTIALLY NEGATIVE ITEMS
        
        COLLECTION SERVICES INC
        Address: PO BOX 98765
        Account Number: ****1234
        Original Creditor: MEDICAL CENTER
        Status: Collection
        Balance: $500.00
        Date Opened: 01/15/2020
        
        CHARGED OFF BANK
        Address: 123 BANK STREET  
        Account Number: ****5678
        Status: Charged Off
        Balance: $2,500.00
        Credit Limit: $5,000.00
        Date Opened: 03/10/2018
        
        ACCOUNTS IN GOOD STANDING
        
        CHASE FREEDOM CARD  
        Address: PO BOX 15298
        Account Number: ****9999
        Status: Open
        Balance: $1,200.00
        Credit Limit: $8,000.00
        Monthly Payment: $50.00
        Date Opened: 06/01/2015
        
        WELLS FARGO AUTO LOAN
        Address: PO BOX 54321
        Account Number: ****7777
        Status: Current
        Balance: $15,000.00
        Monthly Payment: $350.00
        Date Opened: 09/15/2021
      `;
      
      const tradelines = parser.parseEnhancedCreditReport(mockCreditReport, 'test-user-123');
      
      expect(tradelines).toHaveLength(4);
      
      // Check negative items
      const negativeItems = tradelines.filter(t => t.is_negative);
      expect(negativeItems).toHaveLength(2);
      expect(negativeItems.some(t => t.creditor_name.includes('COLLECTION'))).toBe(true);
      expect(negativeItems.some(t => t.creditor_name.includes('CHARGED OFF'))).toBe(true);
      
      // Check positive items
      const positiveItems = tradelines.filter(t => !t.is_negative);
      expect(positiveItems).toHaveLength(2);
      expect(positiveItems.some(t => t.creditor_name.includes('CHASE'))).toBe(true);
      expect(positiveItems.some(t => t.creditor_name.includes('WELLS FARGO'))).toBe(true);
      
      // Verify specific details
      const chaseCard = tradelines.find(t => t.creditor_name.includes('CHASE'));
      expect(chaseCard?.account_balance).toBe('$1,200.00');
      expect(chaseCard?.credit_limit).toBe('$8,000.00');
      expect(chaseCard?.monthly_payment).toBe('$50.00');
    });

    it('should handle edge cases gracefully', () => {
      const edgeCases = [
        '', // Empty string
        'Not a credit report', // No relevant content
        'SOME BANK\\nAccount: 1234', // Minimal content
      ];
      
      edgeCases.forEach(text => {
        expect(() => {
          const result = parser.parseEnhancedCreditReport(text);
          expect(Array.isArray(result)).toBe(true);
        }).not.toThrow();
      });
    });
  });

  describe('Validation and Error Handling', () => {
    it('should validate tradeline completeness', () => {
      const validTradeline = {
        creditor_name: 'VALID BANK',
        account_number: '****1234',
        account_status: 'Open'
      };
      
      const invalidTradeline = {
        creditor_name: 'X', // Too short
        account_number: '',
        account_status: ''
      };
      
      expect(parser['isValidTradeline'](validTradeline)).toBe(true);
      expect(parser['isValidTradeline'](invalidTradeline)).toBe(false);
    });

    it('should handle malformed data gracefully', () => {
      const malformedBlock = `
        MALFORMED DATA!!!@#$%
        $$$$$$$$$$$$$$$$$$$$
        ################
      `;
      
      const details = parser.extractAccountDetails(malformedBlock);
      
      // Should not throw and should return some default values
      expect(typeof details).toBe('object');
      expect(details.id).toBeDefined();
      expect(details.created_at).toBeDefined();
    });
  });
});