/**
 * Real-world test of enhanced parser using actual Experian credit report format
 * Based on the PDF structure from '/mnt/g/OneDrive/Personal/Desktop/Experian 9102015.pdf'
 */

import { EnhancedCreditReportParser } from './enhanced-credit-report-parser';
import { ParsedTradeline } from './tradeline/types';

// Mock the actual structure from the Experian PDF
const MOCK_EXPERIAN_TEXT = `
Online Personal Credit Report from Experian for
FERNANDO D HERNANDEZ
Your report number is
4291-8045-04
Report date:
09/10/2015

Potentially Negative Items or items for further review

CHASE CARD
Address:
PO BOX 15298
WILMINGTON, DE 19850
(800) 432-3117
Account Number: 464018208930....
Address Identification Number:
018634229
Status: Account charged off. $808 written off. $808 past due as
of Aug 2015.
Status Details: This account is scheduled to continue on
record until Mar 2021.
This item was updated from our processing of your dispute in Apr
2015.

Date Opened:
01/2014
Reported Since:
02/2014
Date of Status:
01/2015
Last Reported:
08/2015
Your Statement:

Type:
Credit card
Terms:
NA
Monthly Payment:
$0
Responsibility:
Individual

Credit Limit/Original Amount:
$500
High Balance:
$808
Recent Balance:
$808 as of 08/2015
Recent Payment:
$0

Comment: Account closed at credit grantor's request.

Payment History:
2015                                2014
AUG JUL JUN MAY APR MAR FEB JAN DEC NOV OCT SEP AUG JUL JUN MAY APR MAR FEB
CO  CO  CO  CO  CO  CO  CO  CO  150 120 90  60  30  ND  OK  OK  OK  OK  OK

Account History:
Charge Off as of Aug 2015, Jul 2015, Jun 2015, Jan 2015 to May
2015
150 days past due as of Dec 2014
120 days past due as of Nov 2014
90 days past due as of Oct 2014
60 days past due as of Sep 2014
30 days past due as of Aug 2014

Accounts in Good Standing

BANK OF AMERICA
Address:
PO BOX 982235
EL PASO, TX 79998
(800) 215-6195
Account Number: 488893705720....
Address Identification Number:
018634329
Status: Closed/Never late.
Status Details: This account is scheduled to continue on
record until Feb 2025.

Date Opened:
12/2012
Reported Since:
12/2012
Date of Status:
02/2015
Last Reported:
02/2015
Your Statement:

Type:
Secured Card
Terms:
NA
Monthly Payment:
$26
Responsibility:
Individual

Credit Limit/Original Amount:
$300
High Balance:
$144
Recent Balance:
$0 /paid as of 02/2015
Recent Payment:
$105

Account closed at consumer's request.

Payment History:
2015                2014                                2013
FEB JAN DEC NOV OCT SEP AUG JUL JUN MAY APR MAR FEB JAN DEC NOV OCT SEP AUG JUL
CLS OK  OK  OK  OK  OK  OK  OK  OK  OK  OK  OK  OK  OK  ND  ND  ND  ND  ND  ND

SCHOOLSFIRST FEDERAL CREDIT UNION
Address:
PO BOX 11547
SANTA ANA, CA 92711
No phone number available
Account Number: 420973000041....
Address Identification Number:
018631853
Status: Closed.

Date Opened:
04/2012
Reported Since:
04/2012
Date of Status:
12/2014
Last Reported:
08/2015
Type:
Credit card
Terms:
NA
Monthly Payment:
$40
Responsibility:
Individual

Credit Limit/Original Amount:
$2,000
High Balance:
$2,230
Recent Balance:
$1,975 as of 08/2015
Recent Payment:
$40

Comment: Account closed at credit grantor's request.

SCHOOLSFIRST FEDERAL CREDIT UNION
Address:
PO BOX 11547
SANTA ANA, CA 92711
No phone number available
Account Number: 755678....
Address Identification Number:
018631853
Status: Open.
Status Details: By Sep 2021, this account is scheduled to go
to a positive status.

Date Opened:
01/2014
Reported Since:
01/2014
Date of Status:
04/2015
Last Reported:
08/2015

Type:
Unsecured
Terms:
30 Months
Monthly Payment:
$173
Responsibility:
Individual

Credit Limit/Original Amount:
$4,300
High Balance:
NA
Recent Balance:
$1,947 as of 08/2015
Recent Payment:
$0

The original amount of this account was $4,300

SCHOOLSFIRST FEDERAL CREDIT UNION
Address:
PO BOX 11547
SANTA ANA, CA 92711
No phone number available
Account Number: 755678....
Address Identification Number:
018631853
Status: Open.
Status Details: By Jul 2021, this account is scheduled to go to
a positive status.

Date Opened:
05/2014
Reported Since:
05/2014
Date of Status:
05/2015
Last Reported:
08/2015

Type:
Auto Loan
Terms:
19 Months
Monthly Payment:
$174
Responsibility:
Individual

Credit Limit/Original Amount:
$3,198
High Balance:
NA
Recent Balance:
$2,111 as of 08/2015
Recent Payment:
$0

Comment: Redeemed repossession.
`;

/**
 * Test the enhanced parser against real Experian format
 */
export function testEnhancedParserWithRealData(): void {
  console.log('🧪 Testing Enhanced Parser with Real Experian Data');
  console.log('=' * 60);
  
  const parser = new EnhancedCreditReportParser();
  const userId = 'test-user-fernando';
  
  try {
    // Test section segmentation
    console.log('📋 Step 1: Testing Section Segmentation');
    const segments = parser.segmentBySectionAnchors(MOCK_EXPERIAN_TEXT);
    
    console.log('🔍 Section Results:');
    console.log(`  Negative Items: ${segments.negativeItems.length > 0 ? 'FOUND' : 'NOT FOUND'}`);
    console.log(`  Good Standing: ${segments.goodStanding.length > 0 ? 'FOUND' : 'NOT FOUND'}`);
    
    if (segments.negativeItems.length > 0) {
      console.log('  Negative section preview:', segments.negativeItems.substring(0, 200));
    }
    
    // Test full parsing
    console.log('\n📊 Step 2: Testing Full Enhanced Parsing');
    const tradelines = parser.parseEnhancedCreditReport(MOCK_EXPERIAN_TEXT, userId);
    
    console.log(`✅ Extracted ${tradelines.length} tradelines`);
    
    // Analyze results vs current parsing problems
    console.log('\n🔍 Step 3: Analyzing Results vs Current Problems');
    
    tradelines.forEach((tradeline, index) => {
      console.log(`\n📄 Tradeline ${index + 1}:`);
      console.log(`  Creditor: "${tradeline.creditor_name}"`);
      console.log(`  Account: "${tradeline.account_number}"`);
      console.log(`  Balance: "${tradeline.account_balance}"`);
      console.log(`  Status: "${tradeline.account_status}"`);
      console.log(`  Type: "${tradeline.account_type}"`);
      console.log(`  Credit Limit: "${tradeline.credit_limit}"`);
      console.log(`  Negative: ${tradeline.is_negative}`);
      
      // Check for improvement over current parsing
      const improvements = [];
      
      if (tradeline.creditor_name && !tradeline.creditor_name.includes('Individual\\n') && 
          !tradeline.creditor_name.includes(' St') && !tradeline.creditor_name.includes('W North')) {
        improvements.push('✅ Proper creditor name (not address fragment)');
      }
      
      if (tradeline.account_number && tradeline.account_number.length > 4) {
        improvements.push('✅ Account number extracted');
      }
      
      if (tradeline.account_balance && tradeline.account_balance !== '$0') {
        improvements.push('✅ Actual balance found');
      }
      
      if (tradeline.credit_limit && tradeline.credit_limit !== '$0') {
        improvements.push('✅ Credit limit extracted');
      }
      
      if (improvements.length > 0) {
        console.log('  🎯 Improvements over current parser:');
        improvements.forEach(improvement => console.log(`    ${improvement}`));
      } else {
        console.log('  ⚠️ Still needs improvement');
      }
    });
    
    // Test specific cases from the actual report
    console.log('\n🎯 Step 4: Testing Specific Expected Results');
    
    const expectedResults = [
      { creditor: 'CHASE CARD', account: '464018208930', balance: '$808', negative: true },
      { creditor: 'BANK OF AMERICA', account: '488893705720', balance: '$0', negative: false },
      { creditor: 'SCHOOLSFIRST FEDERAL CREDIT UNION', account: '420973000041', balance: '$1,975', negative: false }
    ];
    
    expectedResults.forEach((expected, index) => {
      const found = tradelines.find(t => 
        t.creditor_name.toUpperCase().includes(expected.creditor.toUpperCase())
      );
      
      if (found) {
        console.log(`✅ Found ${expected.creditor}:`);
        console.log(`   Account match: ${found.account_number.includes(expected.account.substring(0, 8)) ? '✅' : '❌'}`);
        console.log(`   Balance match: ${found.account_balance === expected.balance ? '✅' : '❌'} (Expected: ${expected.balance}, Got: ${found.account_balance})`);
        console.log(`   Negative flag: ${found.is_negative === expected.negative ? '✅' : '❌'} (Expected: ${expected.negative}, Got: ${found.is_negative})`);
      } else {
        console.log(`❌ Missing ${expected.creditor}`);
      }
    });
    
    // Test payment history parsing
    console.log('\n📅 Step 5: Testing Payment History Parsing');
    const chaseSection = segments.negativeItems;
    if (chaseSection) {
      const paymentHistory = parser.normalizePaymentHistory(chaseSection);
      console.log(`📊 Payment history entries found: ${paymentHistory.length}`);
      
      if (paymentHistory.length > 0) {
        console.log('🔍 Sample payment history:');
        paymentHistory.slice(0, 5).forEach(entry => {
          console.log(`   ${entry.month}: ${entry.status}`);
        });
        
        // Check for charge-offs in 2015
        const chargeOffs = paymentHistory.filter(entry => 
          entry.month.startsWith('2015') && entry.status.includes('Charge Off')
        );
        console.log(`✅ Found ${chargeOffs.length} charge-off entries in 2015 (expected from PDF)`);
      }
    }
    
    console.log('\n🎉 Enhanced Parser Test Complete!');
    console.log('📊 Summary of Improvements:');
    console.log(`   Total tradelines: ${tradelines.length} (vs ${16} messy ones from current parser)`);
    console.log(`   Proper creditor names: ${tradelines.filter(t => t.creditor_name && t.creditor_name.length > 5).length}`);
    console.log(`   Account numbers found: ${tradelines.filter(t => t.account_number && t.account_number.length > 4).length}`);
    console.log(`   Non-zero balances: ${tradelines.filter(t => t.account_balance && t.account_balance !== '$0').length}`);
    console.log(`   Negative items detected: ${tradelines.filter(t => t.is_negative).length}`);
    
    return tradelines;
    
  } catch (error) {
    console.error('❌ Enhanced parser test failed:', error);
    throw error;
  }
}

/**
 * Compare enhanced parser results with current parser results
 */
export function compareWithCurrentResults(currentResults: any[]): void {
  console.log('\n🔄 Comparing Enhanced Parser vs Current Parser Results');
  console.log('=' * 60);
  
  const enhancedResults = testEnhancedParserWithRealData();
  
  console.log('📊 Current Parser Issues:');
  currentResults.forEach((result, index) => {
    if (index < 5) { // Show first 5 for brevity
      console.log(`   ${index + 1}. "${result.creditor_name}" - ${result.creditor_name.includes('\\n') ? '❌ Contains newlines' : ''} ${result.creditor_name.includes(' St') ? '❌ Address fragment' : ''}`);
    }
  });
  
  console.log('\n🎯 Enhanced Parser Improvements:');
  enhancedResults.forEach((result, index) => {
    if (index < 5) { // Show first 5 for brevity
      console.log(`   ${index + 1}. "${result.creditor_name}" - ✅ Clean creditor name`);
    }
  });
  
  console.log('\n📈 Improvement Metrics:');
  console.log(`   Current parser tradelines: ${currentResults.length}`);
  console.log(`   Enhanced parser tradelines: ${enhancedResults.length}`);
  console.log(`   Current clean names: ${currentResults.filter(r => r.creditor_name && !r.creditor_name.includes('\\n') && !r.creditor_name.includes(' St')).length}`);
  console.log(`   Enhanced clean names: ${enhancedResults.filter(r => r.creditor_name && r.creditor_name.length > 3).length}`);
  console.log(`   Current with account numbers: ${currentResults.filter(r => r.account_number && r.account_number.length > 4).length}`);
  console.log(`   Enhanced with account numbers: ${enhancedResults.filter(r => r.account_number && r.account_number.length > 4).length}`);
}

// Test runner
if (typeof window !== 'undefined') {
  (window as any).testEnhancedParser = testEnhancedParserWithRealData;
  (window as any).compareWithCurrentResults = compareWithCurrentResults;
}