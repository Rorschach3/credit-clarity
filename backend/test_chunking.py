#!/usr/bin/env python3
"""
Test the PDF chunking and Document AI integration
"""

import sys
import os
import asyncio
sys.path.append(os.getcwd())

from main import DocumentAIProcessor
from services.pdf_chunking_service import PDFChunkingService

async def test_chunking():
    """Test PDF chunking and processing"""
    pdf_path = "/mnt/g/OneDrive/Personal/Desktop/TransUnion-06-10-2025.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    print("🧪 Testing PDF Chunking and Document AI Integration...")
    
    try:
        # Test chunking service directly
        print("📊 Step 1: Analyzing PDF structure...")
        chunking_service = PDFChunkingService(max_pages_per_chunk=15)
        
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        chunking_info = chunking_service.get_chunking_info(pdf_content)
        print(f"  Total pages: {chunking_info['total_pages']}")
        print(f"  Chunks needed: {chunking_info['chunks_needed']}")
        print(f"  Library: {chunking_info['library_used']}")
        
        # Test Document AI with chunking
        print("\n📄 Step 2: Testing Document AI with chunking...")
        doc_ai = DocumentAIProcessor()
        
        # This should now handle the 71 pages by chunking
        extracted_text, form_fields = await doc_ai.extract_text_and_entities(pdf_path)
        
        print(f"✅ Document AI with chunking extracted:")
        print(f"  Text length: {len(extracted_text)} characters")
        print(f"  Form fields: {len(form_fields)} fields")
        
        # Show first 1000 chars
        print(f"\n📋 First 1000 characters of extracted text:")
        print("=" * 60)
        print(extracted_text[:1000])
        print("=" * 60)
        
        # Look for creditors in the chunked extraction
        expected_creditors = [
            "UPSTART", "SUNRISE BANK", "SCHOOLSFIRST", "SELF FINANCIAL", 
            "WEBBANK", "FINGERHUT", "DISCOVER", "SYNCB", "CARE CREDIT",
            "CAPITAL ONE", "BANK OF AMERICA", "JPMCB", "CREDIT ONE",
            "CLIMB", "MOHELA", "LENTEGRITY", "ATLANTIC"
        ]
        
        print(f"\n🔍 Creditor Analysis in chunked extraction:")
        found_creditors = []
        for creditor in expected_creditors:
            count = extracted_text.upper().count(creditor.upper())
            if count > 0:
                found_creditors.append(creditor)
                print(f"  ✅ {creditor}: {count} mentions")
            else:
                print(f"  ❌ {creditor}: Not found")
        
        print(f"\n📊 Summary: Found {len(found_creditors)}/{len(expected_creditors)} expected creditors")
        
        # Show sample form fields
        print(f"\n📋 Sample form fields (first 10):")
        for i, field in enumerate(form_fields[:10], 1):
            print(f"  {i}. '{field['field_name']}' = '{field['field_value']}'")
        
        return extracted_text, form_fields
        
    except Exception as e:
        print(f"❌ Chunking test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chunking())