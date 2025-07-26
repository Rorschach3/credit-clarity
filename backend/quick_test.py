#!/usr/bin/env python3
"""
Quick test to see PDF content
"""

import PyPDF2
import re

def extract_pdf_text(pdf_path):
    """Extract text from PDF"""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num, page in enumerate(reader.pages):
            if page_num < 3:  # Only first 3 pages for speed
                text += f"\n=== PAGE {page_num + 1} ===\n"
                text += page.extract_text()
    return text

def analyze_pdf_structure():
    """Analyze the PDF structure"""
    pdf_path = "/mnt/g/OneDrive/Personal/Desktop/TransUnion-06-10-2025.pdf"
    
    print("🔍 Quick PDF Analysis...")
    
    # Extract limited text
    text = extract_pdf_text(pdf_path)
    print(f"📖 Extracted {len(text)} characters from first 3 pages")
    
    print("\n📋 First 1500 characters:")
    print("=" * 60)
    print(text[:1500])
    print("=" * 60)
    
    # Look for expected creditors
    expected_creditors = [
        "UPSTART", "SUNRISE BANK", "SCHOOLSFIRST", "SELF FINANCIAL", 
        "WEBBANK", "FINGERHUT", "DISCOVER", "SYNCB", "CARE CREDIT",
        "CAPITAL ONE", "BANK OF AMERICA", "JPMCB", "CREDIT ONE",
        "CLIMB", "MOHELA", "LENTEGRITY", "ATLANTIC"
    ]
    
    print(f"\n🔍 Creditor Analysis:")
    found_creditors = []
    for creditor in expected_creditors:
        count = text.upper().count(creditor.upper())
        if count > 0:
            found_creditors.append(creditor)
            print(f"  ✅ {creditor}: {count} mentions")
        else:
            print(f"  ❌ {creditor}: Not found")
    
    print(f"\n📊 Summary: Found {len(found_creditors)}/{len(expected_creditors)} expected creditors")
    
    # Look for common patterns
    print(f"\n🔍 Pattern Analysis:")
    patterns = [
        (r'\$\d{1,3}(,\d{3})*', "Dollar amounts"),
        (r'\d{2}/\d{2}/\d{4}', "Dates (MM/DD/YYYY)"),
        (r'\*{4,}\d{4}', "Masked account numbers"),
        (r'\d+\*{4,}', "Account numbers with trailing asterisks"),
        (r'Current|Closed|Open|Paid', "Account statuses"),
        (r'Credit Card|Revolving|Installment', "Account types")
    ]
    
    for pattern, description in patterns:
        matches = re.findall(pattern, text)
        print(f"  {description}: {len(matches)} matches")
        if matches and len(matches) <= 10:
            print(f"    Examples: {matches[:5]}")

if __name__ == "__main__":
    analyze_pdf_structure()