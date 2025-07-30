import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { 
  parseTradelineFromText, 
  validateTradeline, 
  normalizeTradeline,
  identifyNegativeTradelines,
  groupTradelinesByBureau,
  calculateCreditUtilization,
  extractAccountNumber,
  parseDate,
  determineAccountType,
  type ParsedTradeline 
} from '../tradelineParser';

describe('Tradeline Parser', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('parseDate', () => {
    it('should parse MM/DD/YYYY format', () => {
      expect(parseDate('12/25/2023')).toBe('12/25/2023');
      expect(parseDate('01/01/2020')).toBe('01/01/2020');
    });

    it('should parse MM-DD-YYYY format', () => {
      expect(parseDate('12-25-2023')).toBe('12/25/2023');
      expect(parseDate('01-01-2020')).toBe('01/01/2020');
    });

    it('should parse YYYY/MM/DD format', () => {
      expect(parseDate('2023/12/25')).toBe('12/25/2023');
      expect(parseDate('2020/01/01')).toBe('01/01/2020');
    });

    it('should parse month name formats', () => {
      expect(parseDate('Dec 25, 2023')).toBe('12/25/2023');
      expect(parseDate('January 1, 2020')).toBe('01/01/2020');
      expect(parseDate('25 Dec 2023')).toBe('12/25/2023');
    });

    it('should handle invalid dates', () => {
      expect(parseDate('invalid date')).toBe('');
      expect(parseDate('')).toBe('');
      expect(parseDate('13/32/2023')).toBe('');
    });
  });

  describe('extractAccountNumber', () => {
    it('should extract masked account numbers', () => {
      expect(extractAccountNumber('****1234')).toBe('****1234');
      expect(extractAccountNumber('xxxx5678')).toBe('xxxx5678');
      expect(extractAccountNumber('Account: ****9999')).toBe('****9999');
    });

    it('should extract full account numbers', () => {
      expect(extractAccountNumber('Account: 1234567890')).toBe('1234567890');
      expect(extractAccountNumber('Acct# 9876543210')).toBe('9876543210');
    });

    it('should handle credit card number formats', () => {
      expect(extractAccountNumber('1234-5678-9012-3456')).toBe('1234-5678-9012-3456');
      expect(extractAccountNumber('1234 5678 9012 3456')).toBe('1234567890123456');
    });

    it('should return empty string for invalid input', () => {
      expect(extractAccountNumber('no numbers here')).toBe('');
      expect(extractAccountNumber('')).toBe('');
    });
  });

  describe('determineAccountType', () => {
    it('should identify credit card accounts', () => {
      expect(determineAccountType('CHASE CREDIT CARD')).toBe('Credit Card');
      expect(determineAccountType('CAPITAL ONE VISA')).toBe('Credit Card');
      expect(determineAccountType('AMERICAN EXPRESS')).toBe('Credit Card');
    });

    it('should identify auto loan accounts', () => {
      expect(determineAccountType('FORD CREDIT AUTO LOAN')).toBe('Auto Loan');
      expect(determineAccountType('HONDA FINANCIAL')).toBe('Auto Loan');
      expect(determineAccountType('ALLY AUTO')).toBe('Auto Loan');
    });

    it('should identify mortgage accounts', () => {
      expect(determineAccountType('QUICKEN LOANS MORTGAGE')).toBe('Mortgage');
      expect(determineAccountType('ROCKET MORTGAGE')).toBe('Mortgage');
      expect(determineAccountType('FREEDOM MORTGAGE')).toBe('Mortgage');
    });

    it('should identify student loan accounts', () => {
      expect(determineAccountType('NAVIENT STUDENT LOAN')).toBe('Student Loan');
      expect(determineAccountType('GREAT LAKES EDUCATIONAL')).toBe('Student Loan');
      expect(determineAccountType('DEPT OF EDUCATION')).toBe('Student Loan');
    });

    it('should identify personal loan accounts', () => {
      expect(determineAccountType('PERSONAL LOAN')).toBe('Personal Loan');
      expect(determineAccountType('LENDING CLUB')).toBe('Personal Loan');
      expect(determineAccountType('PROSPER')).toBe('Personal Loan');
    });

    it('should default to Credit Card for unknown types', () => {
      expect(determineAccountType('UNKNOWN BANK')).toBe('Credit Card');
      expect(determineAccountType('')).toBe('Credit Card');
    });
  });

  describe('validateTradeline', () => {
    it('should validate complete tradeline', () => {
      const validTradeline: ParsedTradeline = {
        id: 'test-1',
        creditor_name: 'Test Bank',
        account_number: '****1234',
        date_opened: '01/01/2020',
        account_status: 'Open',
        account_type: 'Credit Card',
        account_balance: '$1,000',
        credit_limit: '$5,000',
        monthly_payment: '$100',
        credit_bureau: 'Experian',
        is_negative: false,
        dispute_count: 0,
        user_id: 'user-123',
      };

      expect(validateTradeline(validTradeline)).toBe(true);
    });

    it('should reject tradeline with missing required fields', () => {
      const invalidTradeline: Partial<ParsedTradeline> = {
        id: 'test-1',
        creditor_name: '',
        account_number: '****1234',
        date_opened: '01/01/2020',
        account_status: 'Open',
        account_type: 'Credit Card',
      };

      expect(validateTradeline(invalidTradeline as ParsedTradeline)).toBe(false);
    });

    it('should reject tradeline with invalid ID', () => {
      const invalidTradeline: ParsedTradeline = {
        id: '',
        creditor_name: 'Test Bank',
        account_number: '****1234',
        date_opened: '01/01/2020',
        account_status: 'Open',
        account_type: 'Credit Card',
        account_balance: '$1,000',
        credit_limit: '$5,000',
        monthly_payment: '$100',
        credit_bureau: 'Experian',
        is_negative: false,
        dispute_count: 0,
        user_id: 'user-123',
      };

      expect(validateTradeline(invalidTradeline)).toBe(false);
    });
  });

  describe('normalizeTradeline', () => {
    it('should normalize creditor name', () => {
      const tradeline: ParsedTradeline = {
        id: 'test-1',
        creditor_name: '  chase credit card  ',
        account_number: '****1234',
        date_opened: '01/01/2020',
        account_status: 'Open',
        account_type: 'Credit Card',
        account_balance: '$1,000',
        credit_limit: '$5,000',
        monthly_payment: '$100',
        credit_bureau: 'Experian',
        is_negative: false,
        dispute_count: 0,
        user_id: 'user-123',
      };

      const normalized = normalizeTradeline(tradeline);
      expect(normalized.creditor_name).toBe('Chase Credit Card');
    });

    it('should normalize account status', () => {
      const tradeline: ParsedTradeline = {
        id: 'test-1',
        creditor_name: 'Test Bank',
        account_number: '****1234',
        date_opened: '01/01/2020',
        account_status: 'open',
        account_type: 'Credit Card',
        account_balance: '$1,000',
        credit_limit: '$5,000',
        monthly_payment: '$100',
        credit_bureau: 'Experian',
        is_negative: false,
        dispute_count: 0,
        user_id: 'user-123',
      };

      const normalized = normalizeTradeline(tradeline);
      expect(normalized.account_status).toBe('Open');
    });

    it('should normalize monetary values', () => {
      const tradeline: ParsedTradeline = {
        id: 'test-1',
        creditor_name: 'Test Bank',
        account_number: '****1234',
        date_opened: '01/01/2020',
        account_status: 'Open',
        account_type: 'Credit Card',
        account_balance: '1000',
        credit_limit: '5000.00',
        monthly_payment: '100',
        credit_bureau: 'Experian',
        is_negative: false,
        dispute_count: 0,
        user_id: 'user-123',
      };

      const normalized = normalizeTradeline(tradeline);
      expect(normalized.account_balance).toBe('$1,000');
      expect(normalized.credit_limit).toBe('$5,000');
      expect(normalized.monthly_payment).toBe('$100');
    });

    it('should normalize dates', () => {
      const tradeline: ParsedTradeline = {
        id: 'test-1',
        creditor_name: 'Test Bank',
        account_number: '****1234',
        date_opened: '2020-01-01',
        account_status: 'Open',
        account_type: 'Credit Card',
        account_balance: '$1,000',
        credit_limit: '$5,000',
        monthly_payment: '$100',
        credit_bureau: 'Experian',
        is_negative: false,
        dispute_count: 0,
        user_id: 'user-123',
      };

      const normalized = normalizeTradeline(tradeline);
      expect(normalized.date_opened).toBe('01/01/2020');
    });
  });

  describe('identifyNegativeTradelines', () => {
    it('should identify negative tradelines by status', () => {
      const tradelines: ParsedTradeline[] = [
        {
          id: 'test-1',
          creditor_name: 'Test Bank',
          account_number: '****1234',
          date_opened: '01/01/2020',
          account_status: 'Charged Off',
          account_type: 'Credit Card',
          account_balance: '$1,000',
          credit_limit: '$5,000',
          monthly_payment: '$100',
          credit_bureau: 'Experian',
          is_negative: false,
          dispute_count: 0,
          user_id: 'user-123',
        },
        {
          id: 'test-2',
          creditor_name: 'Another Bank',
          account_number: '****5678',
          date_opened: '01/01/2019',
          account_status: 'Open',
          account_type: 'Credit Card',
          account_balance: '$500',
          credit_limit: '$2,000',
          monthly_payment: '$50',
          credit_bureau: 'Experian',
          is_negative: false,
          dispute_count: 0,
          user_id: 'user-123',
        },
      ];

      const negative = identifyNegativeTradelines(tradelines);
      expect(negative).toHaveLength(1);
      expect(negative[0].id).toBe('test-1');
      expect(negative[0].is_negative).toBe(true);
    });

    it('should identify negative tradelines by keywords', () => {
      const tradelines: ParsedTradeline[] = [
        {
          id: 'test-1',
          creditor_name: 'Test Bank Collection',
          account_number: '****1234',
          date_opened: '01/01/2020',
          account_status: 'Open',
          account_type: 'Credit Card',
          account_balance: '$1,000',
          credit_limit: '$5,000',
          monthly_payment: '$100',
          credit_bureau: 'Experian',
          is_negative: false,
          dispute_count: 0,
          user_id: 'user-123',
        },
      ];

      const negative = identifyNegativeTradelines(tradelines);
      expect(negative).toHaveLength(1);
      expect(negative[0].is_negative).toBe(true);
    });

    it('should not modify positive tradelines', () => {
      const tradelines: ParsedTradeline[] = [
        {
          id: 'test-1',
          creditor_name: 'Test Bank',
          account_number: '****1234',
          date_opened: '01/01/2020',
          account_status: 'Open',
          account_type: 'Credit Card',
          account_balance: '$1,000',
          credit_limit: '$5,000',
          monthly_payment: '$100',
          credit_bureau: 'Experian',
          is_negative: false,
          dispute_count: 0,
          user_id: 'user-123',
        },
      ];

      const negative = identifyNegativeTradelines(tradelines);
      expect(negative).toHaveLength(0);
    });
  });

  describe('groupTradelinesByBureau', () => {
    it('should group tradelines by credit bureau', () => {
      const tradelines: ParsedTradeline[] = [
        {
          id: 'test-1',
          creditor_name: 'Test Bank',
          account_number: '****1234',
          date_opened: '01/01/2020',
          account_status: 'Open',
          account_type: 'Credit Card',
          account_balance: '$1,000',
          credit_limit: '$5,000',
          monthly_payment: '$100',
          credit_bureau: 'Experian',
          is_negative: false,
          dispute_count: 0,
          user_id: 'user-123',
        },
        {
          id: 'test-2',
          creditor_name: 'Another Bank',
          account_number: '****5678',
          date_opened: '01/01/2019',
          account_status: 'Open',
          account_type: 'Credit Card',
          account_balance: '$500',
          credit_limit: '$2,000',
          monthly_payment: '$50',
          credit_bureau: 'Equifax',
          is_negative: false,
          dispute_count: 0,
          user_id: 'user-123',
        },
        {
          id: 'test-3',
          creditor_name: 'Third Bank',
          account_number: '****9999',
          date_opened: '01/01/2018',
          account_status: 'Open',
          account_type: 'Credit Card',
          account_balance: '$200',
          credit_limit: '$1,000',
          monthly_payment: '$25',
          credit_bureau: 'Experian',
          is_negative: false,
          dispute_count: 0,
          user_id: 'user-123',
        },
      ];

      const grouped = groupTradelinesByBureau(tradelines);
      
      expect(grouped).toHaveProperty('Experian');
      expect(grouped).toHaveProperty('Equifax');
      expect(grouped.Experian).toHaveLength(2);
      expect(grouped.Equifax).toHaveLength(1);
    });

    it('should handle empty tradelines array', () => {
      const grouped = groupTradelinesByBureau([]);
      expect(Object.keys(grouped)).toHaveLength(0);
    });

    it('should handle tradelines without bureau', () => {
      const tradelines: ParsedTradeline[] = [
        {
          id: 'test-1',
          creditor_name: 'Test Bank',
          account_number: '****1234',
          date_opened: '01/01/2020',
          account_status: 'Open',
          account_type: 'Credit Card',
          account_balance: '$1,000',
          credit_limit: '$5,000',
          monthly_payment: '$100',
          credit_bureau: '',
          is_negative: false,
          dispute_count: 0,
          user_id: 'user-123',
        },
      ];

      const grouped = groupTradelinesByBureau(tradelines);
      expect(grouped).toHaveProperty('Unknown');
      expect(grouped.Unknown).toHaveLength(1);
    });
  });

  describe('calculateCreditUtilization', () => {
    it('should calculate credit utilization correctly', () => {
      const tradelines: ParsedTradeline[] = [
        {
          id: 'test-1',
          creditor_name: 'Test Bank',
          account_number: '****1234',
          date_opened: '01/01/2020',
          account_status: 'Open',
          account_type: 'Credit Card',
          account_balance: '$1,000',
          credit_limit: '$5,000',
          monthly_payment: '$100',
          credit_bureau: 'Experian',
          is_negative: false,
          dispute_count: 0,
          user_id: 'user-123',
        },
        {
          id: 'test-2',
          creditor_name: 'Another Bank',
          account_number: '****5678',
          date_opened: '01/01/2019',
          account_status: 'Open',
          account_type: 'Credit Card',
          account_balance: '$500',
          credit_limit: '$2,000',
          monthly_payment: '$50',
          credit_bureau: 'Experian',
          is_negative: false,
          dispute_count: 0,
          user_id: 'user-123',
        },
      ];

      const utilization = calculateCreditUtilization(tradelines);
      // Total balance: $1,500, Total limit: $7,000
      // Utilization: 1500/7000 = 0.214 = 21.4%
      expect(utilization).toBeCloseTo(21.4, 1);
    });

    it('should handle zero credit limit', () => {
      const tradelines: ParsedTradeline[] = [
        {
          id: 'test-1',
          creditor_name: 'Test Bank',
          account_number: '****1234',
          date_opened: '01/01/2020',
          account_status: 'Open',
          account_type: 'Credit Card',
          account_balance: '$1,000',
          credit_limit: '$0',
          monthly_payment: '$100',
          credit_bureau: 'Experian',
          is_negative: false,
          dispute_count: 0,
          user_id: 'user-123',
        },
      ];

      const utilization = calculateCreditUtilization(tradelines);
      expect(utilization).toBe(0);
    });

    it('should handle non-credit card accounts', () => {
      const tradelines: ParsedTradeline[] = [
        {
          id: 'test-1',
          creditor_name: 'Test Bank',
          account_number: '****1234',
          date_opened: '01/01/2020',
          account_status: 'Open',
          account_type: 'Auto Loan',
          account_balance: '$10,000',
          credit_limit: '$0',
          monthly_payment: '$300',
          credit_bureau: 'Experian',
          is_negative: false,
          dispute_count: 0,
          user_id: 'user-123',
        },
      ];

      const utilization = calculateCreditUtilization(tradelines);
      expect(utilization).toBe(0);
    });

    it('should handle empty tradelines array', () => {
      const utilization = calculateCreditUtilization([]);
      expect(utilization).toBe(0);
    });
  });

  describe('parseTradelineFromText', () => {
    it('should parse tradeline from structured text', () => {
      const text = `
        CHASE CREDIT CARD
        Account Number: ****1234
        Date Opened: 01/01/2020
        Account Status: Open
        Balance: $1,000
        Credit Limit: $5,000
        Monthly Payment: $100
        Credit Bureau: Experian
      `;

      const tradeline = parseTradelineFromText(text, 'user-123');
      
      expect(tradeline.creditor_name).toBe('CHASE CREDIT CARD');
      expect(tradeline.account_number).toBe('****1234');
      expect(tradeline.date_opened).toBe('01/01/2020');
      expect(tradeline.account_status).toBe('Open');
      expect(tradeline.account_balance).toBe('$1,000');
      expect(tradeline.credit_limit).toBe('$5,000');
      expect(tradeline.monthly_payment).toBe('$100');
      expect(tradeline.credit_bureau).toBe('Experian');
      expect(tradeline.account_type).toBe('Credit Card');
      expect(tradeline.user_id).toBe('user-123');
    });

    it('should handle missing information gracefully', () => {
      const text = `
        UNKNOWN BANK
        Account Number: ****9999
      `;

      const tradeline = parseTradelineFromText(text, 'user-123');
      
      expect(tradeline.creditor_name).toBe('UNKNOWN BANK');
      expect(tradeline.account_number).toBe('****9999');
      expect(tradeline.date_opened).toBe('');
      expect(tradeline.account_status).toBe('');
      expect(tradeline.account_balance).toBe('');
      expect(tradeline.credit_limit).toBe('');
      expect(tradeline.monthly_payment).toBe('');
      expect(tradeline.credit_bureau).toBe('');
      expect(tradeline.account_type).toBe('Credit Card');
    });

    it('should identify negative tradelines', () => {
      const text = `
        COLLECTION AGENCY
        Account Number: ****1234
        Date Opened: 01/01/2020
        Account Status: Charged Off
        Balance: $1,000
        Credit Limit: $5,000
        Monthly Payment: $100
        Credit Bureau: Experian
      `;

      const tradeline = parseTradelineFromText(text, 'user-123');
      
      expect(tradeline.is_negative).toBe(true);
    });
  });
});