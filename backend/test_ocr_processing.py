"""
Test OCR processing directly with optimized_processor
"""
import asyncio
import sys
from services.optimized_processor import OptimizedCreditReportProcessor

async def test_pdf_processing():
    pdf_path = "TransUnion-06-10-2025.pdf"

    print(f"\n{'='*60}")
    print(f"Testing OCR Processing with 300s timeout")
    print(f"PDF: {pdf_path}")
    print(f"{'='*60}\n")

    processor = OptimizedCreditReportProcessor()

    try:
        result = await processor.process_credit_report_optimized(pdf_path)

        print(f"\n{'='*60}")
        print(f"PROCESSING RESULT:")
        print(f"{'='*60}")
        print(f"Success: {result.get('success', False)}")
        print(f"Method: {result.get('method_used', 'unknown')}")
        print(f"Processing Time: {result.get('processing_time', 0):.2f}s")
        print(f"Tradelines Found: {len(result.get('tradelines', []))}")
        print(f"Cost: ${result.get('cost_estimate', 0):.4f}")

        if result.get('error'):
            print(f"Error: {result['error']}")

        # Show first few tradelines
        tradelines = result.get('tradelines', [])
        if tradelines:
            print(f"\n{'='*60}")
            print(f"SAMPLE TRADELINES (first 3):")
            print(f"{'='*60}")
            for i, tl in enumerate(tradelines[:3], 1):
                print(f"\n{i}. {tl.get('creditor_name', 'Unknown')}")
                print(f"   Account: {tl.get('account_number', 'N/A')}")
                print(f"   Balance: {tl.get('account_balance', 'N/A')}")
                print(f"   Status: {tl.get('account_status', 'N/A')}")
                print(f"   Negative: {tl.get('is_negative', False)}")
        else:
            print("\nNo tradelines extracted!")

        print(f"\n{'='*60}\n")

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_pdf_processing())
