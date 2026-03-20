"""
Find what text is being lost in section detection
"""
import asyncio
from services.optimized_processor import OptimizedCreditReportProcessor

async def find_lost_text():
    pdf_path = "TransUnion-06-10-2025.pdf"
    processor = OptimizedCreditReportProcessor()

    print("Extracting OCR text...")
    result = await processor._extract_with_ocr(pdf_path)

    if result.get('success'):
        text = result.get('text', '')
        sections = processor._detect_credit_report_sections(text)

        # Combine all section texts
        all_section_text = '\n'.join(sections.values())

        print(f"OCR text: {len(text)} chars")
        print(f"All sections: {len(all_section_text)} chars")
        print(f"Lost: {len(text) - len(all_section_text)} chars\n")

        # Find what's in OCR text but not in sections
        # Check if CAPITAL ONE is in the original text but not in sections
        if 'CAPITAL ONE' in text and 'CAPITAL ONE' not in all_section_text:
            print("CAPITAL ONE is in OCR text but NOT in any section!")

            # Find where CAPITAL ONE appears in the original
            idx = text.find('CAPITAL ONE')
            start = max(0, idx - 500)
            end = min(len(text), idx + 500)

            print("\n--- Context around first CAPITAL ONE in OCR ---")
            print(text[start:end])

            # Check what section marker (if any) appears before CAPITAL ONE
            before_text = text[:idx]
            print(f"\n--- Last 300 chars before CAPITAL ONE ---")
            print(before_text[-300:])

if __name__ == "__main__":
    asyncio.run(find_lost_text())
