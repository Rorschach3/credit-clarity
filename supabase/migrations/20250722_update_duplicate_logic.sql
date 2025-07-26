-- Update tradeline unique constraints for new duplicate detection logic
-- Date: 2025-07-22
-- Purpose: Change duplicate detection from full account match to first 4 digits + date + bureau

-- Drop the current unique constraint
DROP INDEX IF EXISTS unique_tradeline_per_user_bureau;

-- Drop the current index
DROP INDEX IF EXISTS idx_tradelines_user_creditor_bureau;

-- Add a function to get first 4 digits of account number
CREATE OR REPLACE FUNCTION get_account_first_4(account_number TEXT)
RETURNS TEXT AS $$
BEGIN
  -- Remove any non-alphanumeric characters and get first 4 characters
  RETURN LEFT(REGEXP_REPLACE(COALESCE(account_number, ''), '[^A-Za-z0-9]', '', 'g'), 4);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create a new unique constraint based on the new criteria:
-- user_id, creditor_name, first_4_digits_of_account_number, date_opened, credit_bureau
CREATE UNIQUE INDEX unique_tradeline_per_bureau_detailed
ON tradelines (
  user_id, 
  creditor_name, 
  get_account_first_4(account_number), 
  date_opened, 
  credit_bureau
) 
WHERE user_id IS NOT NULL 
  AND creditor_name IS NOT NULL 
  AND creditor_name != '' 
  AND credit_bureau IS NOT NULL 
  AND credit_bureau != ''
  AND date_opened IS NOT NULL 
  AND date_opened != '';

-- Create an index for better query performance on the new criteria
CREATE INDEX idx_tradelines_duplicate_check 
ON tradelines (
  user_id, 
  creditor_name, 
  get_account_first_4(account_number), 
  date_opened, 
  credit_bureau
);

-- Create an index for account number prefix lookups
CREATE INDEX idx_tradelines_account_prefix 
ON tradelines USING btree (user_id, get_account_first_4(account_number));

-- Add a comment explaining the new logic
COMMENT ON INDEX unique_tradeline_per_bureau_detailed IS 
'Ensures one tradeline per user per credit bureau based on: creditor_name, first 4 digits of account_number, and date_opened';

COMMENT ON FUNCTION get_account_first_4(TEXT) IS 
'Extracts first 4 alphanumeric characters from account number for duplicate detection';