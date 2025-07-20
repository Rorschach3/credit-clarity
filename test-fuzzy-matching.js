// Simple Node.js script to test fuzzy matching functions
// Run with: node test-fuzzy-matching.js

// Mock the import paths since this is running outside Jest
const path = require('path');

// Simple test functions
function normalizeCreditorName(name) {
  if (!name) return '';
  
  return name
    .trim()
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .replace(/[^\w\s]/g, '')
    .replace(/\b(bank|credit|card|company|corp|inc|llc)\b/g, '')
    .trim();
}

function extractAccountPrefix(accountNumber) {
  if (!accountNumber) return '';
  
  const digits = accountNumber.replace(/\D/g, '');
  return digits.substring(0, 4);
}

function normalizeDate(dateStr) {
  if (!dateStr) return '';
  
  try {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return '';
    
    return date.toISOString().split('T')[0];
  } catch {
    return '';
  }
}

// Test runner
function runTests() {
  console.log('🧪 Running Fuzzy Matching Tests...\n');
  
  let passed = 0;
  let failed = 0;
  
  function test(description, testFn) {
    try {
      testFn();
      console.log(`✅ ${description}`);
      passed++;
    } catch (error) {
      console.log(`❌ ${description}`);
      console.log(`   Error: ${error.message}`);
      failed++;
    }
  }
  
  function expect(actual) {
    return {
      toBe(expected) {
        if (actual !== expected) {
          throw new Error(`Expected "${expected}" but got "${actual}"`);
        }
      }
    };
  }
  
  // Creditor Name Tests
  console.log('📋 Testing normalizeCreditorName...');
  test('should normalize CHASE BANK to chase', () => {
    expect(normalizeCreditorName('CHASE BANK')).toBe('chase');
  });
  
  test('should normalize Chase Bank to chase', () => {
    expect(normalizeCreditorName('Chase Bank')).toBe('chase');
  });
  
  test('should handle extra spaces', () => {
    expect(normalizeCreditorName('  Chase   Bank  ')).toBe('chase');
  });
  
  test('should remove common suffixes', () => {
    expect(normalizeCreditorName('Chase Bank, N.A.')).toBe('chase');
  });
  
  test('should handle Bank of America Corp', () => {
    expect(normalizeCreditorName('Bank of America Corp')).toBe('of america');
  });
  
  test('should handle Wells Fargo & Company', () => {
    expect(normalizeCreditorName('Wells Fargo & Company')).toBe('wells fargo');
  });
  
  // Account Prefix Tests
  console.log('\n💳 Testing extractAccountPrefix...');
  test('should extract 1234 from 1234-5678-9012', () => {
    expect(extractAccountPrefix('1234-5678-9012')).toBe('1234');
  });
  
  test('should extract 1234 from 1234 5678 9012', () => {
    expect(extractAccountPrefix('1234 5678 9012')).toBe('1234');
  });
  
  test('should extract 1234 from 1234567890123456', () => {
    expect(extractAccountPrefix('1234567890123456')).toBe('1234');
  });
  
  test('should extract 1234 from xxxx-xxxx-xxxx-1234', () => {
    expect(extractAccountPrefix('xxxx-xxxx-xxxx-1234')).toBe('1234');
  });
  
  test('should handle empty string', () => {
    expect(extractAccountPrefix('')).toBe('');
  });
  
  test('should handle no digits', () => {
    expect(extractAccountPrefix('ABCD-EFGH-IJKL')).toBe('');
  });
  
  // Date Normalization Tests
  console.log('\n📅 Testing normalizeDate...');
  test('should keep 2020-01-15 as 2020-01-15', () => {
    expect(normalizeDate('2020-01-15')).toBe('2020-01-15');
  });
  
  test('should convert 01/15/2020 to 2020-01-15', () => {
    expect(normalizeDate('01/15/2020')).toBe('2020-01-15');
  });
  
  test('should handle empty string', () => {
    expect(normalizeDate('')).toBe('');
  });
  
  test('should handle invalid date', () => {
    expect(normalizeDate('not-a-date')).toBe('');
  });
  
  // Real-world Scenarios
  console.log('\n🌍 Testing Real-world Scenarios...');
  test('should match Chase variations', () => {
    const name1 = normalizeCreditorName('CHASE BANK USA, N.A.');
    const name2 = normalizeCreditorName('Chase Bank');
    expect(name1).toBe(name2);
  });
  
  test('should match account number variations', () => {
    const acc1 = extractAccountPrefix('4532-1234-5678-9012');
    const acc2 = extractAccountPrefix('4532 **** **** 9012');
    expect(acc1).toBe(acc2);
  });
  
  test('should match date variations', () => {
    const date1 = normalizeDate('2020-03-15');
    const date2 = normalizeDate('03/15/2020');
    expect(date1).toBe(date2);
  });
  
  console.log(`\n📊 Test Results: ${passed} passed, ${failed} failed`);
  
  if (failed === 0) {
    console.log('🎉 All tests passed! Fuzzy matching logic is working correctly.');
  } else {
    console.log('⚠️  Some tests failed. Please check the implementation.');
  }
}

// Run the tests
runTests();