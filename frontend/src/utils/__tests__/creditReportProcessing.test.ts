import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { ParsedTradelineSchema } from '../tradeline/types'; // Import the schema

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

describe('Tradeline Validation', () => {
  it('should validate a tradeline with a valid credit_bureau', () => {
    const validTradeline = {
      id: 'test-1',
      creditor_name: 'Test Bank',
      account_type: 'Credit Card',
      account_status: 'Open',
      account_balance: '$1000',
      credit_limit: '$5000',
      is_negative: false,
      account_number: '1234567890',
      date_opened: '01/01/2020',
      monthly_payment: '$50',
      credit_bureau: 'TransUnion',
      created_at: new Date().toISOString(),
    };
    expect(() => ParsedTradelineSchema.parse(validTradeline)).not.toThrow();
  });

  it('should throw error for invalid credit_bureau', () => {
    const invalidTradeline = {
      id: 'test-1',
      creditor_name: 'Test Bank',
      account_type: 'Credit Card',
      account_status: 'Open',
      account_balance: '$1000',
      credit_limit: '$5000',
      is_negative: false,
      account_number: '1234567890',
      date_opened: '01/01/2020',
      monthly_payment: '$50',
      credit_bureau: 'InvalidBureau',
      created_at: new Date().toISOString(),
    };
    expect(() => ParsedTradelineSchema.parse(invalidTradeline)).toThrow();
  });

  it('should validate account_number with numbers, x, *, or .', () => {
    const validTradeline = {
      id: 'test-1',
      creditor_name: 'Test Bank',
      account_type: 'Credit Card',
      account_status: 'Open',
      account_balance: '$1000',
      credit_limit: '$5000',
      is_negative: false,
      account_number: '1234x*5.67890',
      date_opened: '01/01/2020',
      monthly_payment: '$50',
      credit_bureau: 'TransUnion',
      created_at: new Date().toISOString(),
    };
    expect(() => ParsedTradelineSchema.parse(validTradeline)).not.toThrow();
  });

  it('should throw error for invalid account_number characters', () => {
    const invalidTradeline = {
      id: 'test-1',
      creditor_name: 'Test Bank',
      account_type: 'Credit Card',
      account_status: 'Open',
      account_balance: '$1000',
      credit_limit: '$5000',
      is_negative: false,
      account_number: '123-456',
      date_opened: '01/01/2020',
      monthly_payment: '$50',
      credit_bureau: 'TransUnion',
      created_at: new Date().toISOString(),
    };
    expect(() => ParsedTradelineSchema.parse(invalidTradeline)).toThrow();
  });

  it('should throw error for missing account_number', () => {
    const invalidTradeline = {
      id: 'test-1',
      creditor_name: 'Test Bank',
      account_type: 'Credit Card',
      account_status: 'Open',
      account_balance: '$1000',
      credit_limit: '$5000',
      is_negative: false,
      date_opened: '01/01/2020',
      monthly_payment: '$50',
      credit_bureau: 'TransUnion',
      created_at: new Date().toISOString(),
    };
    expect(() => ParsedTradelineSchema.parse(invalidTradeline)).toThrow();
  });

  it('should validate creditor_name with no special characters', () => {
    const validTradeline = {
      id: 'test-1',
      creditor_name: 'Test Bank Inc',
      account_type: 'Credit Card',
      account_status: 'Open',
      account_balance: '$1000',
      credit_limit: '$5000',
      is_negative: false,
      account_number: '1234567890',
      date_opened: '01/01/2020',
      monthly_payment: '$50',
      credit_bureau: 'TransUnion',
      created_at: new Date().toISOString(),
    };
    expect(() => ParsedTradelineSchema.parse(validTradeline)).not.toThrow();
  });

  it('should throw error for creditor_name with special characters', () => {
    const invalidTradeline = {
      id: 'test-1',
      creditor_name: 'Test Bank!',
      account_type: 'Credit Card',
      account_status: 'Open',
      account_balance: '$1000',
      credit_limit: '$5000',
      is_negative: false,
      account_number: '1234567890',
      date_opened: '01/01/2020',
      monthly_payment: '$50',
      credit_bureau: 'TransUnion',
      created_at: new Date().toISOString(),
    };
    expect(() => ParsedTradelineSchema.parse(invalidTradeline)).toThrow();
  });

  it('should validate date_opened as a valid date', () => {
    const validTradeline = {
      id: 'test-1',
      creditor_name: 'Test Bank',
      account_type: 'Credit Card',
      account_status: 'Open',
      account_balance: '$1000',
      credit_limit: '$5000',
      is_negative: false,
      account_number: '1234567890',
      date_opened: '12/25/2023',
      monthly_payment: '$50',
      credit_bureau: 'TransUnion',
      created_at: new Date().toISOString(),
    };
    expect(() => ParsedTradelineSchema.parse(validTradeline)).not.toThrow();
  });

  it('should throw error for invalid date_opened format', () => {
    const invalidTradeline = {
      id: 'test-1',
      creditor_name: 'Test Bank',
      account_type: 'Credit Card',
      account_status: 'Open',
      account_balance: '$1000',
      credit_limit: '$5000',
      is_negative: false,
      account_number: '1234567890',
      date_opened: '2023-12-25', // Invalid format
      monthly_payment: '$50',
      credit_bureau: 'TransUnion',
      created_at: new Date().toISOString(),
    };
    expect(() => ParsedTradelineSchema.parse(invalidTradeline)).toThrow();
  });

  it('should validate account_balance as a financial amount $XX', () => {
    const validTradeline = {
      id: 'test-1',
      creditor_name: 'Test Bank',
      account_type: 'Credit Card',
      account_status: 'Open',
      account_balance: '$12345',
      credit_limit: '$5000',
      is_negative: false,
      account_number: '1234567890',
      date_opened: '01/01/2020',
      monthly_payment: '$50',
      credit_bureau: 'TransUnion',
      created_at: new Date().toISOString(),
    };
    expect(() => ParsedTradelineSchema.parse(validTradeline)).not.toThrow();
  });

  it('should throw error for invalid account_balance format', () => {
    const invalidTradeline = {
      id: 'test-1',
      creditor_name: 'Test Bank',
      account_type: 'Credit Card',
      account_status: 'Open',
      account_balance: '$1,000.50', // Invalid format
      credit_limit: '$5000',
      is_negative: false,
      account_number: '1234567890',
      date_opened: '01/01/2020',
      monthly_payment: '$50',
      credit_bureau: 'TransUnion',
      created_at: new Date().toISOString(),
    };
    expect(() => ParsedTradelineSchema.parse(invalidTradeline)).toThrow();
  });

  it('should validate monthly_payment as a financial amount $XX', () => {
    const validTradeline = {
      id: 'test-1',
      creditor_name: 'Test Bank',
      account_type: 'Credit Card',
      account_status: 'Open',
      account_balance: '$1000',
      credit_limit: '$5000',
      is_negative: false,
      account_number: '1234567890',
      date_opened: '01/01/2020',
      monthly_payment: '$50',
      credit_bureau: 'TransUnion',
      created_at: new Date().toISOString(),
    };
    expect(() => ParsedTradelineSchema.parse(validTradeline)).not.toThrow();
  });

  it('should throw error for invalid monthly_payment format', () => {
    const invalidTradeline = {
      id: 'test-1',
      creditor_name: 'Test Bank',
      account_type: 'Credit Card',
      account_status: 'Open',
      account_balance: '$1000',
      credit_limit: '$5000',
      is_negative: false,
      account_number: '1234567890',
      date_opened: '01/01/2020',
      monthly_payment: '$50.25', // Invalid format
      credit_bureau: 'TransUnion',
      created_at: new Date().toISOString(),
    };
    expect(() => ParsedTradelineSchema.parse(invalidTradeline)).toThrow();
  });

  it('should validate credit_limit as a financial amount $XX', () => {
    const validTradeline = {
      id: 'test-1',
      creditor_name: 'Test Bank',
      account_type: 'Credit Card',
      account_status: 'Open',
      account_balance: '$1000',
      credit_limit: '$5000',
      is_negative: false,
      account_number: '1234567890',
      date_opened: '01/01/2020',
      monthly_payment: '$50',
      credit_bureau: 'TransUnion',
      created_at: new Date().toISOString(),
    };
    expect(() => ParsedTradelineSchema.parse(validTradeline)).not.toThrow();
  });

  it('should throw error for invalid credit_limit format', () => {
    const invalidTradeline = {
      id: 'test-1',
      creditor_name: 'Test Bank',
      account_type: 'Credit Card',
      account_status: 'Open',
      account_balance: '$1000',
      credit_limit: '$5,000.75', // Invalid format
      is_negative: false,
      account_number: '1234567890',
      date_opened: '01/01/2020',
      monthly_payment: '$50',
      credit_bureau: 'TransUnion',
      created_at: new Date().toISOString(),
    };
    expect(() => ParsedTradelineSchema.parse(invalidTradeline)).toThrow();
  });
});