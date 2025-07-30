import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { 
  generateDisputeLetters, 
  generateDisputeLetterContent, 
  getDisputeReasons,
  CREDIT_BUREAU_ADDRESSES 
} from '../disputeUtils';
import { ParsedTradeline } from '../tradelineParser';

// Mock jsPDF
jest.mock('jspdf', () => {
  return jest.fn().mockImplementation(() => ({
    internal: {
      pageSize: { height: 792, width: 612 },
    },
    setFontSize: jest.fn(),
    setFont: jest.fn(),
    text: jest.fn(),
    addPage: jest.fn(),
    splitTextToSize: jest.fn((text) => text.split('\n')),
    output: jest.fn(() => new Blob(['mock-pdf'], { type: 'application/pdf' })),
  }));
});

// Mock pdf-lib
jest.mock('pdf-lib', () => ({
  PDFDocument: {
    create: jest.fn(() => ({
      addPage: jest.fn(() => ({
        getSize: jest.fn(() => ({ width: 612, height: 792 })),
        drawText: jest.fn(),
      })),
      save: jest.fn(() => new Uint8Array([1, 2, 3])),
    })),
  },
  rgb: jest.fn(() => ({ r: 0, g: 0, b: 0 })),
}));

describe('Dispute Utils', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('CREDIT_BUREAU_ADDRESSES', () => {
    it('should contain all major credit bureaus', () => {
      expect(CREDIT_BUREAU_ADDRESSES).toHaveProperty('Experian');
      expect(CREDIT_BUREAU_ADDRESSES).toHaveProperty('Equifax');
      expect(CREDIT_BUREAU_ADDRESSES).toHaveProperty('TransUnion');
    });

    it('should have complete address information', () => {
      const experian = CREDIT_BUREAU_ADDRESSES.Experian;
      expect(experian).toHaveProperty('name');
      expect(experian).toHaveProperty('address');
      expect(experian).toHaveProperty('city');
      expect(experian).toHaveProperty('state');
      expect(experian).toHaveProperty('zip');
    });
  });

  describe('getDisputeReasons', () => {
    it('should return default reasons for complete tradeline', () => {
      const tradeline: ParsedTradeline = {
        id: 'test-1',
        creditor_name: 'Test Bank',
        account_number: '1234567890',
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

      const reasons = getDisputeReasons(tradeline);
      expect(reasons).toContain('This account does not belong to me');
      expect(reasons).toContain('The information reported is inaccurate');
    });

    it('should return specific reasons for missing account number', () => {
      const tradeline: ParsedTradeline = {
        id: 'test-1',
        creditor_name: 'Test Bank',
        account_number: '',
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

      const reasons = getDisputeReasons(tradeline);
      expect(reasons).toContain('Account number is missing or incomplete');
    });

    it('should return specific reasons for missing date opened', () => {
      const tradeline: ParsedTradeline = {
        id: 'test-1',
        creditor_name: 'Test Bank',
        account_number: '1234567890',
        date_opened: '',
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

      const reasons = getDisputeReasons(tradeline);
      expect(reasons).toContain('Date opened is inaccurate or missing');
    });

    it('should return specific reasons for missing account status', () => {
      const tradeline: ParsedTradeline = {
        id: 'test-1',
        creditor_name: 'Test Bank',
        account_number: '1234567890',
        date_opened: '01/01/2020',
        account_status: '',
        account_type: 'Credit Card',
        account_balance: '$1,000',
        credit_limit: '$5,000',
        monthly_payment: '$100',
        credit_bureau: 'Experian',
        is_negative: false,
        dispute_count: 0,
        user_id: 'user-123',
      };

      const reasons = getDisputeReasons(tradeline);
      expect(reasons).toContain('Account status is inaccurate');
    });
  });

  describe('generateDisputeLetterContent', () => {
    const mockProfile = {
      firstName: 'John',
      lastName: 'Doe',
      address: '123 Main St',
      city: 'Anytown',
      state: 'CA',
      zipCode: '12345',
      dateOfBirth: '01/01/1990',
      ssn: '123456789',
    };

    const mockTradelines: ParsedTradeline[] = [
      {
        id: 'test-1',
        creditor_name: 'Test Bank',
        account_number: '1234567890',
        date_opened: '01/01/2020',
        account_status: 'Open',
        account_type: 'Credit Card',
        account_balance: '$1,000',
        credit_limit: '$5,000',
        monthly_payment: '$100',
        credit_bureau: 'Experian',
        is_negative: true,
        dispute_count: 0,
        user_id: 'user-123',
      },
    ];

    it('should generate complete dispute letter content', () => {
      const content = generateDisputeLetterContent(mockTradelines, 'Experian', mockProfile);
      
      expect(content).toContain('John Doe');
      expect(content).toContain('123 Main St');
      expect(content).toContain('Anytown, CA 12345');
      expect(content).toContain('Experian');
      expect(content).toContain('Test Bank');
      expect(content).toContain('Fair Credit Reporting Act');
      expect(content).toContain('Request for Investigation');
    });

    it('should mask SSN in letter content', () => {
      const content = generateDisputeLetterContent(mockTradelines, 'Experian', mockProfile);
      
      expect(content).toContain('***-**-6789');
      expect(content).not.toContain('123456789');
    });

    it('should mask account number in letter content', () => {
      const content = generateDisputeLetterContent(mockTradelines, 'Experian', mockProfile);
      
      expect(content).toContain('****7890');
      expect(content).not.toContain('1234567890');
    });

    it('should include bureau address information', () => {
      const content = generateDisputeLetterContent(mockTradelines, 'Experian', mockProfile);
      
      expect(content).toContain('P.O. Box 4000');
      expect(content).toContain('Allen, TX 75013');
    });

    it('should include account table with tradeline information', () => {
      const content = generateDisputeLetterContent(mockTradelines, 'Experian', mockProfile);
      
      expect(content).toContain('Creditor Name | Account Number | Date Opened | Dispute Reason');
      expect(content).toContain('Test Bank | ****7890 | 01/01/2020 | Inaccurate Information');
    });
  });

  describe('generateDisputeLetters', () => {
    const mockProfile = {
      firstName: 'John',
      lastName: 'Doe',
      address: '123 Main St',
      city: 'Anytown',
      state: 'CA',
      zipCode: '12345',
      dateOfBirth: '01/01/1990',
      ssn: '123456789',
    };

    const mockTradelines: ParsedTradeline[] = [
      {
        id: 'test-1',
        creditor_name: 'Test Bank',
        account_number: '1234567890',
        date_opened: '01/01/2020',
        account_status: 'Open',
        account_type: 'Credit Card',
        account_balance: '$1,000',
        credit_limit: '$5,000',
        monthly_payment: '$100',
        credit_bureau: 'Experian',
        is_negative: true,
        dispute_count: 0,
        user_id: 'user-123',
      },
      {
        id: 'test-2',
        creditor_name: 'Another Bank',
        account_number: '9876543210',
        date_opened: '01/01/2019',
        account_status: 'Closed',
        account_type: 'Credit Card',
        account_balance: '$0',
        credit_limit: '$2,000',
        monthly_payment: '$0',
        credit_bureau: 'Equifax',
        is_negative: true,
        dispute_count: 0,
        user_id: 'user-123',
      },
    ];

    it('should generate letters grouped by credit bureau', async () => {
      const mockUpdateProgress = jest.fn();
      const selectedTradelines = ['test-1', 'test-2'];

      const letters = await generateDisputeLetters(
        selectedTradelines,
        mockTradelines,
        mockProfile,
        mockUpdateProgress
      );

      expect(letters).toHaveLength(2); // One for each bureau
      expect(letters[0].creditBureau).toBe('Experian');
      expect(letters[1].creditBureau).toBe('Equifax');
      expect(mockUpdateProgress).toHaveBeenCalledWith(
        expect.objectContaining({
          step: expect.any(String),
          progress: expect.any(Number),
          message: expect.any(String),
        })
      );
    });

    it('should include correct tradeline count in each letter', async () => {
      const mockUpdateProgress = jest.fn();
      const selectedTradelines = ['test-1', 'test-2'];

      const letters = await generateDisputeLetters(
        selectedTradelines,
        mockTradelines,
        mockProfile,
        mockUpdateProgress
      );

      const experianLetter = letters.find(l => l.creditBureau === 'Experian');
      const equifaxLetter = letters.find(l => l.creditBureau === 'Equifax');

      expect(experianLetter?.disputeCount).toBe(1);
      expect(equifaxLetter?.disputeCount).toBe(1);
    });

    it('should handle empty tradeline selection', async () => {
      const mockUpdateProgress = jest.fn();
      const selectedTradelines: string[] = [];

      const letters = await generateDisputeLetters(
        selectedTradelines,
        mockTradelines,
        mockProfile,
        mockUpdateProgress
      );

      expect(letters).toHaveLength(0);
    });

    it('should handle tradelines without credit bureau', async () => {
      const mockUpdateProgress = jest.fn();
      const tradelinesWithoutBureau: ParsedTradeline[] = [
        {
          id: 'test-1',
          creditor_name: 'Test Bank',
          account_number: '1234567890',
          date_opened: '01/01/2020',
          account_status: 'Open',
          account_type: 'Credit Card',
          account_balance: '$1,000',
          credit_limit: '$5,000',
          monthly_payment: '$100',
          credit_bureau: '', // No bureau specified
          is_negative: true,
          dispute_count: 0,
          user_id: 'user-123',
        },
      ];

      const letters = await generateDisputeLetters(
        ['test-1'],
        tradelinesWithoutBureau,
        mockProfile,
        mockUpdateProgress
      );

      expect(letters).toHaveLength(0);
    });
  });
});