"""
Comprehensive testing suite for Phase 4 parsing accuracy validation.
Tests the advanced parsing pipeline to ensure 99% tradeline extraction accuracy.
"""
import asyncio
import json
import os
import pytest
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from unittest.mock import Mock, patch

import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import matplotlib.pyplot as plt
import seaborn as sns

# Import Phase 4 components
import sys
sys.path.append('/mnt/c/projects/credit-clarity/backend')

from services.advanced_parsing.multi_layer_extractor import (
    MultiLayerExtractor,
    ExtractionMethod,
    ConsolidatedResult
)
from services.advanced_parsing.bureau_specific_parser import (
    UniversalBureauParser,
    ExperianParser,
    EquifaxParser,
    TransUnionParser,
    ParsingResult
)
from services.advanced_parsing.ai_tradeline_validator import (
    AITradelineValidator,
    ValidationResult,
    TradelineData
)
from services.advanced_parsing.error_correction_system import (
    ErrorCorrectionSystem,
    ErrorType,
    CorrectionResult
)


@dataclass
class TestResult:
    """Test result for a single parsing operation."""
    test_id: str
    file_name: str
    bureau: str
    expected_tradelines: int
    extracted_tradelines: int
    accuracy: float
    processing_time: float
    method_used: str
    errors: List[str]
    validation_passed: bool
    correction_applied: bool


@dataclass
class AccuracyReport:
    """Comprehensive accuracy report."""
    total_tests: int
    passed_tests: int
    overall_accuracy: float
    bureau_accuracy: Dict[str, float]
    method_accuracy: Dict[str, float]
    average_processing_time: float
    error_rate: float
    validation_success_rate: float
    correction_success_rate: float


class TestDataGenerator:
    """Generate synthetic test PDFs for accuracy testing."""
    
    def __init__(self):
        self.bureau_templates = {
            "experian": {
                "header": "EXPERIAN CREDIT REPORT",
                "tradeline_format": "ACCOUNT: {account}\nCREDITOR: {creditor}\nBALANCE: ${balance}\nSTATUS: {status}\nOPENED: {opened}\n",
                "section_header": "CREDIT ACCOUNTS"
            },
            "equifax": {
                "header": "EQUIFAX CREDIT REPORT",
                "tradeline_format": "{creditor} - Account #{account}\nCurrent Balance: ${balance}\nAccount Status: {status}\nDate Opened: {opened}\n",
                "section_header": "ACCOUNT INFORMATION"
            },
            "transunion": {
                "header": "TRANSUNION CREDIT REPORT",
                "tradeline_format": "Company: {creditor}\nAccount Number: {account}\nBalance: ${balance}\nStatus: {status}\nDate Opened: {opened}\n",
                "section_header": "CREDIT HISTORY"
            }
        }
    
    def generate_test_pdf(
        self,
        bureau: str,
        tradeline_count: int,
        quality: str = "high"
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Generate a test PDF with known tradelines."""
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            pdf_path = tmp_file.name
        
        # Generate tradeline data
        tradelines = []
        for i in range(tradeline_count):
            tradeline = {
                "creditor": f"Test Creditor {i+1}",
                "account": f"1234567890{i:02d}",
                "balance": f"{1000 + i * 500}",
                "status": "Current" if i % 2 == 0 else "Past Due",
                "opened": f"01/0{(i % 9) + 1}/2020"
            }
            tradelines.append(tradeline)
        
        # Create PDF
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        
        # Add bureau header
        template = self.bureau_templates[bureau]
        y_position = height - 50
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y_position, template["header"])
        y_position -= 40
        
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_position, template["section_header"])
        y_position -= 30
        
        # Add tradelines
        c.setFont("Helvetica", 12)
        for tradeline in tradelines:
            tradeline_text = template["tradeline_format"].format(**tradeline)
            
            # Add quality degradation for testing
            if quality == "medium":
                # Simulate OCR errors
                tradeline_text = tradeline_text.replace("0", "O").replace("1", "l")
            elif quality == "low":
                # More severe degradation
                tradeline_text = tradeline_text.replace("0", "O").replace("1", "l").replace("5", "S")
            
            lines = tradeline_text.split('\n')
            for line in lines:
                if line.strip():
                    c.drawString(50, y_position, line)
                    y_position -= 15
            
            y_position -= 10
            
            # New page if needed
            if y_position < 100:
                c.showPage()
                y_position = height - 50
        
        c.save()
        return pdf_path, tradelines


class ParsingAccuracyTester:
    """Main testing class for parsing accuracy validation."""
    
    def __init__(self):
        self.extractor = MultiLayerExtractor()
        self.parser = UniversalBureauParser()
        self.validator = AITradelineValidator()
        self.corrector = ErrorCorrectionSystem()
        self.test_generator = TestDataGenerator()
        self.results: List[TestResult] = []
    
    async def run_comprehensive_test_suite(
        self,
        test_count: int = 100,
        output_dir: str = "/tmp/parsing_accuracy_tests"
    ) -> AccuracyReport:
        """Run comprehensive parsing accuracy tests."""
        
        print(f"🧪 Starting comprehensive parsing accuracy test suite...")
        print(f"📊 Running {test_count} tests across all bureaus and quality levels")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Test configurations
        bureaus = ["experian", "equifax", "transunion"]
        quality_levels = ["high", "medium", "low"]
        tradeline_counts = [3, 5, 10, 15, 20]
        
        test_id = 0
        total_tests = len(bureaus) * len(quality_levels) * len(tradeline_counts) * 2
        
        print(f"📈 Total test combinations: {total_tests}")
        
        for bureau in bureaus:
            for quality in quality_levels:
                for tradeline_count in tradeline_counts:
                    # Run 2 tests per configuration for statistical significance
                    for iteration in range(2):
                        test_id += 1
                        print(f"🔄 Running test {test_id}/{total_tests}: {bureau}/{quality}/{tradeline_count} tradelines")
                        
                        result = await self.run_single_test(
                            test_id=f"{bureau}_{quality}_{tradeline_count}_{iteration}",
                            bureau=bureau,
                            tradeline_count=tradeline_count,
                            quality=quality
                        )
                        
                        self.results.append(result)
                        
                        # Progress update
                        if test_id % 10 == 0:
                            current_accuracy = sum(r.accuracy for r in self.results) / len(self.results)
                            print(f"📊 Progress: {test_id}/{total_tests} - Current avg accuracy: {current_accuracy:.2f}%")
        
        # Generate comprehensive report
        report = self.generate_accuracy_report()
        await self.save_detailed_results(output_dir, report)
        
        return report
    
    async def run_single_test(
        self,
        test_id: str,
        bureau: str,
        tradeline_count: int,
        quality: str = "high"
    ) -> TestResult:
        """Run a single parsing accuracy test."""
        
        start_time = time.time()
        errors = []
        validation_passed = False
        correction_applied = False
        
        try:
            # Generate test PDF
            pdf_path, expected_tradelines = self.test_generator.generate_test_pdf(
                bureau=bureau,
                tradeline_count=tradeline_count,
                quality=quality
            )
            
            try:
                # Step 1: Multi-layer extraction
                extraction_result = await self.extractor.extract_text_multi_layer(
                    pdf_path=pdf_path,
                    use_ai=True,
                    quality_threshold=0.8
                )
                
                if not extraction_result.success:
                    errors.append(f"Extraction failed: {extraction_result.error}")
                    raise Exception("Extraction failed")
                
                # Step 2: Bureau-specific parsing
                parsing_result = self.parser.get_best_result(extraction_result.consolidated_text)
                
                if not parsing_result.success:
                    errors.append(f"Parsing failed: {parsing_result.error}")
                    raise Exception("Parsing failed")
                
                # Step 3: AI validation
                validated_tradelines = []
                for tradeline_data in parsing_result.tradelines:
                    validation_result = await self.validator.validate_and_correct_tradeline(
                        tradeline=tradeline_data,
                        context_text=extraction_result.consolidated_text[:1000]
                    )
                    
                    if validation_result.is_valid:
                        validated_tradelines.append(validation_result.corrected_tradeline or tradeline_data)
                        validation_passed = True
                
                # Step 4: Error correction if needed
                if parsing_result.confidence < 0.9:
                    corrected_result, corrections = await self.corrector.detect_and_correct_errors(
                        parsing_result=parsing_result,
                        original_text=extraction_result.consolidated_text,
                        pdf_path=pdf_path
                    )
                    
                    if corrections:
                        correction_applied = True
                        validated_tradelines = corrected_result.tradelines
                
                # Calculate accuracy
                extracted_count = len(validated_tradelines)
                expected_count = len(expected_tradelines)
                
                # Match extracted tradelines to expected ones
                matches = self.match_tradelines(expected_tradelines, validated_tradelines)
                accuracy = (matches / expected_count) * 100 if expected_count > 0 else 0
                
                processing_time = time.time() - start_time
                
                return TestResult(
                    test_id=test_id,
                    file_name=f"{test_id}.pdf",
                    bureau=bureau,
                    expected_tradelines=expected_count,
                    extracted_tradelines=extracted_count,
                    accuracy=accuracy,
                    processing_time=processing_time,
                    method_used=extraction_result.best_method.value if extraction_result.best_method else "unknown",
                    errors=errors,
                    validation_passed=validation_passed,
                    correction_applied=correction_applied
                )
                
            finally:
                # Cleanup temporary file
                try:
                    os.unlink(pdf_path)
                except:
                    pass
                    
        except Exception as e:
            processing_time = time.time() - start_time
            errors.append(str(e))
            
            return TestResult(
                test_id=test_id,
                file_name=f"{test_id}.pdf",
                bureau=bureau,
                expected_tradelines=tradeline_count,
                extracted_tradelines=0,
                accuracy=0.0,
                processing_time=processing_time,
                method_used="failed",
                errors=errors,
                validation_passed=False,
                correction_applied=False
            )
    
    def match_tradelines(
        self,
        expected: List[Dict[str, Any]],
        extracted: List[TradelineData]
    ) -> int:
        """Match extracted tradelines to expected ones."""
        matches = 0
        
        for exp_tradeline in expected:
            for ext_tradeline in extracted:
                # Simple matching based on creditor name and account
                exp_creditor = exp_tradeline.get("creditor", "").lower()
                ext_creditor = getattr(ext_tradeline, "creditor_name", "").lower()
                
                exp_account = exp_tradeline.get("account", "")
                ext_account = getattr(ext_tradeline, "account_number", "")
                
                # Fuzzy matching for OCR errors
                if (self.fuzzy_match(exp_creditor, ext_creditor, threshold=0.8) and
                    self.fuzzy_match(exp_account, ext_account, threshold=0.7)):
                    matches += 1
                    break
        
        return matches
    
    def fuzzy_match(self, str1: str, str2: str, threshold: float = 0.8) -> bool:
        """Simple fuzzy string matching."""
        if not str1 or not str2:
            return False
        
        # Simple character overlap ratio
        str1_set = set(str1.lower())
        str2_set = set(str2.lower())
        
        if not str1_set or not str2_set:
            return False
        
        overlap = len(str1_set.intersection(str2_set))
        union = len(str1_set.union(str2_set))
        
        similarity = overlap / union if union > 0 else 0
        return similarity >= threshold
    
    def generate_accuracy_report(self) -> AccuracyReport:
        """Generate comprehensive accuracy report."""
        
        if not self.results:
            return AccuracyReport(
                total_tests=0,
                passed_tests=0,
                overall_accuracy=0.0,
                bureau_accuracy={},
                method_accuracy={},
                average_processing_time=0.0,
                error_rate=0.0,
                validation_success_rate=0.0,
                correction_success_rate=0.0
            )
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.accuracy >= 95.0)  # 95% threshold for "passed"
        overall_accuracy = sum(r.accuracy for r in self.results) / total_tests
        
        # Bureau accuracy breakdown
        bureau_accuracy = {}
        for bureau in ["experian", "equifax", "transunion"]:
            bureau_results = [r for r in self.results if r.bureau == bureau]
            if bureau_results:
                bureau_accuracy[bureau] = sum(r.accuracy for r in bureau_results) / len(bureau_results)
        
        # Method accuracy breakdown
        method_accuracy = {}
        methods = set(r.method_used for r in self.results)
        for method in methods:
            method_results = [r for r in self.results if r.method_used == method]
            if method_results:
                method_accuracy[method] = sum(r.accuracy for r in method_results) / len(method_results)
        
        average_processing_time = sum(r.processing_time for r in self.results) / total_tests
        error_rate = sum(1 for r in self.results if r.errors) / total_tests * 100
        validation_success_rate = sum(1 for r in self.results if r.validation_passed) / total_tests * 100
        correction_success_rate = sum(1 for r in self.results if r.correction_applied) / total_tests * 100
        
        return AccuracyReport(
            total_tests=total_tests,
            passed_tests=passed_tests,
            overall_accuracy=overall_accuracy,
            bureau_accuracy=bureau_accuracy,
            method_accuracy=method_accuracy,
            average_processing_time=average_processing_time,
            error_rate=error_rate,
            validation_success_rate=validation_success_rate,
            correction_success_rate=correction_success_rate
        )
    
    async def save_detailed_results(self, output_dir: str, report: AccuracyReport):
        """Save detailed test results and generate visualizations."""
        
        # Save raw results
        results_data = [asdict(result) for result in self.results]
        with open(f"{output_dir}/test_results.json", 'w') as f:
            json.dump(results_data, f, indent=2)
        
        # Save summary report
        with open(f"{output_dir}/accuracy_report.json", 'w') as f:
            json.dump(asdict(report), f, indent=2)
        
        # Generate CSV for further analysis
        df = pd.DataFrame(results_data)
        df.to_csv(f"{output_dir}/test_results.csv", index=False)
        
        # Generate visualizations
        await self.generate_visualizations(df, output_dir)
        
        # Generate text report
        await self.generate_text_report(report, output_dir)
    
    async def generate_visualizations(self, df: pd.DataFrame, output_dir: str):
        """Generate accuracy visualization charts."""
        
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Phase 4 Parsing Accuracy Test Results', fontsize=16, fontweight='bold')
        
        # 1. Overall accuracy distribution
        axes[0, 0].hist(df['accuracy'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        axes[0, 0].axvline(df['accuracy'].mean(), color='red', linestyle='--', label=f'Mean: {df["accuracy"].mean():.1f}%')
        axes[0, 0].axvline(99, color='green', linestyle='-', label='Target: 99%')
        axes[0, 0].set_xlabel('Accuracy (%)')
        axes[0, 0].set_ylabel('Number of Tests')
        axes[0, 0].set_title('Accuracy Distribution')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Bureau comparison
        bureau_accuracy = df.groupby('bureau')['accuracy'].mean().sort_values(ascending=False)
        bars = axes[0, 1].bar(bureau_accuracy.index, bureau_accuracy.values, color=['#ff9999', '#66b3ff', '#99ff99'])
        axes[0, 1].axhline(99, color='green', linestyle='--', label='Target: 99%')
        axes[0, 1].set_xlabel('Credit Bureau')
        axes[0, 1].set_ylabel('Average Accuracy (%)')
        axes[0, 1].set_title('Accuracy by Credit Bureau')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, value in zip(bars, bureau_accuracy.values):
            axes[0, 1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                           f'{value:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        # 3. Processing time vs accuracy
        scatter = axes[1, 0].scatter(df['processing_time'], df['accuracy'], 
                                    c=df['extracted_tradelines'], cmap='viridis', alpha=0.6)
        axes[1, 0].set_xlabel('Processing Time (seconds)')
        axes[1, 0].set_ylabel('Accuracy (%)')
        axes[1, 0].set_title('Processing Time vs Accuracy')
        axes[1, 0].grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=axes[1, 0], label='Tradelines Extracted')
        
        # 4. Success rate by tradeline count
        tradeline_success = df.groupby('expected_tradelines').agg({
            'accuracy': 'mean',
            'test_id': 'count'
        }).rename(columns={'test_id': 'test_count'})
        
        bars = axes[1, 1].bar(tradeline_success.index, tradeline_success['accuracy'], 
                             color='lightcoral', alpha=0.7)
        axes[1, 1].axhline(99, color='green', linestyle='--', label='Target: 99%')
        axes[1, 1].set_xlabel('Expected Tradelines')
        axes[1, 1].set_ylabel('Average Accuracy (%)')
        axes[1, 1].set_title('Accuracy vs Tradeline Count')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        # Add test count labels
        for bar, count in zip(bars, tradeline_success['test_count']):
            axes[1, 1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                           f'n={count}', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/accuracy_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Generate detailed heatmap
        self.generate_heatmap(df, output_dir)
    
    def generate_heatmap(self, df: pd.DataFrame, output_dir: str):
        """Generate accuracy heatmap by bureau and quality."""
        
        # Create pivot table for heatmap
        quality_map = {'high': 'High Quality', 'medium': 'Medium Quality', 'low': 'Low Quality'}
        df['quality'] = df['test_id'].str.extract(r'_(high|medium|low)_').fillna('unknown')[0]
        df['quality_label'] = df['quality'].map(quality_map).fillna('Unknown')
        
        pivot_table = df.pivot_table(
            values='accuracy',
            index='quality_label',
            columns='bureau',
            aggfunc='mean'
        )
        
        plt.figure(figsize=(10, 6))
        sns.heatmap(
            pivot_table,
            annot=True,
            fmt='.1f',
            cmap='RdYlGn',
            center=95,
            vmin=80,
            vmax=100,
            cbar_kws={'label': 'Accuracy (%)'},
            linewidths=0.5
        )
        plt.title('Parsing Accuracy Heatmap\n(Bureau vs Quality Level)', fontsize=14, fontweight='bold')
        plt.xlabel('Credit Bureau', fontweight='bold')
        plt.ylabel('PDF Quality Level', fontweight='bold')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/accuracy_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    async def generate_text_report(self, report: AccuracyReport, output_dir: str):
        """Generate comprehensive text report."""
        
        report_content = f"""
# Phase 4 Parsing Accuracy Test Report
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary
- **Overall Accuracy**: {report.overall_accuracy:.2f}%
- **Target Achievement**: {'✅ PASSED' if report.overall_accuracy >= 99.0 else '❌ NEEDS IMPROVEMENT'}
- **Tests Passed**: {report.passed_tests}/{report.total_tests} ({report.passed_tests/report.total_tests*100:.1f}%)
- **Average Processing Time**: {report.average_processing_time:.2f}s
- **Error Rate**: {report.error_rate:.1f}%

## Detailed Results

### Bureau-Specific Accuracy
"""
        
        for bureau, accuracy in sorted(report.bureau_accuracy.items(), key=lambda x: x[1], reverse=True):
            status = "✅ PASSED" if accuracy >= 99.0 else "⚠️ NEEDS IMPROVEMENT"
            report_content += f"- **{bureau.title()}**: {accuracy:.2f}% {status}\n"
        
        report_content += f"""
### Extraction Method Performance
"""
        
        for method, accuracy in sorted(report.method_accuracy.items(), key=lambda x: x[1], reverse=True):
            report_content += f"- **{method}**: {accuracy:.2f}%\n"
        
        report_content += f"""
### Performance Metrics
- **Validation Success Rate**: {report.validation_success_rate:.1f}%
- **Error Correction Applied**: {report.correction_success_rate:.1f}%
- **Processing Speed**: {1/report.average_processing_time:.1f} documents/second

### Quality Assessment
"""
        
        if report.overall_accuracy >= 99.0:
            report_content += """
🎉 **EXCELLENT**: Phase 4 parsing pipeline meets the 99% accuracy target!

**Key Strengths**:
- Multi-layer extraction provides robust text recovery
- Bureau-specific parsers handle format variations effectively  
- AI validation catches and corrects parsing errors
- Error correction system provides intelligent fallbacks

**Recommendations**:
- Deploy to production environment
- Monitor real-world performance
- Collect user feedback for continuous improvement
"""
        elif report.overall_accuracy >= 95.0:
            report_content += """
⚠️ **GOOD**: Close to target but needs optimization.

**Areas for Improvement**:
- Fine-tune AI validation thresholds
- Enhance error correction patterns
- Optimize OCR preprocessing
- Add more training data for edge cases
"""
        else:
            report_content += """
❌ **NEEDS SIGNIFICANT IMPROVEMENT**: Major issues detected.

**Critical Issues**:
- Review multi-layer extraction configuration
- Check bureau parser regex patterns  
- Validate AI model performance
- Investigate error correction logic
"""
        
        report_content += f"""
### Test Configuration
- **Total Test Cases**: {report.total_tests}
- **Bureau Coverage**: Experian, Equifax, TransUnion
- **Quality Levels**: High, Medium, Low
- **Tradeline Counts**: 3, 5, 10, 15, 20
- **Validation Methods**: AI-powered + Rule-based

### Files Generated
- `test_results.json` - Raw test data
- `test_results.csv` - Spreadsheet format
- `accuracy_analysis.png` - Statistical charts
- `accuracy_heatmap.png` - Bureau/quality heatmap
- `accuracy_report.txt` - This report

---
**Phase 4 Testing Suite v1.0**  
Credit Clarity Advanced Parsing Pipeline
"""
        
        with open(f"{output_dir}/accuracy_report.txt", 'w') as f:
            f.write(report_content)


# Performance benchmarking functions
class PerformanceBenchmark:
    """Performance benchmarking for parsing pipeline."""
    
    def __init__(self):
        self.tester = ParsingAccuracyTester()
    
    async def run_performance_benchmark(
        self,
        file_sizes: List[int] = [1, 5, 10, 20, 50],
        concurrent_users: List[int] = [1, 5, 10, 20],
        output_dir: str = "/tmp/performance_benchmark"
    ):
        """Run performance benchmark tests."""
        
        os.makedirs(output_dir, exist_ok=True)
        results = []
        
        for file_size in file_sizes:
            for user_count in concurrent_users:
                print(f"🚀 Benchmarking: {file_size}MB files, {user_count} concurrent users")
                
                # Create test files
                test_files = []
                for i in range(user_count):
                    tradeline_count = max(3, file_size * 2)  # More tradelines for larger files
                    pdf_path, _ = self.tester.test_generator.generate_test_pdf(
                        bureau="experian",
                        tradeline_count=tradeline_count,
                        quality="high"
                    )
                    test_files.append(pdf_path)
                
                # Concurrent processing
                start_time = time.time()
                tasks = []
                
                for i, pdf_path in enumerate(test_files):
                    task = self.tester.run_single_test(
                        test_id=f"perf_{file_size}mb_{user_count}users_{i}",
                        bureau="experian",
                        tradeline_count=tradeline_count,
                        quality="high"
                    )
                    tasks.append(task)
                
                # Run concurrently
                test_results = await asyncio.gather(*tasks)
                total_time = time.time() - start_time
                
                # Calculate metrics
                avg_accuracy = sum(r.accuracy for r in test_results) / len(test_results)
                avg_processing_time = sum(r.processing_time for r in test_results) / len(test_results)
                throughput = len(test_results) / total_time
                
                result = {
                    "file_size_mb": file_size,
                    "concurrent_users": user_count,
                    "total_time": total_time,
                    "avg_accuracy": avg_accuracy,
                    "avg_processing_time": avg_processing_time,
                    "throughput": throughput,
                    "errors": sum(1 for r in test_results if r.errors)
                }
                
                results.append(result)
                print(f"✅ Result: {avg_accuracy:.1f}% accuracy, {throughput:.2f} docs/sec")
                
                # Cleanup
                for pdf_path in test_files:
                    try:
                        os.unlink(pdf_path)
                    except:
                        pass
        
        # Save benchmark results
        with open(f"{output_dir}/performance_benchmark.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        return results


# Main test execution functions
async def run_accuracy_tests():
    """Main function to run accuracy tests."""
    tester = ParsingAccuracyTester()
    report = await tester.run_comprehensive_test_suite(test_count=100)
    
    print("\n" + "="*80)
    print("🎯 PHASE 4 PARSING ACCURACY TEST RESULTS")
    print("="*80)
    print(f"Overall Accuracy: {report.overall_accuracy:.2f}%")
    print(f"Target Achievement: {'✅ PASSED' if report.overall_accuracy >= 99.0 else '❌ NEEDS IMPROVEMENT'}")
    print(f"Tests Passed: {report.passed_tests}/{report.total_tests}")
    print(f"Average Processing Time: {report.average_processing_time:.2f}s")
    print("="*80)
    
    return report


async def run_performance_tests():
    """Main function to run performance tests."""
    benchmark = PerformanceBenchmark()
    results = await benchmark.run_performance_benchmark()
    
    print("\n" + "="*80)
    print("⚡ PERFORMANCE BENCHMARK RESULTS")
    print("="*80)
    
    for result in results:
        print(f"📊 {result['file_size_mb']}MB, {result['concurrent_users']} users: "
              f"{result['throughput']:.2f} docs/sec, {result['avg_accuracy']:.1f}% accuracy")
    
    print("="*80)
    return results


if __name__ == "__main__":
    # Run both accuracy and performance tests
    async def main():
        print("🚀 Starting Phase 4 Comprehensive Testing Suite")
        
        # Accuracy tests
        accuracy_report = await run_accuracy_tests()
        
        # Performance tests  
        performance_results = await run_performance_tests()
        
        print("\n✅ All tests completed! Check output directories for detailed results.")
        
        return accuracy_report, performance_results
    
    # Run tests
    asyncio.run(main())