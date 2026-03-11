"""
Comprehensive test runner for Phase 4 parsing accuracy validation.
Runs all test suites and generates consolidated reports.
"""
import pytest

# This module is an executable harness (not a unit test) and depends on optional heavy
# packages + local test assets. Skip it during normal `pytest` runs.
pytest.skip(
    "Phase 4 parsing test runner is a manual harness (requires optional dependencies).",
    allow_module_level=True,
)

import asyncio
import json
import os
import time
from datetime import datetime
from typing import Dict, Any, List
import argparse

# Import test modules
from test_parsing_accuracy import ParsingAccuracyTester, PerformanceBenchmark
from test_real_world_validation import RealWorldValidator, EdgeCaseTester
from test_sprint0_validation import Sprint0Validator


class Phase4TestRunner:
    """Main test runner for Phase 4 comprehensive testing."""
    
    def __init__(self, output_dir: str = "/tmp/phase4_test_results"):
        self.output_dir = output_dir
        self.start_time = None
        self.results = {}
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"📁 Test results will be saved to: {output_dir}")
    
    async def run_all_tests(
        self,
        run_accuracy: bool = True,
        run_performance: bool = True,
        run_real_world: bool = True,
        run_edge_cases: bool = True,
        run_sprint0: bool = True,
        test_count: int = 50
    ):
        """Run all Phase 4 tests."""

        self.start_time = time.time()
        print("🚀 Starting Phase 4 Comprehensive Testing Suite")
        print("=" * 80)
        print(f"Test Configuration:")
        print(f"  - Sprint 0 Validation: {'✅' if run_sprint0 else '❌'}")
        print(f"  - Accuracy Tests: {'✅' if run_accuracy else '❌'}")
        print(f"  - Performance Tests: {'✅' if run_performance else '❌'}")
        print(f"  - Real-World Validation: {'✅' if run_real_world else '❌'}")
        print(f"  - Edge Case Testing: {'✅' if run_edge_cases else '❌'}")
        print(f"  - Test Count: {test_count}")
        print("=" * 80)

        # Run Sprint 0 validation (PRIORITY: Real PDF vs Ground Truth SQL)
        if run_sprint0:
            print("\n🎯 Running Sprint 0 Validation (TransUnion PDF vs Ground Truth SQL)...")
            sprint0_results = await self.run_sprint0_validation()
            self.results["sprint0_validation"] = sprint0_results

        # Run accuracy tests
        if run_accuracy:
            print("\n📊 Running Parsing Accuracy Tests...")
            accuracy_results = await self.run_accuracy_tests(test_count)
            self.results["accuracy_tests"] = accuracy_results
        
        # Run performance tests
        if run_performance:
            print("\n⚡ Running Performance Benchmark Tests...")
            performance_results = await self.run_performance_tests()
            self.results["performance_tests"] = performance_results
        
        # Run real-world validation
        if run_real_world:
            print("\n🌍 Running Real-World Validation...")
            real_world_results = await self.run_real_world_tests()
            self.results["real_world_validation"] = real_world_results
        
        # Run edge case tests
        if run_edge_cases:
            print("\n🔬 Running Edge Case Tests...")
            edge_case_results = await self.run_edge_case_tests()
            self.results["edge_case_tests"] = edge_case_results
        
        # Generate comprehensive report
        await self.generate_comprehensive_report()
        
        total_time = time.time() - self.start_time
        print(f"\n✅ All tests completed in {total_time:.2f} seconds")
        print(f"📄 Comprehensive report saved to: {self.output_dir}")
        
        return self.results
    
    async def run_sprint0_validation(self):
        """Run Sprint 0 validation: Real PDF vs Ground Truth SQL."""
        try:
            from pathlib import Path

            backend_dir = Path(__file__).resolve().parents[2]
            pdf_path = backend_dir / 'TransUnion-06-10-2025.pdf'
            sql_path = backend_dir / 'tradeline_test_rows.sql'
            output_dir = Path(self.output_dir) / 'sprint0'

            validator = Sprint0Validator()
            report = await validator.run_validation(
                pdf_path=pdf_path,
                sql_path=sql_path,
                output_dir=output_dir
            )

            return {
                "success": report.passed,
                "report": {
                    "expected_count": report.expected_count,
                    "extracted_count": report.extracted_count,
                    "matched_count": report.matched_count,
                    "critical_accuracy": report.critical_accuracy,
                    "optional_accuracy": report.optional_accuracy,
                    "overall_accuracy": report.overall_accuracy,
                    "passed": report.passed,
                    "errors": report.errors,
                    "warnings": report.warnings
                },
                "summary": {
                    "overall_accuracy": report.overall_accuracy,
                    "critical_accuracy": report.critical_accuracy,
                    "optional_accuracy": report.optional_accuracy,
                    "target_achieved": report.passed,
                    "tests_passed": 1 if report.passed else 0,
                    "total_tests": 1
                }
            }
        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "summary": {
                    "overall_accuracy": 0.0,
                    "critical_accuracy": 0.0,
                    "optional_accuracy": 0.0,
                    "target_achieved": False,
                    "tests_passed": 0,
                    "total_tests": 1
                }
            }

    async def run_accuracy_tests(self, test_count: int):
        """Run parsing accuracy tests."""
        try:
            tester = ParsingAccuracyTester()
            report = await tester.run_comprehensive_test_suite(
                test_count=test_count,
                output_dir=f"{self.output_dir}/accuracy"
            )
            
            return {
                "success": True,
                "report": report.__dict__,
                "summary": {
                    "overall_accuracy": report.overall_accuracy,
                    "target_achieved": report.overall_accuracy >= 99.0,
                    "tests_passed": report.passed_tests,
                    "total_tests": report.total_tests,
                    "average_processing_time": report.average_processing_time
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "summary": {
                    "overall_accuracy": 0.0,
                    "target_achieved": False,
                    "tests_passed": 0,
                    "total_tests": 0
                }
            }
    
    async def run_performance_tests(self):
        """Run performance benchmark tests."""
        try:
            benchmark = PerformanceBenchmark()
            results = await benchmark.run_performance_benchmark(
                output_dir=f"{self.output_dir}/performance"
            )
            
            # Calculate summary metrics
            avg_throughput = sum(r["throughput"] for r in results) / len(results)
            avg_accuracy = sum(r["avg_accuracy"] for r in results) / len(results)
            max_throughput = max(r["throughput"] for r in results)
            
            return {
                "success": True,
                "results": results,
                "summary": {
                    "average_throughput": avg_throughput,
                    "maximum_throughput": max_throughput,
                    "average_accuracy": avg_accuracy,
                    "total_benchmarks": len(results)
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "summary": {
                    "average_throughput": 0.0,
                    "maximum_throughput": 0.0,
                    "average_accuracy": 0.0,
                    "total_benchmarks": 0
                }
            }
    
    async def run_real_world_tests(self):
        """Run real-world validation tests."""
        try:
            validator = RealWorldValidator()
            results = await validator.validate_real_world_cases()
            
            return {
                "success": True,
                "results": results,
                "summary": {
                    "overall_accuracy": results["overall_accuracy"],
                    "total_cases": results["total_cases"],
                    "cases_passed": sum(1 for r in results["results"] if r["success"]),
                    "difficulty_breakdown": results["difficulty_breakdown"]
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "summary": {
                    "overall_accuracy": 0.0,
                    "total_cases": 0,
                    "cases_passed": 0
                }
            }
    
    async def run_edge_case_tests(self):
        """Run edge case tests."""
        try:
            tester = EdgeCaseTester()
            results = await tester.test_edge_cases()
            
            return {
                "success": True,
                "results": results,
                "summary": {
                    "total_edge_cases": results["total_edge_cases"],
                    "passed_edge_cases": results["passed_edge_cases"],
                    "success_rate": results["passed_edge_cases"] / results["total_edge_cases"] * 100
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "summary": {
                    "total_edge_cases": 0,
                    "passed_edge_cases": 0,
                    "success_rate": 0.0
                }
            }
    
    async def generate_comprehensive_report(self):
        """Generate comprehensive test report."""
        
        # Calculate overall metrics
        overall_metrics = self.calculate_overall_metrics()
        
        # Create comprehensive report
        report = {
            "metadata": {
                "test_date": datetime.now().isoformat(),
                "test_duration_seconds": time.time() - self.start_time,
                "phase": "Phase 4 - Advanced Parsing Pipeline",
                "target": "99% tradeline extraction accuracy",
                "version": "1.0.0"
            },
            "overall_metrics": overall_metrics,
            "detailed_results": self.results,
            "conclusions": self.generate_conclusions(overall_metrics),
            "recommendations": self.generate_recommendations(overall_metrics)
        }
        
        # Save JSON report
        with open(f"{self.output_dir}/comprehensive_report.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate HTML report
        await self.generate_html_report(report)
        
        # Generate text summary
        await self.generate_text_summary(report)
        
        return report
    
    def calculate_overall_metrics(self) -> Dict[str, Any]:
        """Calculate overall performance metrics."""

        metrics = {
            "phase4_target_achieved": False,
            "sprint0_passed": False,
            "overall_accuracy": 0.0,
            "performance_rating": "Unknown",
            "robustness_score": 0.0,
            "production_readiness": "Not Ready"
        }

        # Sprint 0 validation (highest priority)
        if "sprint0_validation" in self.results and self.results["sprint0_validation"]["success"]:
            sprint0_data = self.results["sprint0_validation"]["summary"]
            metrics["sprint0_passed"] = sprint0_data["target_achieved"]
            metrics["overall_accuracy"] = sprint0_data["overall_accuracy"]
            metrics["phase4_target_achieved"] = sprint0_data["target_achieved"]

        # Accuracy metrics (fallback if Sprint 0 not run)
        elif "accuracy_tests" in self.results and self.results["accuracy_tests"]["success"]:
            accuracy_data = self.results["accuracy_tests"]["summary"]
            metrics["overall_accuracy"] = accuracy_data["overall_accuracy"]
            metrics["phase4_target_achieved"] = accuracy_data["target_achieved"]
        
        # Performance metrics
        if "performance_tests" in self.results and self.results["performance_tests"]["success"]:
            perf_data = self.results["performance_tests"]["summary"]
            throughput = perf_data["average_throughput"]
            
            if throughput >= 5.0:
                metrics["performance_rating"] = "Excellent"
            elif throughput >= 2.0:
                metrics["performance_rating"] = "Good"
            elif throughput >= 1.0:
                metrics["performance_rating"] = "Fair"
            else:
                metrics["performance_rating"] = "Poor"
        
        # Robustness score (combination of real-world and edge cases)
        robustness_scores = []
        
        if "real_world_validation" in self.results and self.results["real_world_validation"]["success"]:
            real_world_accuracy = self.results["real_world_validation"]["summary"]["overall_accuracy"]
            robustness_scores.append(real_world_accuracy)
        
        if "edge_case_tests" in self.results and self.results["edge_case_tests"]["success"]:
            edge_case_success = self.results["edge_case_tests"]["summary"]["success_rate"]
            robustness_scores.append(edge_case_success)
        
        if robustness_scores:
            metrics["robustness_score"] = sum(robustness_scores) / len(robustness_scores)
        
        # Production readiness assessment
        if (metrics["overall_accuracy"] >= 99.0 and 
            metrics["performance_rating"] in ["Excellent", "Good"] and 
            metrics["robustness_score"] >= 85.0):
            metrics["production_readiness"] = "Ready"
        elif (metrics["overall_accuracy"] >= 95.0 and 
              metrics["performance_rating"] != "Poor" and 
              metrics["robustness_score"] >= 75.0):
            metrics["production_readiness"] = "Needs Minor Improvements"
        else:
            metrics["production_readiness"] = "Needs Major Improvements"
        
        return metrics
    
    def generate_conclusions(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate test conclusions."""
        conclusions = []
        
        # Accuracy conclusion
        if metrics["phase4_target_achieved"]:
            conclusions.append(f"✅ Phase 4 SUCCESS: Achieved {metrics['overall_accuracy']:.2f}% accuracy, exceeding 99% target!")
        else:
            conclusions.append(f"❌ Phase 4 target missed: {metrics['overall_accuracy']:.2f}% accuracy (target: 99%)")
        
        # Performance conclusion
        perf_rating = metrics["performance_rating"]
        if perf_rating == "Excellent":
            conclusions.append("⚡ Excellent performance: System handles high-volume processing efficiently")
        elif perf_rating == "Good":
            conclusions.append("⚡ Good performance: System performance meets production requirements")
        elif perf_rating == "Fair":
            conclusions.append("⚠️ Fair performance: Some optimization needed for production scale")
        else:
            conclusions.append("❌ Poor performance: Significant optimization required")
        
        # Robustness conclusion
        robustness = metrics["robustness_score"]
        if robustness >= 90:
            conclusions.append("🛡️ Excellent robustness: System handles edge cases and real-world variations well")
        elif robustness >= 80:
            conclusions.append("🛡️ Good robustness: System is stable with minor edge case issues")
        else:
            conclusions.append("⚠️ Robustness needs improvement: System struggles with edge cases")
        
        # Production readiness
        readiness = metrics["production_readiness"]
        if readiness == "Ready":
            conclusions.append("🚀 PRODUCTION READY: System meets all requirements for deployment")
        elif readiness == "Needs Minor Improvements":
            conclusions.append("🔧 Minor improvements needed before production deployment")
        else:
            conclusions.append("🚫 Major improvements required before production consideration")
        
        return conclusions
    
    def generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []
        
        # Accuracy recommendations
        if metrics["overall_accuracy"] < 99.0:
            recommendations.append("🎯 Improve accuracy by fine-tuning AI validation thresholds")
            recommendations.append("📝 Add more training data for bureau-specific patterns")
            recommendations.append("🔍 Enhance OCR preprocessing for better text quality")
        
        # Performance recommendations
        if metrics["performance_rating"] in ["Fair", "Poor"]:
            recommendations.append("⚡ Optimize multi-layer extraction timeouts")
            recommendations.append("💾 Implement more aggressive result caching")
            recommendations.append("🔄 Consider horizontal scaling for high-volume processing")
        
        # Robustness recommendations
        if metrics["robustness_score"] < 85.0:
            recommendations.append("🛡️ Strengthen error correction patterns")
            recommendations.append("📚 Expand real-world test case coverage")
            recommendations.append("🔧 Improve handling of edge cases and malformed data")
        
        # General recommendations
        recommendations.extend([
            "📊 Implement continuous accuracy monitoring in production",
            "🔔 Set up alerts for accuracy degradation",
            "📈 Collect user feedback for continuous improvement",
            "🧪 Run regular regression tests with new credit report formats"
        ])
        
        return recommendations
    
    async def generate_html_report(self, report: Dict[str, Any]):
        """Generate HTML report."""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Phase 4 Parsing Accuracy Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; }}
        .metric-card {{ background: white; margin: 10px; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .success {{ border-left: 5px solid #4CAF50; }}
        .warning {{ border-left: 5px solid #FF9800; }}
        .error {{ border-left: 5px solid #F44336; }}
        .metric-value {{ font-size: 2em; font-weight: bold; }}
        .section {{ margin: 20px 0; }}
        ul {{ list-style-type: none; padding: 0; }}
        li {{ margin: 5px 0; padding: 10px; background: #f9f9f9; border-radius: 4px; }}
        .timestamp {{ color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 Phase 4 Parsing Accuracy Test Report</h1>
        <p>Advanced PDF parsing pipeline validation - Target: 99% accuracy</p>
        <p class="timestamp">Generated: {report['metadata']['test_date']}</p>
    </div>
    
    <div class="section">
        <h2>📊 Overall Results</h2>
        
        <div class="metric-card {'success' if report['overall_metrics']['phase4_target_achieved'] else 'error'}">
            <h3>🎯 Phase 4 Target Achievement</h3>
            <div class="metric-value">{report['overall_metrics']['overall_accuracy']:.2f}%</div>
            <p>Target: 99% | Status: {'✅ ACHIEVED' if report['overall_metrics']['phase4_target_achieved'] else '❌ NOT ACHIEVED'}</p>
        </div>
        
        <div class="metric-card">
            <h3>⚡ Performance Rating</h3>
            <div class="metric-value">{report['overall_metrics']['performance_rating']}</div>
        </div>
        
        <div class="metric-card">
            <h3>🛡️ Robustness Score</h3>
            <div class="metric-value">{report['overall_metrics']['robustness_score']:.1f}%</div>
        </div>
        
        <div class="metric-card {'success' if report['overall_metrics']['production_readiness'] == 'Ready' else 'warning' if 'Minor' in report['overall_metrics']['production_readiness'] else 'error'}">
            <h3>🚀 Production Readiness</h3>
            <div class="metric-value">{report['overall_metrics']['production_readiness']}</div>
        </div>
    </div>
    
    <div class="section">
        <h2>📝 Conclusions</h2>
        <ul>
        {"".join(f"<li>{conclusion}</li>" for conclusion in report['conclusions'])}
        </ul>
    </div>
    
    <div class="section">
        <h2>💡 Recommendations</h2>
        <ul>
        {"".join(f"<li>{rec}</li>" for rec in report['recommendations'])}
        </ul>
    </div>
    
    <div class="section">
        <h2>📋 Test Summary</h2>
        <div class="metric-card">
            <h3>Test Duration</h3>
            <p>{report['metadata']['test_duration_seconds']:.2f} seconds</p>
        </div>
    </div>
    
</body>
</html>
        """
        
        with open(f"{self.output_dir}/report.html", 'w') as f:
            f.write(html_content)
    
    async def generate_text_summary(self, report: Dict[str, Any]):
        """Generate text summary."""
        
        summary = f"""
PHASE 4 PARSING ACCURACY TEST SUMMARY
{'=' * 50}

Test Date: {report['metadata']['test_date']}
Duration: {report['metadata']['test_duration_seconds']:.2f} seconds
Target: 99% tradeline extraction accuracy

OVERALL RESULTS:
• Accuracy: {report['overall_metrics']['overall_accuracy']:.2f}%
• Target Achieved: {'YES ✅' if report['overall_metrics']['phase4_target_achieved'] else 'NO ❌'}
• Performance: {report['overall_metrics']['performance_rating']}
• Robustness: {report['overall_metrics']['robustness_score']:.1f}%
• Production Ready: {report['overall_metrics']['production_readiness']}

CONCLUSIONS:
"""
        
        for conclusion in report['conclusions']:
            summary += f"• {conclusion}\n"
        
        summary += "\nRECOMMendations:\n"
        for rec in report['recommendations']:
            summary += f"• {rec}\n"
        
        summary += f"\n{'=' * 50}\nDetailed results available in JSON and HTML formats.\n"
        
        with open(f"{self.output_dir}/summary.txt", 'w') as f:
            f.write(summary)


async def main():
    """Main function to run tests based on command line arguments."""
    parser = argparse.ArgumentParser(description="Run Phase 4 comprehensive testing suite")

    parser.add_argument("--sprint0", action="store_true", default=True, help="Run Sprint 0 validation (PDF vs SQL)")
    parser.add_argument("--no-sprint0", action="store_true", help="Skip Sprint 0 validation")
    parser.add_argument("--accuracy", action="store_true", default=True, help="Run accuracy tests")
    parser.add_argument("--no-accuracy", action="store_true", help="Skip accuracy tests")
    parser.add_argument("--performance", action="store_true", default=True, help="Run performance tests")
    parser.add_argument("--no-performance", action="store_true", help="Skip performance tests")
    parser.add_argument("--real-world", action="store_true", default=True, help="Run real-world validation")
    parser.add_argument("--no-real-world", action="store_true", help="Skip real-world validation")
    parser.add_argument("--edge-cases", action="store_true", default=True, help="Run edge case tests")
    parser.add_argument("--no-edge-cases", action="store_true", help="Skip edge case tests")
    parser.add_argument("--test-count", type=int, default=50, help="Number of accuracy tests to run")
    parser.add_argument("--output-dir", type=str, default="/tmp/phase4_test_results", help="Output directory")

    args = parser.parse_args()

    # Configure test execution
    run_sprint0 = args.sprint0 and not args.no_sprint0
    run_accuracy = args.accuracy and not args.no_accuracy
    run_performance = args.performance and not args.no_performance
    run_real_world = args.real_world and not args.no_real_world
    run_edge_cases = args.edge_cases and not args.no_edge_cases
    
    # Create test runner
    runner = Phase4TestRunner(output_dir=args.output_dir)
    
    # Run all tests
    results = await runner.run_all_tests(
        run_sprint0=run_sprint0,
        run_accuracy=run_accuracy,
        run_performance=run_performance,
        run_real_world=run_real_world,
        run_edge_cases=run_edge_cases,
        test_count=args.test_count
    )
    
    # Print final summary
    print("\n" + "=" * 80)
    print("🎉 PHASE 4 TESTING COMPLETE!")
    print("=" * 80)

    if results.get("sprint0_validation", {}).get("success") is not None:
        sprint0_data = results["sprint0_validation"]["summary"]
        target_met = "✅ PASSED" if sprint0_data["target_achieved"] else "❌ FAILED"
        print(f"🎯 Sprint 0 Validation: {target_met}")
        print(f"   Overall Accuracy: {sprint0_data['overall_accuracy']:.2f}%")
        print(f"   Critical Accuracy: {sprint0_data['critical_accuracy']:.2f}% (Target: 100%)")
        print(f"   Optional Accuracy: {sprint0_data['optional_accuracy']:.2f}% (Target: ≥95%)")

    elif results.get("accuracy_tests", {}).get("success"):
        accuracy = results["accuracy_tests"]["summary"]["overall_accuracy"]
        target_met = "✅ TARGET MET" if accuracy >= 99.0 else "❌ TARGET MISSED"
        print(f"📊 Overall Accuracy: {accuracy:.2f}% - {target_met}")

    print(f"📁 Full results: {args.output_dir}")
    print(f"🌐 HTML Report: {args.output_dir}/report.html")
    print("=" * 80)
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
