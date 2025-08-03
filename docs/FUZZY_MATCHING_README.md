# Fuzzy Tradeline Matching System

## Overview

The fuzzy matching system prevents duplicate tradelines by intelligently identifying when an incoming tradeline represents the same account as an existing one, even when there are slight variations in the data format.

## How It Works

### Matching Criteria

A tradeline is considered a match if **ALL THREE** criteria are met:

1. **Creditor Name Match** (40% confidence weight)
   - Case-insensitive comparison
   - Removes common suffixes (Bank, Corp, Inc, LLC, etc.)
   - Handles special characters and extra whitespace
   - Example: "CHASE BANK" matches "Chase Bank, N.A."

2. **Account Number Prefix Match** (30% confidence weight)
   - Compares first 4 digits only
   - Ignores formatting (spaces, dashes, letters)
   - Example: "1234-5678-9012" matches "1234 5678 9012 3456"

3. **Date Opened Match** (30% confidence weight)
   - Exact match after normalization
   - Handles various date formats
   - Example: "2020-01-15" matches "01/15/2020"

### Smart Field Merging

When a match is found, the system **only updates empty fields** in the existing record:

- ✅ **Preserves existing data** - Never overwrites populated fields
- ✅ **Fills gaps** - Updates empty/null/`$0` fields with new information
- ✅ **Enhances negative status** - Updates `is_negative` to `true` if incoming has more specific info

### Examples

#### Example 1: Perfect Match with Field Updates
```typescript
// Existing tradeline in database
{
  creditor_name: "Chase Bank",
  account_number: "1234-5678-9012",
  date_opened: "2020-01-15",
  account_balance: "", // Empty
  credit_limit: "$5,000" // Has value
}

// Incoming tradeline from new report
{
  creditor_name: "CHASE BANK",
  account_number: "1234 5678 9012 3456",
  date_opened: "01/15/2020",
  account_balance: "$2,500", // New info
  credit_limit: "$10,000" // Different value
}

// Result: Updates only account_balance
// credit_limit remains "$5,000" (preserves existing data)
```

#### Example 2: No Match Due to Different Account Prefix
```typescript
// Existing: account_number: "1234-5678-9012"
// Incoming: account_number: "5678-1234-9012"
// Result: No match, creates new tradeline
```

## Implementation Files

- **`src/utils/fuzzyTradelineMatching.ts`** - Core matching logic
- **`src/utils/tradelineParser.ts`** - Modified save function
- **`src/utils/__tests__/fuzzyTradelineMatching.test.ts`** - Unit tests

## Benefits

1. **Prevents Duplicates** - Avoids multiple records for the same account
2. **Data Preservation** - Never loses existing complete information
3. **Progressive Enhancement** - Gradually builds complete tradeline profiles
4. **Handles Variations** - Works with different credit report formats
5. **Maintains History** - Preserves dispute counts and other metadata

## Confidence Scoring

The system calculates a confidence score (0-100) based on matching criteria:

- **100%** - All criteria match (perfect duplicate)
- **70%** - Creditor + Date match (partial match)
- **40%** - Only creditor matches (low confidence)
- **0%** - No criteria match

Only 100% confidence matches trigger the merge process.

## Usage

The system automatically activates when saving tradelines:

```typescript
import { saveTradelinesToDatabase } from '@/utils/tradelineParser';

// Automatically uses fuzzy matching
const results = await saveTradelinesToDatabase(newTradelines, userId);
```

## Console Logging

The system provides detailed logging for debugging:

```
🔍 Processing tradeline: Chase Bank - 1234-5678-9012
✅ Found fuzzy match: confidence: 100, criteria: {creditor: true, account: true, date: true}
🔄 Will update existing tradeline abc-123 with 2 fields
📊 Tradeline processing complete: {total: 5, newInserts: 3, updates: 2}
```

## Testing

Run the comprehensive test suite:

```bash
npm test fuzzyTradelineMatching.test.ts
```

Tests cover:
- Name normalization edge cases
- Account number extraction
- Date format handling
- Matching logic scenarios
- Field merging behavior