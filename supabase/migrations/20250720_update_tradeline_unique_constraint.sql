-- Update unique constraint to allow same tradelines from different credit bureaus
-- This allows up to 3 instances of the same account (one per bureau: Equifax, Experian, TransUnion)

-- Drop the existing unique constraint
ALTER TABLE public.tradelines 
DROP CONSTRAINT IF EXISTS unique_tradeline_per_user;

-- Add new constraint that includes credit_bureau
ALTER TABLE public.tradelines 
ADD CONSTRAINT unique_tradeline_per_user_bureau 
UNIQUE (user_id, account_number, creditor_name, credit_bureau);

-- Create an index for better query performance
CREATE INDEX IF NOT EXISTS idx_tradelines_user_creditor_bureau 
ON public.tradelines (user_id, creditor_name, credit_bureau);