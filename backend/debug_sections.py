"""
Debug script to see what's in each section
"""
import asyncio
from services.optimized_processor import OptimizedCreditReportProcessor

async def debug_sections():
    pdf_path = "TransUnion-06-10-2025.pdf"
    processor = OptimizedCreditReportProcessor()

    print("Extracting OCR text...")
    result = await processor._extract_with_ocr(pdf_path)

    if result.get('success'):
        text = result.get('text', '')
        print(f"OCR extracted {len(text)} characters\n")

        # Detect sections
        sections = processor._detect_credit_report_sections(text)
        print(f"Found {len(sections)} sections: {list(sections.keys())}\n")

        # Check each section for "Account Name"
        for section_name, section_text in sections.items():
            count = section_text.count("Account Name")
            print(f"\n{'='*60}")
            print(f"Section: {section_name}")
            print(f"Length: {len(section_text)} chars")
            print(f"'Account Name' occurrences: {count}")

            if count > 0:
                print(f"\n--- First 1000 chars ---")
                print(section_text[:1000])

if __name__ == "__main__":
    asyncio.run(debug_sections())
