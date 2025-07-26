#!/usr/bin/env python3
"""
Test that the import fix works
"""

import sys
import os
import asyncio
sys.path.append(os.getcwd())

async def test_import():
    """Test the enhanced tradeline service import"""
    try:
        from services.enhanced_tradeline_service import EnhancedTradelineService
        print("✅ Successfully imported EnhancedTradelineService")
        
        # Create a dummy supabase client (just for testing the import)
        class MockSupabase:
            pass
        
        service = EnhancedTradelineService(MockSupabase())
        print("✅ Successfully created EnhancedTradelineService instance")
        
        # Test some basic methods
        result = service.get_account_first_4("****1234")
        print(f"✅ get_account_first_4('****1234') = '{result}'")
        
        should_update = service.should_update_field("", "$100")
        print(f"✅ should_update_field('', '$100') = {should_update}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_import())
    if success:
        print("\n🎉 All import tests passed! The save functionality should now work.")
    else:
        print("\n❌ Import tests failed.")