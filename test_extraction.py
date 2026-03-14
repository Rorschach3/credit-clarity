"""
Quick test script to verify tradeline extraction pipeline works end-to-end
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from services.tradeline_extraction.pipeline import TradelineExtractionPipeline

async def test_extraction():
    """Test the full extraction pipeline"""
    pdf_path = Path(__file__).parent / "backend" / "TransUnion-06-10-2025.pdf"

    if not pdf_path.exists():
        print(f"❌ Sample PDF not found at {pdf_path}")
        return False

    print(f"✅ Found sample PDF: {pdf_path}")
    print(f"📄 File size: {pdf_path.stat().st_size / 1024:.2f} KB")
    print()

    # Initialize pipeline
    print("🔧 Initializing tradeline extraction pipeline...")
    pipeline = TradelineExtractionPipeline(use_real_world_parser=True)
    print("✅ Pipeline initialized")
    print()

    # Run extraction (don't store to avoid database dependency)
    print("🚀 Starting extraction process...")
    result = await pipeline.process_credit_report(
        pdf_path=str(pdf_path),
        user_id="test-user-123",
        store_results=False  # Don't store to database for this test
    )

    # Print results
    print("\n" + "="*60)
    print("EXTRACTION RESULTS")
    print("="*60)
    print(f"✅ Success: {result.success}")
    print(f"📄 PDF Processed: {result.pdf_processed}")
    print(f"📝 Text Extracted: {result.text_extracted}")
    print(f"🔍 Tradelines Parsed: {result.tradelines_parsed}")
    print(f"✔️  Tradelines Validated: {result.tradelines_validated}")
    print(f"⏱️  Processing Time: {result.processing_time_ms}ms")
    print()

    if result.warnings:
        print("⚠️  Warnings:")
        for warning in result.warnings:
            print(f"  - {warning}")
        print()

    if result.error:
        print(f"❌ Error: {result.error}")
        return False

    if result.validation_summary:
        print(f"📊 Validation Summary ({len(result.validation_summary)} tradelines):")
        for i, summary in enumerate(result.validation_summary[:5], 1):  # Show first 5
            print(f"  {i}. Valid: {summary.get('valid')}, Score: {summary.get('score', 'N/A')}")
        if len(result.validation_summary) > 5:
            print(f"  ... and {len(result.validation_summary) - 5} more")
        print()

    if result.metadata:
        print("📈 Metadata:")
        for key, value in result.metadata.items():
            print(f"  - {key}: {value}")
        print()

    return result.success

if __name__ == "__main__":
    print("🧪 Testing Tradeline Extraction Pipeline")
    print("="*60)
    print()

    success = asyncio.run(test_extraction())

    print()
    print("="*60)
    if success:
        print("✅ TEST PASSED - Tradeline extraction is working!")
    else:
        print("❌ TEST FAILED - Check errors above")
    print("="*60)

    sys.exit(0 if success else 1)
