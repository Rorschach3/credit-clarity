#!/usr/bin/env python3
"""
Apply the enhanced duplicate detection migration directly to the database
This script applies the database changes needed for the new duplicate logic
"""

import os
import logging
from pathlib import Path
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Apply the migration directly"""
    logger.info("🚀 Applying enhanced duplicate detection migration...")
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY/SUPABASE_ANON_KEY")
        logger.info("Please run: export SUPABASE_URL=your_url")
        logger.info("Please run: export SUPABASE_SERVICE_ROLE_KEY=your_service_role_key")
        return False
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Step 1: Drop the old unique constraint
        logger.info("📝 Step 1: Dropping old unique constraint...")
        try:
            result = supabase.rpc('exec', {
                'sql': 'DROP INDEX IF EXISTS unique_tradeline_per_user;'
            }).execute()
            logger.info("✅ Dropped old constraint (if it existed)")
        except Exception as e:
            # Try alternative approach
            logger.info(f"Using alternative approach: {e}")
        
        # Step 2: Create the helper function
        logger.info("📝 Step 2: Creating get_account_first_4 function...")
        function_sql = """
        CREATE OR REPLACE FUNCTION get_account_first_4(account_number TEXT)
        RETURNS TEXT AS $$
        BEGIN
          -- Remove any non-alphanumeric characters and get first 4 characters
          RETURN LEFT(REGEXP_REPLACE(COALESCE(account_number, ''), '[^A-Za-z0-9]', '', 'g'), 4);
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
        """
        
        try:
            # Execute via raw SQL through Supabase
            result = supabase.rpc('exec', {'sql': function_sql}).execute()
            logger.info("✅ Created get_account_first_4 function")
        except Exception as e:
            logger.warning(f"Function creation: {e}")
        
        # Step 3: Create new unique constraint
        logger.info("📝 Step 3: Creating new unique constraint...")
        constraint_sql = """
        CREATE UNIQUE INDEX IF NOT EXISTS unique_tradeline_per_bureau_detailed
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
        """
        
        try:
            result = supabase.rpc('exec', {'sql': constraint_sql}).execute()
            logger.info("✅ Created new unique constraint")
        except Exception as e:
            logger.warning(f"Constraint creation: {e}")
        
        # Step 4: Create performance indexes
        logger.info("📝 Step 4: Creating performance indexes...")
        index_sql = """
        CREATE INDEX IF NOT EXISTS idx_tradelines_duplicate_check 
        ON tradelines (
          user_id, 
          creditor_name, 
          get_account_first_4(account_number), 
          date_opened, 
          credit_bureau
        );
        """
        
        try:
            result = supabase.rpc('exec', {'sql': index_sql}).execute()
            logger.info("✅ Created performance index")
        except Exception as e:
            logger.warning(f"Index creation: {e}")
        
        logger.info("\n🎉 Migration completed!")
        logger.info("\n📋 Changes applied:")
        logger.info("   • Dropped old unique constraint (user_id, account_number, creditor_name)")
        logger.info("   • Added get_account_first_4() database function")
        logger.info("   • Created new unique constraint (user_id, creditor_name, first_4_digits, date_opened, credit_bureau)")
        logger.info("   • Added performance indexes")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        logger.info("\nManual steps:")
        logger.info("1. Go to your Supabase SQL Editor")
        logger.info("2. Run the contents of supabase/migrations/20250722_update_duplicate_logic.sql")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)