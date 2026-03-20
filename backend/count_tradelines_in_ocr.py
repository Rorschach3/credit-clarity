"""
Count how many "Account Name" headers are in the OCR text
"""
import asyncio
from services.optimized_processor import OptimizedCreditReportProcessor

async def count_account_names():
    pdf_path = "TransUnion-06-10-2025.pdf"
    processor = OptimizedCreditReportProcessor()

    print("Extracting OCR text from 40 pages...")
    result = await processor._extract_with_ocr(pdf_path)

    if result.get('success'):
        text = result.get('text', '')
        print(f"\nOCR extracted: {len(text)} chars\n")

        # Count occurrences
        account_name_count = text.count("Account Name")
        print(f"'Account Name' found: {account_name_count} times")

        # Show context around each occurrence
        print(f"\n--- First 5 'Account Name' occurrences ---\n")
        start_idx = 0
        for i in range(min(5, account_name_count)):
            idx = text.find("Account Name", start_idx)
            if idx == -1:
                break

            # Get context
            context_start = max(0, idx - 100)
            context_end = min(len(text), idx + 200)
            context = text[context_start:context_end]

            print(f"\n{i+1}. Position {idx}:")
            print(f"   {context}")
            print(f"   {'-'*80}")

            start_idx = idx + 1

if __name__ == "__main__":
    asyncio.run(count_account_names())
