#!/usr/bin/env python3
"""
Test Document AI extraction directly
"""

import sys
import os
sys.path.append(os.getcwd())

from main import DocumentAIProcessor

def test_document_ai():
    """Test Document AI processing"""
    pdf_path = "/mnt/g/OneDrive/Personal/Desktop/TransUnion-06-10-2025.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    print("🧪 Testing Document AI Processing...")
    
    try:
        doc_ai = DocumentAIProcessor()
        
        # Test text extraction
        print("📖 Extracting text with Document AI...")
        extracted_text = doc_ai.extract_text(pdf_path)
        
        print(f"✅ Document AI extracted {len(extracted_text)} characters")
        print("\n📋 First 2000 characters from Document AI:")
        print("=" * 60)
        print(extracted_text[:2000])
        print("=" * 60)
        
        # Look for creditors in Document AI text
        expected_creditors = [
            "UPSTART", "SUNRISE BANK", "SCHOOLSFIRST", "SELF FINANCIAL", 
            "WEBBANK", "FINGERHUT", "DISCOVER", "SYNCB", "CARE CREDIT",
            "CAPITAL ONE", "BANK OF AMERICA", "JPMCB", "CREDIT ONE",
            "CLIMB", "MOHELA", "LENTEGRITY", "ATLANTIC"
        ]
        
        print(f"\n🔍 Creditor Analysis in Document AI text:")
        found_creditors = []
        for creditor in expected_creditors:
            count = extracted_text.upper().count(creditor.upper())
            if count > 0:
                found_creditors.append(creditor)
                print(f"  ✅ {creditor}: {count} mentions")
            else:
                print(f"  ❌ {creditor}: Not found")
        
        print(f"\n📊 Summary: Found {len(found_creditors)}/{len(expected_creditors)} expected creditors")
        
        # Try structured extraction
        print(f"\n🔍 Testing structured tradeline extraction...")
        structured_tradelines = doc_ai.extract_structured_tradelines(pdf_path)
        print(f"📊 Structured extraction found {len(structured_tradelines)} tradelines")
        
        for i, tradeline in enumerate(structured_tradelines, 1):
            print(f"  {i}. {tradeline.get('creditor_name', 'Unknown')}")
        
        return extracted_text, structured_tradelines
        
    except Exception as e:
        print(f"❌ Document AI test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_document_ai()