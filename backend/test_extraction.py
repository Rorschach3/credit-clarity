#!/usr/bin/env python3
"""
Test PDF extraction with the improvements
"""

import PyPDF2
import tempfile
import sys
import os
sys.path.append(os.getcwd())

from main import GeminiProcessor, DocumentAIProcessor, parse_tradelines_basic

def extract_pdf_text(pdf_path):
    """Extract text from PDF"""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text

def test_gemini_extraction():
    """Test Gemini extraction with improved prompt"""
    pdf_path = "/mnt/g/OneDrive/Personal/Desktop/TransUnion-06-10-2025.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    print("🧪 Testing Improved Gemini Extraction...")
    
    # Extract text
    text = extract_pdf_text(pdf_path)
    print(f"📖 Extracted {len(text)} characters from PDF")
    
    # Test Gemini processing 
    try:
        gemini = GeminiProcessor()
        tradelines = gemini.extract_tradelines(text)
        
        print(f"📊 Gemini extracted {len(tradelines)} tradelines:")
        
        expected_creditors = [
            "UPSTART", "SUNRISE BANK", "SCHOOLSFIRST", "SELF FINANCIAL", 
            "WEBBANK", "DISCOVER", "SYNCB", "CAPITAL ONE", "BANK OF AMERICA",
            "JPMCB", "CREDIT ONE", "CLIMB", "MOHELA", "LENTEGRITY", "ATLANTIC"
        ]
        
        found_creditors = []
        for i, tradeline in enumerate(tradelines, 1):
            creditor = tradeline.get('creditor_name', 'Unknown')
            found_creditors.append(creditor)
            print(f"  {i}. {creditor}")
            print(f"     Balance: {tradeline.get('account_balance', 'N/A')}")
            print(f"     Credit Limit: {tradeline.get('credit_limit', 'N/A')}")
            print(f"     Account #: {tradeline.get('account_number', 'N/A')}")
            print(f"     Status: {tradeline.get('account_status', 'N/A')}")
        
        # Check coverage of expected creditors
        print(f"\n📈 Coverage Analysis:")
        for expected in expected_creditors:
            found = any(expected.upper() in creditor.upper() for creditor in found_creditors)
            print(f"  {'✅' if found else '❌'} {expected}: {'Found' if found else 'Missing'}")
        
    except Exception as e:
        print(f"❌ Gemini test failed: {e}")

if __name__ == "__main__":
    test_gemini_extraction()