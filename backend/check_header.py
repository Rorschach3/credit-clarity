"""
Check what's in the header section
"""
import asyncio
from services.optimized_processor import OptimizedCreditReportProcessor

async def check_header():
    pdf_path = "TransUnion-06-10-2025.pdf"
    processor = OptimizedCreditReportProcessor()

    print("Extracting OCR text...")
    result = await processor._extract_with_ocr(pdf_path)

    if result.get('success'):
        text = result.get('text', '')

        # Detect sections
        sections = processor._detect_credit_report_sections(text)

        # Check header section
        header = sections.get('header', '')
        print(f"Header section: {len(header)} chars")
        print(f"Contains 'CAPITAL': {header.count('CAPITAL')}")
        print(f"Contains 'Account Name': {header.count('Account Name')}")

        if 'CAPITAL' in header:
            # Find context around CAPITAL
            idx = header.find('CAPITAL')
            start = max(0, idx - 300)
            end = min(len(header), idx + 700)
            print(f"\n--- Context around CAPITAL ---")
            print(header[start:end])

if __name__ == "__main__":
    asyncio.run(check_header())
