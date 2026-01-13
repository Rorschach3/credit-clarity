"""
Debug why section detection is losing text
"""
import asyncio
from services.optimized_processor import OptimizedCreditReportProcessor

async def debug_section_loss():
    pdf_path = "TransUnion-06-10-2025.pdf"
    processor = OptimizedCreditReportProcessor()

    print("Extracting OCR text...")
    result = await processor._extract_with_ocr(pdf_path)

    if result.get('success'):
        text = result.get('text', '')
        print(f"Total OCR text: {len(text)} chars\n")

        # Check if CAPITAL ONE is in the full text
        print(f"Full text contains 'CAPITAL ONE': {text.count('CAPITAL ONE')}")
        print(f"Full text contains 'Account Name': {text.count('Account Name')}\n")

        # Detect sections
        sections = processor._detect_credit_report_sections(text)

        # Calculate total section chars
        total_section_chars = sum(len(section_text) for section_text in sections.values())
        print(f"Total section chars: {total_section_chars}")
        print(f"Lost chars: {len(text) - total_section_chars}\n")

        # Show each section size
        for section_name, section_text in sections.items():
            print(f"{section_name}: {len(section_text)} chars")

        # Check what's in the lost text
        # The section detection should save all text, but let's see if there's
        # text that didn't match any section pattern
        print(f"\n--- Checking for CAPITAL ONE in each section ---")
        for section_name, section_text in sections.items():
            if 'CAPITAL' in section_text:
                print(f"Found in {section_name}!")

if __name__ == "__main__":
    asyncio.run(debug_section_loss())
