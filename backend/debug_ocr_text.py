"""
Debug script to save OCR text for inspection
"""
import asyncio
from services.optimized_processor import OptimizedCreditReportProcessor

async def extract_and_save_ocr_text():
    pdf_path = "TransUnion-06-10-2025.pdf"
    processor = OptimizedCreditReportProcessor()

    print("Extracting OCR text...")
    result = await processor._extract_with_ocr(pdf_path)

    if result.get('success'):
        text = result.get('text', '')
        print(f"OCR extracted {len(text)} characters")

        # Save to file for inspection
        with open('ocr_output.txt', 'w', encoding='utf-8') as f:
            f.write(text)
        print("Saved to ocr_output.txt")

        # Show a sample
        print("\n" + "="*60)
        print("SAMPLE FROM PAGES 8-10 (where tradelines should be):")
        print("="*60)
        lines = text.split('\n')
        in_page_8_10 = False
        sample_lines = []
        for line in lines:
            if '--- Page 8' in line:
                in_page_8_10 = True
            if '--- Page 11' in line:
                break
            if in_page_8_10:
                sample_lines.append(line)

        print('\n'.join(sample_lines[:100]))  # First 100 lines of pages 8-10
    else:
        print("OCR failed")

if __name__ == "__main__":
    asyncio.run(extract_and_save_ocr_text())
