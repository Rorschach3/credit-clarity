#!/usr/bin/env python3
"""
Test basic extraction without Gemini
"""

import PyPDF2
import sys
import os
sys.path.append(os.getcwd())

from main import parse_tradelines_basic

def extract_pdf_text(pdf_path):
    """Extract text from PDF"""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text

def test_basic_extraction():
    """Test basic extraction"""
    pdf_path = "/mnt/g/OneDrive/Personal/Desktop/TransUnion-06-10-2025.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    print("🧪 Testing Basic Extraction (Fallback)...")
    
    # Extract text
    text = extract_pdf_text(pdf_path)
    print(f"📖 Extracted {len(text)} characters from PDF")
    
    # Test basic processing 
    try:
        tradelines = parse_tradelines_basic(text)
        
        print(f"📊 Basic parsing extracted {len(tradelines)} tradelines:")
        
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
            print(f"     Date Opened: {tradeline.get('date_opened', 'N/A')}")
        
        # Check coverage of expected creditors
        print(f"\n📈 Coverage Analysis:")
        for expected in expected_creditors:
            found = any(expected.upper() in creditor.upper() for creditor in found_creditors)
            print(f"  {'✅' if found else '❌'} {expected}: {'Found' if found else 'Missing'}")
        
        return tradelines
        
    except Exception as e:
        print(f"❌ Basic extraction test failed: {e}")
        import traceback
        traceback.print_exc()

def show_sample_text():
    """Show sample text from PDF to understand structure"""
    pdf_path = "/mnt/g/OneDrive/Personal/Desktop/TransUnion-06-10-2025.pdf"
    
    text = extract_pdf_text(pdf_path)
    
    print("📋 Sample text from PDF (first 2000 characters):")
    print("=" * 60)
    print(text[:2000])
    print("=" * 60)
    
    print("\n🔍 Looking for specific creditors in text:")
    creditors = ["UPSTART", "SUNRISE BANK", "CAPITAL ONE", "DISCOVER", "SYNCB", "WEBBANK"]
    for creditor in creditors:
        count = text.upper().count(creditor.upper())
        print(f"  {creditor}: {count} mentions")

if __name__ == "__main__":
    show_sample_text()
    print("\n" + "="*60 + "\n")
    test_basic_extraction()