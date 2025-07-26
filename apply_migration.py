#!/usr/bin/env python3
"""
Apply the database migration to update unique constraint for tradelines
"""

import os
from supabase import create_client

# Load environment variables
SUPABASE_URL = "https://gywohmbqohytziwsjrps.supabase.co"
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_ANON_KEY:
    print("❌ SUPABASE_ANON_KEY environment variable not set")
    exit(1)

# Initialize client
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Migration SQL
migration_sql = """
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
"""

def apply_migration():
    """Apply the migration"""
    try:
        print("🚀 Applying database migration...")
        
        # Execute migration SQL
        result = supabase.rpc('exec_sql', {'sql': migration_sql}).execute()
        
        if result.data:
            print("✅ Migration applied successfully!")
            print(f"Result: {result.data}")
        else:
            print("❌ Migration failed - no data returned")
            
    except Exception as e:
        print(f"❌ Migration failed with error: {e}")
        print("This might be because:")
        print("1. The RPC function 'exec_sql' doesn't exist")
        print("2. Insufficient permissions")
        print("3. The constraint already exists")
        print("\nYou may need to apply this migration manually in the Supabase dashboard:")
        print("\n" + migration_sql)

def check_constraints():
    """Check current constraints on tradelines table"""
    try:
        print("\n🔍 Checking current constraints...")
        
        # Query to check constraints
        constraint_query = """
        SELECT constraint_name, constraint_type 
        FROM information_schema.table_constraints 
        WHERE table_name = 'tradelines' 
        AND table_schema = 'public'
        AND constraint_type = 'UNIQUE';
        """
        
        result = supabase.rpc('exec_sql', {'sql': constraint_query}).execute()
        
        if result.data:
            print("Current unique constraints:")
            for constraint in result.data:
                print(f"  - {constraint}")
        else:
            print("❌ Could not check constraints")
            
    except Exception as e:
        print(f"❌ Error checking constraints: {e}")

if __name__ == "__main__":
    apply_migration()
    check_constraints()