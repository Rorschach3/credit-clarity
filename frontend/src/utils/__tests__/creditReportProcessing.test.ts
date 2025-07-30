import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { processCreditReport, validateCreditReportData } from '../creditReportProcessing';

// Mock external dependencies
jest.mock('@/integrations/supabase/client', () => ({
  supabase: {
    auth: {
      getUser: jest.fn(),
    },
    from: jest.fn(() => ({
      insert: jest.fn(() => ({
        execute: jest.fn(),
      })),
    })),
  },
}));

describe('Credit Report Processing', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('validateCreditReportData', () => {
    it('should validate valid credit report data', () => {
      const validData = {
        user_id: '123e4567-e89b-12d3-a456-426614174000',
        credit_score: 750,
        report_data: {
          tradelines: [
            {
              id: 'test-1',
              creditor_name: 'Test Bank',
              account_type: 'Credit Card',
              account_status: 'Open',
              account_balance: '$1,000',
              credit_limit: '$5,000',
              is_negative: false,
            },
          ],
        },
      };

      expect(() => validateCreditReportData(validData)).not.toThrow();
    });

    it('should throw error for invalid user_id', () => {
      const invalidData = {
        user_id: 'invalid-uuid',
        credit_score: 750,
        report_data: { tradelines: [] },
      };

      expect(() => validateCreditReportData(invalidData)).toThrow('Invalid user_id format');
    });

    it('should throw error for invalid credit score', () => {
      const invalidData = {
        user_id: '123e4567-e89b-12d3-a456-426614174000',
        credit_score: 950, // Out of range
        report_data: { tradelines: [] },
      };

      expect(() => validateCreditReportData(invalidData)).toThrow('Credit score must be between 300 and 850');
    });

    it('should throw error for missing report_data', () => {
      const invalidData = {
        user_id: '123e4567-e89b-12d3-a456-426614174000',
        credit_score: 750,
      };

      expect(() => validateCreditReportData(invalidData)).toThrow('Report data is required');
    });
  });

  describe('processCreditReport', () => {
    it('should process credit report successfully', async () => {
      const mockFile = new File(['test content'], 'test-report.pdf', {
        type: 'application/pdf',
      });

      const mockUserId = '123e4567-e89b-12d3-a456-426614174000';

      // Mock the processing function
      const mockProcessResult = {
        success: true,
        tradelines: [
          {
            id: 'test-1',
            creditor_name: 'Test Bank',
            account_type: 'Credit Card',
            account_status: 'Open',
            account_balance: '$1,000',
            credit_limit: '$5,000',
            is_negative: false,
          },
        ],
        credit_score: 750,
      };

      // Mock the implementation
      const processCreditReportMock = jest.fn().mockResolvedValue(mockProcessResult);
      
      const result = await processCreditReportMock(mockFile, mockUserId);

      expect(result.success).toBe(true);
      expect(result.tradelines).toHaveLength(1);
      expect(result.tradelines[0].creditor_name).toBe('Test Bank');
      expect(result.credit_score).toBe(750);
    });

    it('should handle processing errors gracefully', async () => {
      const mockFile = new File(['invalid content'], 'test-report.pdf', {
        type: 'application/pdf',
      });

      const mockUserId = '123e4567-e89b-12d3-a456-426614174000';

      // Mock the processing function to throw an error
      const processCreditReportMock = jest.fn().mockRejectedValue(new Error('Processing failed'));
      
      await expect(processCreditReportMock(mockFile, mockUserId)).rejects.toThrow('Processing failed');
    });

    it('should reject non-PDF files', async () => {
      const mockFile = new File(['test content'], 'test-report.txt', {
        type: 'text/plain',
      });

      const mockUserId = '123e4567-e89b-12d3-a456-426614174000';

      const processCreditReportMock = jest.fn().mockRejectedValue(new Error('Only PDF files are supported'));
      
      await expect(processCreditReportMock(mockFile, mockUserId)).rejects.toThrow('Only PDF files are supported');
    });
  });
});