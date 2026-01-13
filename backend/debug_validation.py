"""
Debug validation layer to see what's wiping out creditor names
"""
import asyncio
from services.optimized_processor import OptimizedCreditReportProcessor

async def debug_validation():
    pdf_path = "TransUnion-06-10-2025.pdf"
    processor = OptimizedCreditReportProcessor()

    print("Extracting OCR text...")
    result = await processor._extract_with_ocr(pdf_path)

    if result.get('success'):
        text = result.get('text', '')
        print(f"OCR extracted: {len(text)} chars\n")

        # Parse tradelines
        from services.enhanced_gemini_processor import EnhancedGeminiProcessor
        parser = EnhancedGeminiProcessor()
        tradelines = parser._fallback_basic_parsing(text)

        print(f"Parsed tradelines: {len(tradelines)}")
        for i, tl in enumerate(tradelines[:3]):
            print(f"  {i}: {tl.get('creditor_name', '')[:50]}")

        if tradelines:
            # Test validation on first tradeline
            print(f"\n{'='*60}")
            print("Testing validation on first tradeline:")
            print(f"{'='*60}\n")

            test_tradeline = tradelines[0].copy()
            print(f"Before validation:")
            print(f"  creditor_name: '{test_tradeline.get('creditor_name', '')[:50]}'")
            print(f"  account_number: '{test_tradeline.get('account_number', '')}'")
            print(f"  account_balance: '{test_tradeline.get('account_balance', '')}'")

            # Run validation
            from services.advanced_parsing.ai_tradeline_validator import AITradelineValidator
            validator = AITradelineValidator()

            try:
                validation_results = await validator.batch_validate_tradelines([test_tradeline], text)

                if validation_results:
                    result = validation_results[0]
                    print(f"\nValidation result:")
                    print(f"  is_valid: {result.is_valid}")
                    print(f"  confidence: {result.confidence}")
                    print(f"  issues: {result.issues}")

                    if hasattr(result, 'corrected_data') and result.corrected_data:
                        corrected = result.corrected_data if isinstance(result.corrected_data, dict) else vars(result.corrected_data)
                        print(f"\nCorrected data keys: {list(corrected.keys())}")
                        print(f"  creditor_name in corrected: {'creditor_name' in corrected}")
                        if 'creditor_name' in corrected:
                            print(f"  corrected creditor_name: '{corrected.get('creditor_name', '')[:50]}'")

                        # Simulate the update
                        test_copy = test_tradeline.copy()
                        test_copy.update(corrected)
                        print(f"\nAfter update with corrected_data:")
                        print(f"  creditor_name: '{test_copy.get('creditor_name', '')[:50]}'")
                        print(f"  account_number: '{test_copy.get('account_number', '')}'")
                        print(f"  account_balance: '{test_copy.get('account_balance', '')}'")
                    else:
                        print("\nNo corrected_data returned")

            except Exception as e:
                print(f"\nValidation failed: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_validation())
