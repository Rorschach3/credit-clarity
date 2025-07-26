#!/usr/bin/env python3
"""
Test the complete end-to-end processing pipeline
"""

import asyncio
import sys
import os
sys.path.append(os.getcwd())

async def test_end_to_end_processing():
    """Test the complete PDF processing pipeline"""
    try:
        # Import required modules
        from main import app
        from fastapi.testclient import TestClient
        import tempfile
        import shutil
        
        # Create a test client
        client = TestClient(app)
        
        # Check if PDF file exists
        pdf_path = "/mnt/c/projects/credit-clarity/TransUnion-06-10-2025.pdf"
        if not os.path.exists(pdf_path):
            print(f"❌ PDF file not found at {pdf_path}")
            return False
        
        print(f"✅ Found PDF file: {pdf_path}")
        print(f"📄 File size: {os.path.getsize(pdf_path) / (1024*1024):.2f} MB")
        
        # Test the processing endpoint
        print("🔄 Testing PDF processing...")
        
        with open(pdf_path, 'rb') as pdf_file:
            files = {'file': ('TransUnion-06-10-2025.pdf', pdf_file, 'application/pdf')}
            data = {'method': 'ai_processing'}
            
            print("📤 Sending request to /process-credit-report...")
            response = client.post('/process-credit-report', files=files, data=data)
            
        print(f"📨 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ PDF processing successful!")
            
            # Analyze results
            if 'tradelines' in result:
                tradelines = result['tradelines']
                print(f"📊 Found {len(tradelines)} tradelines")
                
                # Show summary of tradelines
                if tradelines:
                    print("\n🏦 Creditors found:")
                    creditors = [t.get('creditor_name', 'Unknown') for t in tradelines[:10]]  # First 10
                    for i, creditor in enumerate(creditors, 1):
                        print(f"  {i}. {creditor}")
                    
                    if len(tradelines) > 10:
                        print(f"  ... and {len(tradelines) - 10} more")
                
                # Check if any were saved to database
                if 'database_stats' in result:
                    stats = result['database_stats']
                    print(f"\n💾 Database stats:")
                    print(f"  - New tradelines: {stats.get('new_tradelines', 0)}")
                    print(f"  - Updated tradelines: {stats.get('updated_tradelines', 0)}")
                    print(f"  - Failed saves: {stats.get('failed_saves', 0)}")
                
                return len(tradelines) > 0
            else:
                print("❌ No tradelines found in response")
                return False
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            return False
            
    except Exception as e:
        print(f"❌ End-to-end test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_end_to_end_processing())
    if success:
        print("\n🎉 End-to-end test passed! The system is working correctly.")
    else:
        print("\n❌ End-to-end test failed.")