#!/usr/bin/env python3
"""
Apply the enhanced duplicate detection migration to the database
This script updates the unique constraints to support the new duplicate logic
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def apply_migration():
    """Apply the enhanced duplicate detection migration"""
    
    # Get Supabase credentials from environment or .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        logger.warning("python-dotenv not available, using environment variables only")
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_service_key:
        logger.error("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables")
        logger.info("Please set these in your .env file or environment")
        return False
    
    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_service_key)
        
        logger.info("🚀 Applying enhanced duplicate detection migration...")
        
        # Read the migration SQL
        migration_file = Path(__file__).parent / "supabase" / "migrations" / "20250722_update_duplicate_logic.sql"
        
        if not migration_file.exists():
            logger.error(f"Migration file not found: {migration_file}")
            return False
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        logger.info("📄 Executing migration SQL...")
        
        # Execute the migration
        # Note: This is a simplified approach. In production, you'd want to use Supabase's migration system
        result = supabase.rpc('exec_sql', {'sql': migration_sql})
        
        if result.data:
            logger.info("✅ Migration applied successfully!")
            
            # Verify the new constraint exists
            verify_sql = """
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'tradelines' 
            AND indexname IN ('unique_tradeline_per_bureau_detailed', 'idx_tradelines_duplicate_check');
            """
            
            verification = supabase.rpc('exec_sql', {'sql': verify_sql})
            
            if verification.data:
                logger.info("🔍 Verification:")
                for index in verification.data:
                    logger.info(f"   ✅ Index: {index.get('indexname')}")
            else:
                logger.warning("⚠️ Could not verify new indexes")
            
            logger.info("\n🎉 Enhanced duplicate detection is now active!")
            logger.info("\n📋 Changes applied:")
            logger.info("   • Removed old unique constraint (user_id, account_number, creditor_name, credit_bureau)")
            logger.info("   • Added new unique constraint (user_id, creditor_name, first_4_digits, date_opened, credit_bureau)")
            logger.info("   • Added get_account_first_4() database function")
            logger.info("   • Added performance indexes for new duplicate detection logic")
            
            return True
        else:
            logger.error("❌ Migration failed - no result returned")
            return False
            
    except Exception as e:
        logger.error(f"❌ Migration failed with error: {str(e)}")
        
        # Provide helpful error messages for common issues
        if "permission denied" in str(e).lower():
            logger.error("💡 Tip: Make sure you're using the SERVICE_ROLE_KEY, not the anon key")
        elif "function exec_sql does not exist" in str(e).lower():
            logger.error("💡 Tip: You may need to create the exec_sql function or run this migration through Supabase CLI")
            logger.info("\nAlternative: Run the migration manually:")
            logger.info("1. Go to your Supabase SQL Editor")
            logger.info("2. Copy and paste the contents of supabase/migrations/20250722_update_duplicate_logic.sql")
            logger.info("3. Execute the SQL")
        
        return False

def main():
    """Main function"""
    print("=== Enhanced Duplicate Detection Migration ===\n")
    
    success = asyncio.run(apply_migration())
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Test the new duplicate detection with your application")
        print("2. Monitor for any issues with existing tradelines")
        print("3. Consider running a data cleanup if needed")
    else:
        print("\n❌ Migration failed!")
        print("\nManual migration steps:")
        print("1. Open Supabase SQL Editor")
        print("2. Run the contents of supabase/migrations/20250722_update_duplicate_logic.sql")
        print("3. Verify the new indexes are created")

if __name__ == "__main__":
    main()