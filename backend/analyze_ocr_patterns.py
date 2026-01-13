"""
Analyze OCR text to find all possible tradeline patterns
"""
import asyncio
import re
from services.optimized_processor import OptimizedCreditReportProcessor

async def analyze_patterns():
    pdf_path = "TransUnion-06-10-2025.pdf"
    processor = OptimizedCreditReportProcessor()

    print("Extracting OCR text from 40 pages...")
    result = await processor._extract_with_ocr(pdf_path)

    if result.get('success'):
        text = result.get('text', '')
        print(f"\nOCR extracted: {len(text)} chars\n")

        # Look for account-related patterns
        patterns = {
            "Account Name": text.count("Account Name"),
            "Account Number": text.count("Account Number"),
            "Account Type": text.count("Account Type"),
            "Account Status": text.count("Account Status"),
            "Date Opened": text.count("Date Opened"),
            "Monthly Payment": text.count("Monthly Payment"),
            "Balance": text.count("Balance"),
            "Credit Limit": text.count("Credit Limit"),
        }

        print("Pattern occurrences:")
        for pattern, count in patterns.items():
            print(f"  {pattern}: {count}")

        # Look for capitalized creditor names (common pattern)
        print(f"\n--- Looking for potential creditor patterns ---")
        lines = text.split('\n')
        for i, line in enumerate(lines[:1000]):  # First 1000 lines
            line = line.strip()
            # Look for lines that are all caps and might be creditors
            if line.isupper() and len(line) > 5 and len(line) < 50:
                # Check if next few lines contain account info
                next_lines = '\n'.join(lines[i+1:min(i+5, len(lines))])
                if any(keyword in next_lines for keyword in ['Account', 'Balance', 'Date Opened', 'Monthly']):
                    print(f"Potential creditor: {line}")

if __name__ == "__main__":
    asyncio.run(analyze_patterns())
