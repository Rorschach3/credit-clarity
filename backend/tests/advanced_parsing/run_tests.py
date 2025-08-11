#!/usr/bin/env python3
"""
Quick test execution script for Phase 4 parsing accuracy validation.
This script provides a simple interface to run the comprehensive testing suite.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from test_runner import Phase4TestRunner


async def quick_test():
    """Run a quick validation test (reduced test count for faster execution)."""
    print("🚀 Running Quick Phase 4 Validation Test")
    print("📝 This will run a reduced test suite for faster results")
    print("-" * 60)
    
    runner = Phase4TestRunner(output_dir="/tmp/phase4_quick_test")
    
    # Run with reduced test count for speed
    results = await runner.run_all_tests(
        run_accuracy=True,
        run_performance=False,  # Skip performance tests for quick run
        run_real_world=True,
        run_edge_cases=True,
        test_count=20  # Reduced from 50
    )
    
    return results


async def full_test():
    """Run the complete comprehensive test suite."""
    print("🧪 Running Full Phase 4 Comprehensive Test Suite")
    print("⚠️  This may take 10-30 minutes depending on system performance")
    print("-" * 60)
    
    runner = Phase4TestRunner(output_dir="/tmp/phase4_full_test")
    
    results = await runner.run_all_tests(
        run_accuracy=True,
        run_performance=True,
        run_real_world=True,
        run_edge_cases=True,
        test_count=100  # Full test count
    )
    
    return results


async def accuracy_only_test():
    """Run only accuracy tests."""
    print("📊 Running Accuracy-Only Test")
    print("🎯 Focus: Validate 99% accuracy target achievement")
    print("-" * 60)
    
    runner = Phase4TestRunner(output_dir="/tmp/phase4_accuracy_test")
    
    results = await runner.run_all_tests(
        run_accuracy=True,
        run_performance=False,
        run_real_world=False,
        run_edge_cases=False,
        test_count=75
    )
    
    return results


def print_menu():
    """Print test menu options."""
    print("\n" + "=" * 80)
    print("🧪 PHASE 4 PARSING ACCURACY TESTING SUITE")
    print("=" * 80)
    print("Choose a test configuration:")
    print()
    print("1. 🚀 Quick Test (20 tests, ~5 minutes)")
    print("   - Basic accuracy validation")
    print("   - Real-world cases")
    print("   - Edge cases")
    print()
    print("2. 🧪 Full Test Suite (100 tests, ~30 minutes)")
    print("   - Comprehensive accuracy testing")
    print("   - Performance benchmarks")
    print("   - Real-world validation")
    print("   - Edge case testing")
    print()
    print("3. 📊 Accuracy Only (75 tests, ~15 minutes)")
    print("   - Focus on 99% accuracy target")
    print("   - Statistical significance")
    print()
    print("4. ❌ Exit")
    print()


async def main():
    """Main interactive test runner."""
    
    while True:
        print_menu()
        
        try:
            choice = input("Enter your choice (1-4): ").strip()
            
            if choice == "1":
                print("\n🚀 Starting Quick Test...")
                results = await quick_test()
                break
                
            elif choice == "2":
                print("\n🧪 Starting Full Test Suite...")
                confirm = input("⚠️  This will take 20-30 minutes. Continue? (y/n): ").lower().strip()
                if confirm in ['y', 'yes']:
                    results = await full_test()
                    break
                else:
                    continue
                    
            elif choice == "3":
                print("\n📊 Starting Accuracy-Only Test...")
                results = await accuracy_only_test()
                break
                
            elif choice == "4":
                print("👋 Goodbye!")
                sys.exit(0)
                
            else:
                print("❌ Invalid choice. Please enter 1-4.")
                continue
                
        except KeyboardInterrupt:
            print("\n\n👋 Test cancelled by user.")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again or exit.")
            continue
    
    # Print final results summary
    print("\n" + "=" * 80)
    print("✅ TEST EXECUTION COMPLETE!")
    print("=" * 80)
    
    # Try to show accuracy results if available
    try:
        if "accuracy_tests" in results and results["accuracy_tests"]["success"]:
            accuracy = results["accuracy_tests"]["summary"]["overall_accuracy"]
            target_achieved = accuracy >= 99.0
            
            print(f"🎯 ACCURACY RESULTS:")
            print(f"   Overall Accuracy: {accuracy:.2f}%")
            print(f"   99% Target: {'✅ ACHIEVED' if target_achieved else '❌ NOT ACHIEVED'}")
            
            if target_achieved:
                print("\n🎉 CONGRATULATIONS!")
                print("   Phase 4 advanced parsing pipeline meets the 99% accuracy target!")
                print("   The system is ready for production deployment.")
            else:
                print(f"\n⚠️  NEEDS IMPROVEMENT:")
                print(f"   Current accuracy ({accuracy:.2f}%) is below the 99% target.")
                print(f"   Gap to close: {99.0 - accuracy:.2f} percentage points.")
                
        else:
            print("📋 Accuracy test results not available.")
            
    except Exception as e:
        print(f"📋 Could not display results summary: {e}")
    
    print("\n📁 Check the output directory for detailed reports and analysis.")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)