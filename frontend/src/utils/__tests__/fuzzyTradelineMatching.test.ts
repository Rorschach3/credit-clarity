// Unit tests for fuzzy tradeline matching functionality
import {
  normalizeCreditorName,
  extractAccountPrefix,
  normalizeDate,
  isTradelineMatch,
  mergeTradelineFields,
  
} from '../fuzzyTradelineMatching';
import { ParsedTradeline } from '../tradelineParser';

// Mock Supabase client for database tests
jest.mock('@/integrations/supabase/client', () => ({
  supabase: {
    from: jest.fn(() => ({
      select: jest.fn(() => ({
        eq: jest.fn(() => ({
          data: [],
          error: null
        }))
      })),
      update: jest.fn(() => ({
        eq: jest.fn(() => ({
          data: [],
          error: null
        }))
      }))
    }))
  }
}));

// Mock tradeline factory
const createMockTradeline = (overrides: Partial<ParsedTradeline> = {}): ParsedTradeline => ({
  id: 'test-id',
  user_id: 'test-user',
  creditor_name: 'Chase Bank',
  account_number: '1234-5678-9012',
  account_balance: '$1,500',
  account_status: 'paid on time',
  account_type: 'Credit Card',
  date_opened: '12-20-2020',
  is_negative: false,
  dispute_count: 0,
  created_at: '2024-01-01T00:00:00Z',
  credit_limit: '$5,000',
  credit_bureau: 'Experian',
  monthly_payment: '$50',
  ...overrides
});

describe('Fuzzy Tradeline Matching', () => {
  describe('normalizeCreditorName', () => {
    test('should normalize creditor names consistently', () => {
      expect(normalizeCreditorName('CHASE BANK')).toBe('chase');
      expect(normalizeCreditorName('  Chase   Bank  ')).toBe('chase');
      expect(normalizeCreditorName('Chase Bank, N.A.')).toBe('chase');
      expect(normalizeCreditorName('Bank of America Corp')).toBe('of america');
      expect(normalizeCreditorName('')).toBe('');
    });

    test('should handle special characters and common suffixes', () => {
      expect(normalizeCreditorName('Wells Fargo & Company')).toBe('wells fargo');
      expect(normalizeCreditorName('Capital One Bank (USA), N.A.')).toBe('capital one usa na');
      expect(normalizeCreditorName('Discover Card Services, LLC')).toBe('discover services');
    });
  });

  describe('extractAccountPrefix', () => {
    test('should extract first 4 digits from various account formats', () => {
      expect(extractAccountPrefix('1234-5678-9012')).toBe('1234');
      expect(extractAccountPrefix('1234 5678 9012')).toBe('1234');
      expect(extractAccountPrefix('1234567890123456')).toBe('1234');
      expect(extractAccountPrefix('xxxx-xxxx-xxxx-1234')).toBe('1234');
      expect(extractAccountPrefix('ABC1234DEF5678')).toBe('1234');
      expect(extractAccountPrefix('')).toBe('');
      expect(extractAccountPrefix('ABCD-EFGH-IJKL')).toBe('');
    });

    test('should handle edge cases', () => {
      expect(extractAccountPrefix('123')).toBe('123'); // Less than 4 digits
      expect(extractAccountPrefix('12')).toBe('12');
      expect(extractAccountPrefix('1')).toBe('1');
    });
  });

  describe('normalizeDate', () => {
    test('should normalize various date formats', () => {
      expect(normalizeDate('2020-01-15')).toBe('2020-01-15');
      expect(normalizeDate('01/15/2020')).toBe('2020-01-15');
      expect(normalizeDate('Jan 15, 2020')).toBe('2020-01-15');
      expect(normalizeDate('2020-1-15')).toBe('2020-01-15');
      expect(normalizeDate('')).toBe('');
      expect(normalizeDate('invalid-date')).toBe('');
    });
  });

  describe('isTradelineMatch', () => {
    test('should match tradelines with identical normalized data', () => {
      const tradeline1 = createMockTradeline({
        creditor_name: 'Chase Bank',
        account_number: '1234-5678-9012',
        date_opened: '2020-01-15'
      });

      const tradeline2 = createMockTradeline({
        creditor_name: 'CHASE BANK',
        account_number: '1234 5678 9012 3456',
        date_opened: '01/15/2020'
      });

      const result = isTradelineMatch(tradeline1, tradeline2);
      
      expect(result.isMatch).toBe(true);
      expect(result.confidence).toBe(100);
      expect(result.matchingCriteria.creditorNameMatch).toBe(true);
      expect(result.matchingCriteria.accountNumberMatch).toBe(true);
      expect(result.matchingCriteria.dateOpenedMatch).toBe(true);
    });

    test('should not match tradelines with different creditors', () => {
      const tradeline1 = createMockTradeline({
        creditor_name: 'Chase Bank',
        account_number: '1234-5678-9012',
        date_opened: '2020-01-15'
      });

      const tradeline2 = createMockTradeline({
        creditor_name: 'Bank of America',
        account_number: '1234-5678-9012',
        date_opened: '2020-01-15'
      });

      const result = isTradelineMatch(tradeline1, tradeline2);
      
      expect(result.isMatch).toBe(false);
      expect(result.matchingCriteria.creditorNameMatch).toBe(false);
      expect(result.matchingCriteria.accountNumberMatch).toBe(true);
      expect(result.matchingCriteria.dateOpenedMatch).toBe(true);
    });

    test('should not match tradelines with different account prefixes', () => {
      const tradeline1 = createMockTradeline({
        creditor_name: 'Chase Bank',
        account_number: '1234-5678-9012',
        date_opened: '2020-01-15'
      });

      const tradeline2 = createMockTradeline({
        creditor_name: 'Chase Bank',
        account_number: '5678-1234-9012',
        date_opened: '2020-01-15'
      });

      const result = isTradelineMatch(tradeline1, tradeline2);
      
      expect(result.isMatch).toBe(false);
      expect(result.matchingCriteria.creditorNameMatch).toBe(true);
      expect(result.matchingCriteria.accountNumberMatch).toBe(false);
      expect(result.matchingCriteria.dateOpenedMatch).toBe(true);
    });

    test('should not match tradelines with different dates', () => {
      const tradeline1 = createMockTradeline({
        creditor_name: 'Chase Bank',
        account_number: '1234-5678-9012',
        date_opened: '2020-01-15'
      });

      const tradeline2 = createMockTradeline({
        creditor_name: 'Chase Bank',
        account_number: '1234-5678-9012',
        date_opened: '2021-01-15'
      });

      const result = isTradelineMatch(tradeline1, tradeline2);
      
      expect(result.isMatch).toBe(false);
      expect(result.matchingCriteria.creditorNameMatch).toBe(true);
      expect(result.matchingCriteria.accountNumberMatch).toBe(true);
      expect(result.matchingCriteria.dateOpenedMatch).toBe(false);
    });

    test('should calculate partial confidence scores', () => {
      const tradeline1 = createMockTradeline({
        creditor_name: 'Chase Bank',
        account_number: '1234-5678-9012',
        date_opened: '2020-01-15'
      });

      const tradeline2 = createMockTradeline({
        creditor_name: 'Chase Bank',
        account_number: '5678-1234-9012', // Different prefix
        date_opened: '2020-01-15'
      });

      const result = isTradelineMatch(tradeline1, tradeline2);
      
      expect(result.isMatch).toBe(true);
      expect(result.confidence).toBe(70); // 40 (creditor) + 30 (date) = 70
    });
  });

  describe('mergeTradelineFields', () => {
    test('should only update empty fields in existing tradeline', () => {
      const existingTradeline = createMockTradeline({
        account_balance: '',
        credit_limit: '$5,000.00',
        monthly_payment: '',
        account_status: 'Open',
        credit_bureau: ''
      });

      const incomingTradeline = createMockTradeline({
        account_balance: '$2,500.00',
        credit_limit: '$10,000.00', // This should not override
        monthly_payment: '$75.00',
        account_status: 'Closed', // This should not override
        credit_bureau: 'TransUnion'
      });

      const updates = mergeTradelineFields(existingTradeline, incomingTradeline);
      
      expect(updates).toEqual({
        account_balance: '$2,500.00',
        monthly_payment: '$75.00',
        credit_bureau: 'TransUnion'
      });
      
      // Should not include fields that already have values
      expect(updates).not.toHaveProperty('credit_limit');
      expect(updates).not.toHaveProperty('account_status');
    });

    test('should update negative status when incoming is more specific', () => {
      const existingTradeline = createMockTradeline({
        is_negative: false
      });

      const incomingTradeline = createMockTradeline({
        is_negative: true
      });

      const updates = mergeTradelineFields(existingTradeline, incomingTradeline);
      
      expect(updates).toHaveProperty('is_negative', true);
    });

    test('should handle $0 as empty values', () => {
      const existingTradeline = createMockTradeline({
        account_balance: '$0',
        credit_limit: '$0'
      });

      const incomingTradeline = createMockTradeline({
        account_balance: '$1,500.00',
        credit_limit: '$5,000.00'
      });

      const updates = mergeTradelineFields(existingTradeline, incomingTradeline);
      
      expect(updates).toEqual({
        account_balance: '$1,500.00',
        credit_limit: '$5,000.00'
      });
    });

    test('should return empty object when no updates needed', () => {
      const existingTradeline = createMockTradeline({
        account_balance: '$1,500.00',
        credit_limit: '$5,000.00',
        monthly_payment: '$50.00',
        account_status: 'Open',
        credit_bureau: 'Experian'
      });

      const incomingTradeline = createMockTradeline({
        account_balance: '$2,000.00', // Different but existing has value
        credit_limit: '$10,000.00'   // Different but existing has value
      });

      const updates = mergeTradelineFields(existingTradeline, incomingTradeline);
      
      expect(updates).toEqual({});
    });
  });

  describe('Real-world Scenarios', () => {
    test('should match credit cards with different formatting', () => {
      const existing = createMockTradeline({
        creditor_name: 'CHASE BANK USA, N.A.',
        account_number: '4532-1234-5678-9012',
        date_opened: '2020-03-15',
        account_balance: '$2,500.00',
        credit_limit: ''
      });

      const incoming = createMockTradeline({
        creditor_name: 'Chase Bank',
        account_number: '4532 **** **** 9012',
        date_opened: '03/15/2020',
        account_balance: '$2,800.00',
        credit_limit: '$10,000.00'
      });

      const result = isTradelineMatch(incoming, existing);
      expect(result.isMatch).toBe(true);
      expect(result.confidence).toBe(100);

      const updates = mergeTradelineFields(existing, incoming);
      expect(updates).toEqual({
        credit_limit: '$10,000.00'
      });
      // Should not update account_balance as existing has value
      expect(updates).not.toHaveProperty('account_balance');
    });

    test('should handle mortgage accounts correctly', () => {
      const existing = createMockTradeline({
        creditor_name: 'Wells Fargo Home Mortgage',
        account_number: '8765-4321-0000',
        date_opened: '2019-06-01',
        account_type: 'Mortgage',
        monthly_payment: ''
      });

      const incoming = createMockTradeline({
        creditor_name: 'WELLS FARGO BANK, N.A.',
        account_number: '8765432100001234',
        date_opened: '06/01/2019',
        account_type: 'Real Estate Mortgage',
        monthly_payment: '$1,850.00'
      });

      const result = isTradelineMatch(incoming, existing);
      expect(result.isMatch).toBe(true);
      
      const updates = mergeTradelineFields(existing, incoming);
      expect(updates.monthly_payment).toBe('$1,850.00');
    });

    test('should handle auto loans with dealer variations', () => {
      const existing = createMockTradeline({
        creditor_name: 'Toyota Motor Credit Corporation',
        account_number: '9876-5432-1000',
        date_opened: '2021-08-15'
      });

      const incoming = createMockTradeline({
        creditor_name: 'TOYOTA MOTOR CREDIT CORP',
        account_number: '9876 5432 1000 5678',
        date_opened: '08/15/2021'
      });

      const result = isTradelineMatch(incoming, existing);
      expect(result.isMatch).toBe(true);
    });

    test('should not match similar but different accounts', () => {
      const existing = createMockTradeline({
        creditor_name: 'Chase Bank',
        account_number: '1234-5678-9012',
        date_opened: '2020-01-15'
      });

      const incoming = createMockTradeline({
        creditor_name: 'Chase Bank',
        account_number: '1234-5678-9012',
        date_opened: '2021-01-15' // Different year
      });

      const result = isTradelineMatch(incoming, existing);
      expect(result.isMatch).toBe(false);
    });
  });

  describe('Edge Cases and Error Handling', () => {
    test('should handle null and undefined values gracefully', () => {
      const tradeline1 = createMockTradeline({
        creditor_name: '',
        account_number: '',
        date_opened: ''
      });

      const tradeline2 = createMockTradeline({
        creditor_name: 'Chase Bank',
        account_number: '1234-5678-9012',
        date_opened: '2020-01-15'
      });

      const result = isTradelineMatch(tradeline1, tradeline2);
      expect(result.isMatch).toBe(false);
      expect(result.confidence).toBe(0);
    });

    test('should handle very short account numbers', () => {
      expect(extractAccountPrefix('123')).toBe('123');
      expect(extractAccountPrefix('12')).toBe('12');
      expect(extractAccountPrefix('1')).toBe('1');
      expect(extractAccountPrefix('')).toBe('');
    });

    test('should handle malformed dates', () => {
      expect(normalizeDate('not-a-date')).toBe('');
      expect(normalizeDate('2020-13-45')).toBe(''); // Invalid month/day
      expect(normalizeDate('32/15/2020')).toBe(''); // Invalid format
      expect(normalizeDate('')).toBe('');
    });

    test('should handle account numbers with no digits', () => {
      expect(extractAccountPrefix('ABCD-EFGH-IJKL')).toBe('');
      expect(extractAccountPrefix('****-****-****')).toBe('');
      expect(extractAccountPrefix('xxxx-xxxx-xxxx')).toBe('');
    });

    test('should handle very long creditor names', () => {
      const longName = 'A'.repeat(100) + ' Bank Corporation LLC';
      const normalized = normalizeCreditorName(longName);
      expect(normalized).toBe('a'.repeat(100));
    });
  });

  describe('International and Special Cases', () => {
    test('should handle international bank names', () => {
      expect(normalizeCreditorName('HSBC Bank USA, National Association'))
        .toBe('hsbc usa national association');
      expect(normalizeCreditorName('Bank of Montreal'))
        .toBe('of montreal');
      expect(normalizeCreditorName('TD Bank, N.A.'))
        .toBe('td na');
    });

    test('should handle credit union variations', () => {
      expect(normalizeCreditorName('Navy Federal Credit Union'))
        .toBe('navy federal credit union');
      expect(normalizeCreditorName('PENTAGON FEDERAL CREDIT UNION'))
        .toBe('pentagon federal credit union');
    });

    test('should handle store credit cards', () => {
      const existing = createMockTradeline({
        creditor_name: 'Target Corporation',
        account_number: '1111-2222-3333',
        date_opened: '2022-11-01'
      });

      const incoming = createMockTradeline({
        creditor_name: 'TARGET CORP',
        account_number: '1111 2222 3333 4444',
        date_opened: '11/01/2022'
      });

      const result = isTradelineMatch(incoming, existing);
      expect(result.isMatch).toBe(true);
    });
  });

  describe('Performance and Boundary Tests', () => {
    test('should handle multiple matching criteria combinations', () => {
      const testCases = [
        {
          creditor_name: 'Only creditor matches',
          existing: { creditor_name: 'Chase', account_number: '1234', date_opened: '2020-01-01' },
          incoming: { creditor_name: 'Chase', account_number: '5678', date_opened: '2021-01-01' },
          expectedMatch: false,
          expectedConfidence: 40
        },
        {
          creditorName: 'Creditor and account match',
          existing: { creditor_name: 'Chase', account_number: '1234', date_opened: '2020-01-01' },
          incoming: { creditor_name: 'Chase', account_number: '1234', date_opened: '2021-01-01' },
          expectedMatch: false,
          expectedConfidence: 70
        },
        {
          creditorName: 'Account and date match',
          existing: { creditor_name: 'Chase', account_number: '1234', date_opened: '2020-01-01' },
          incoming: { creditor_name: 'Wells Fargo', account_number: '1234', date_opened: '2020-01-01' },
          expectedMatch: false,
          expectedConfidence: 60
        }
      ];

      testCases.forEach(({ existing, incoming, expectedMatch, expectedConfidence }) => {
        const existingTradeline = createMockTradeline(existing);
        const incomingTradeline = createMockTradeline(incoming);
        
        const result = isTradelineMatch(incomingTradeline, existingTradeline);
        
        expect(result.isMatch).toBe(expectedMatch);
        expect(result.confidence).toBe(expectedConfidence);
      });
    });

    test('should handle date format variations consistently', () => {
      const baseTradeline = createMockTradeline({
        creditor_name: 'Test Bank',
        account_number: '1234-5678-9012'
      });

      const dateFormats = [
        '2020-01-15',
        '01/15/2020',
        '1/15/2020',
        'Jan 15, 2020',
        'January 15, 2020',
        '2020-1-15'
      ];

      // All should normalize to the same date
      const normalizedDates = dateFormats.map(normalizeDate);
      const expectedDate = '2020-01-15';
      
      normalizedDates.forEach(date => {
        expect(date).toBe(expectedDate);
      });

      // All should match when used in tradelines
      dateFormats.forEach(dateFormat => {
        const tradeline1 = { ...baseTradeline, date_opened: dateFormats[0] };
        const tradeline2 = { ...baseTradeline, date_opened: dateFormat };
        
        const result = isTradelineMatch(tradeline1, tradeline2);
        expect(result.matchingCriteria.dateOpenedMatch).toBe(true);
      });
    });
  });

  describe('Field Merging Advanced Scenarios', () => {
    test('should handle complex field merging scenarios', () => {
      const existing = createMockTradeline({
        account_balance: '$1,500.00',
        credit_limit: '',
        monthly_payment: '$0',
        account_status: 'Open',
        account_type: '',
        is_negative: false,
        credit_bureau: 'Experian'
      });

      const incoming = createMockTradeline({
        account_balance: '$2,000.00', // Should not override
        credit_limit: '$5,000.00',   // Should update (empty)
        monthly_payment: '$75.00',   // Should update ($0 = empty)
        account_status: 'Closed',    // Should not override
        account_type: 'Credit Card', // Should update (empty)
        is_negative: true,           // Should update (more specific)
        credit_bureau: 'TransUnion'  // Should not override
      });

      const updates = mergeTradelineFields(existing, incoming);
      
      expect(updates).toEqual({
        credit_limit: '$5,000.00',
        monthly_payment: '$75.00',
        account_type: 'Credit Card',
        is_negative: true
      });
    });

    test('should handle all empty vs all populated scenarios', () => {
      const emptyTradeline = createMockTradeline({
        account_balance: '',
        credit_limit: '',
        monthly_payment: '',
        account_status: '',
        account_type: '',
        credit_bureau: ''
      });

      const populatedTradeline = createMockTradeline({
        account_balance: '$1,000.00',
        credit_limit: '$3,000.00',
        monthly_payment: '$50.00',
        account_status: 'Open',
        account_type: 'Credit Card',
        credit_bureau: 'Equifax'
      });

      const updates = mergeTradelineFields(emptyTradeline, populatedTradeline);
      
      // Should update all empty fields
      expect(Object.keys(updates)).toHaveLength(6);
      expect(updates.account_balance).toBe('$1,000.00');
      expect(updates.credit_limit).toBe('$3,000.00');
    });
  });
});