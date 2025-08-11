"""
Real-world validation tests for Phase 4 parsing accuracy.
Tests against actual credit report patterns and edge cases.
"""
import asyncio
import json
import os
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import tempfile
import re

# Import Phase 4 components
import sys
sys.path.append('/mnt/c/projects/credit-clarity/backend')

from services.advanced_parsing.multi_layer_extractor import MultiLayerExtractor
from services.advanced_parsing.bureau_specific_parser import UniversalBureauParser
from services.advanced_parsing.ai_tradeline_validator import AITradelineValidator
from services.advanced_parsing.error_correction_system import ErrorCorrectionSystem


@dataclass
class RealWorldTestCase:
    """Real-world test case definition."""
    name: str
    description: str
    bureau: str
    text_sample: str
    expected_tradelines: List[Dict[str, Any]]
    difficulty_level: str  # easy, medium, hard, extreme
    common_issues: List[str]


class RealWorldValidator:
    """Validator for real-world credit report patterns."""
    
    def __init__(self):
        self.extractor = MultiLayerExtractor()
        self.parser = UniversalBureauParser()
        self.validator = AITradelineValidator()
        self.corrector = ErrorCorrectionSystem()
        
        # Load real-world test cases
        self.test_cases = self.load_test_cases()
    
    def load_test_cases(self) -> List[RealWorldTestCase]:
        """Load comprehensive real-world test cases."""
        return [
            # Experian test cases
            RealWorldTestCase(
                name="experian_clean_format",
                description="Clean Experian format with standard tradelines",
                bureau="experian",
                text_sample="""
EXPERIAN CREDIT REPORT
Consumer Credit Report for JOHN DOE
Date of Birth: 01/01/1980
SSN: XXX-XX-1234

CREDIT ACCOUNTS

CAPITAL ONE BANK USA N.A.
Account Number: 4111111111111111
Date Opened: 01/15/2020
Account Type: Credit Card
Status: Current
Credit Limit: $5,000
Current Balance: $1,245
Monthly Payment: $25
Last Payment: 02/15/2024

CHASE BANK USA N.A.
Account Number: 4222222222222222
Date Opened: 06/10/2018
Account Type: Credit Card
Status: Current
Credit Limit: $8,000
Current Balance: $2,180
Monthly Payment: $50
Last Payment: 02/10/2024

WELLS FARGO AUTO
Account Number: WF12345678
Date Opened: 03/20/2021
Account Type: Auto Loan
Status: Current
Original Loan Amount: $25,000
Current Balance: $18,420
Monthly Payment: $425
Last Payment: 02/20/2024
                """,
                expected_tradelines=[
                    {
                        "creditor_name": "CAPITAL ONE BANK USA N.A.",
                        "account_number": "4111111111111111",
                        "account_balance": "$1,245",
                        "credit_limit": "$5,000",
                        "monthly_payment": "$25",
                        "date_opened": "01/15/2020",
                        "account_type": "Credit Card",
                        "account_status": "Current"
                    },
                    {
                        "creditor_name": "CHASE BANK USA N.A.",
                        "account_number": "4222222222222222",
                        "account_balance": "$2,180",
                        "credit_limit": "$8,000",
                        "monthly_payment": "$50",
                        "date_opened": "06/10/2018",
                        "account_type": "Credit Card",
                        "account_status": "Current"
                    },
                    {
                        "creditor_name": "WELLS FARGO AUTO",
                        "account_number": "WF12345678",
                        "account_balance": "$18,420",
                        "credit_limit": "$25,000",
                        "monthly_payment": "$425",
                        "date_opened": "03/20/2021",
                        "account_type": "Auto Loan",
                        "account_status": "Current"
                    }
                ],
                difficulty_level="easy",
                common_issues=[]
            ),
            
            RealWorldTestCase(
                name="experian_negative_accounts",
                description="Experian report with negative accounts and collections",
                bureau="experian",
                text_sample="""
EXPERIAN CREDIT REPORT

NEGATIVE CREDIT INFORMATION

DISCOVER BANK
Account Number: 6011111111111117
Date Opened: 08/12/2019
Account Type: Credit Card
Status: CHARGE OFF
Date of Status: 12/15/2023
Credit Limit: $3,500
Balance: $3,247
Amount Past Due: $3,247
Last Payment: 10/15/2023

MIDLAND FUNDING LLC
Account Number: MF987654321
Date Opened: 01/20/2024
Account Type: Collection
Status: COLLECTION
Original Creditor: BEST BUY
Balance: $1,892
Date of Status: 01/20/2024

SYNCHRONY BANK/AMAZON
Account Number: 5555555555554444
Date Opened: 05/01/2020
Account Type: Credit Card
Status: 60 DAYS PAST DUE
Credit Limit: $2,000
Current Balance: $1,750
Amount Past Due: $125
Monthly Payment: $45
Last Payment: 12/15/2023
                """,
                expected_tradelines=[
                    {
                        "creditor_name": "DISCOVER BANK",
                        "account_number": "6011111111111117",
                        "account_balance": "$3,247",
                        "credit_limit": "$3,500",
                        "account_status": "CHARGE OFF",
                        "is_negative": True
                    },
                    {
                        "creditor_name": "MIDLAND FUNDING LLC",
                        "account_number": "MF987654321",
                        "account_balance": "$1,892",
                        "account_status": "COLLECTION",
                        "is_negative": True
                    },
                    {
                        "creditor_name": "SYNCHRONY BANK/AMAZON",
                        "account_number": "5555555555554444",
                        "account_balance": "$1,750",
                        "credit_limit": "$2,000",
                        "account_status": "60 DAYS PAST DUE",
                        "is_negative": True
                    }
                ],
                difficulty_level="medium",
                common_issues=["negative_accounts", "collections", "charge_offs"]
            ),
            
            # Equifax test cases
            RealWorldTestCase(
                name="equifax_mixed_format",
                description="Equifax report with mixed account types and formats",
                bureau="equifax",
                text_sample="""
EQUIFAX CREDIT REPORT
Credit File for: JANE SMITH
Report Date: 03/01/2024

ACCOUNT INFORMATION

AMERICAN EXPRESS COMPANY - Account #: 371449635398431
Account Type: Charge Card | Date Opened: 09/15/2019
Account Status: Current | Credit Limit: No Preset Limit
Current Balance: $4,567 | Last Payment: $2,500 on 02/28/2024
Payment History: Never Late

BANK OF AMERICA, N.A. - Account #: 4400000000000008
Account Type: Credit Card | Date Opened: 04/22/2017
Account Status: Current | Credit Limit: $12,000
Current Balance: $3,234 | Monthly Payment: $75
Payment History: 30 days late 2 times

TOYOTA MOTOR CREDIT - Account #: TMCC56789012
Account Type: Auto Installment | Date Opened: 11/10/2022
Account Status: Current | Original Amount: $32,500
Current Balance: $26,890 | Monthly Payment: $545
Payment History: Never Late

NAVIENT SOLUTIONS - Account #: NAV123456789
Account Type: Student Loan | Date Opened: 08/25/2016
Account Status: Current | Original Amount: $45,000
Current Balance: $38,750 | Monthly Payment: $385
Payment History: 30 days late 1 time
                """,
                expected_tradelines=[
                    {
                        "creditor_name": "AMERICAN EXPRESS COMPANY",
                        "account_number": "371449635398431",
                        "account_balance": "$4,567",
                        "account_type": "Charge Card",
                        "account_status": "Current"
                    },
                    {
                        "creditor_name": "BANK OF AMERICA, N.A.",
                        "account_number": "4400000000000008", 
                        "account_balance": "$3,234",
                        "credit_limit": "$12,000",
                        "account_type": "Credit Card",
                        "account_status": "Current"
                    },
                    {
                        "creditor_name": "TOYOTA MOTOR CREDIT",
                        "account_number": "TMCC56789012",
                        "account_balance": "$26,890",
                        "account_type": "Auto Installment",
                        "account_status": "Current"
                    },
                    {
                        "creditor_name": "NAVIENT SOLUTIONS",
                        "account_number": "NAV123456789",
                        "account_balance": "$38,750",
                        "account_type": "Student Loan",
                        "account_status": "Current"
                    }
                ],
                difficulty_level="medium",
                common_issues=["mixed_formats", "payment_history"]
            ),
            
            # TransUnion test cases
            RealWorldTestCase(
                name="transunion_complex_format",
                description="TransUnion report with complex formatting and special characters",
                bureau="transunion",
                text_sample="""
TransUnion Credit Report
Report for: MICHAEL JOHNSON
Date: March 1, 2024

CREDIT HISTORY

Company: CITIBANK, N.A.
Account Number: 5424********1234
Balance: $2,845.67
Status: Current
Date Opened: 12/03/2018
Credit Limit: $7,500.00
Type: Revolving
Last Activity: 02/28/2024

Company: U.S. BANK NATIONAL ASSOCIATION
Account Number: 4530********5678  
Balance: $856.23
Status: Current - 30 Days Past Due
Date Opened: 07/18/2020
Credit Limit: $4,000.00
Type: Revolving
Last Activity: 01/15/2024

Company: HONDA FINANCIAL SERVICES
Account Number: HFS-9876543210
Balance: $15,234.89
Status: Current
Date Opened: 02/14/2023
Original Amount: $28,500.00
Type: Installment - Auto
Monthly Payment: $485.00
Last Activity: 02/20/2024

Company: NELNET, INC.
Account Number: NLN*1122334455
Balance: $22,450.00
Status: Deferred - In School
Date Opened: 08/30/2019
Original Amount: $35,000.00
Type: Student Loan
Monthly Payment: $0.00
Last Activity: 08/30/2023
                """,
                expected_tradelines=[
                    {
                        "creditor_name": "CITIBANK, N.A.",
                        "account_number": "5424********1234",
                        "account_balance": "$2,845.67",
                        "credit_limit": "$7,500.00",
                        "account_status": "Current"
                    },
                    {
                        "creditor_name": "U.S. BANK NATIONAL ASSOCIATION",
                        "account_number": "4530********5678",
                        "account_balance": "$856.23",
                        "credit_limit": "$4,000.00",
                        "account_status": "Current - 30 Days Past Due"
                    },
                    {
                        "creditor_name": "HONDA FINANCIAL SERVICES",
                        "account_number": "HFS-9876543210",
                        "account_balance": "$15,234.89",
                        "account_type": "Installment - Auto",
                        "account_status": "Current"
                    },
                    {
                        "creditor_name": "NELNET, INC.",
                        "account_number": "NLN*1122334455",
                        "account_balance": "$22,450.00",
                        "account_type": "Student Loan",
                        "account_status": "Deferred - In School"
                    }
                ],
                difficulty_level="hard",
                common_issues=["masked_accounts", "special_characters", "complex_status"]
            ),
            
            # OCR Error Cases
            RealWorldTestCase(
                name="ocr_errors_case",
                description="Text with common OCR errors and misreadings",
                bureau="experian",
                text_sample="""
EXPERIAN CREDIT REP0RT

CREDIT ACC0UNTS

CAPITAl 0NE BANK USA N.A.
Acc0unt Number: 4lllllllllllllll
Date 0pened: 0l/l5/2020
Acc0unt Type: Credit Card
Status: Current
Credit limit: $5,O00
Current Balance: $l,245
M0nthly Payment: $25

CHASE BANK USA N.A.  
Acc0unt Number: 4222222222222Z22
Date 0pened: 06/l0/20l8
Acc0unt Type: Credit Card
Status: Current
Credit limit: $8,O00
Current Balance: $2,l80
M0nthly Payment: $50

WEllS FARG0 AUT0
Acc0unt Number: WFl2345678
Date 0pened: 03/20/202l
Acc0unt Type: Aut0 l0an
Status: Current
0riginal l0an Am0unt: $25,O00
Current Balance: $l8,42O
M0nthly Payment: $425
                """,
                expected_tradelines=[
                    {
                        "creditor_name": "CAPITAL ONE BANK USA N.A.",
                        "account_number": "4111111111111111",
                        "account_balance": "$1,245",
                        "credit_limit": "$5,000"
                    },
                    {
                        "creditor_name": "CHASE BANK USA N.A.",
                        "account_number": "4222222222222222",
                        "account_balance": "$2,180",
                        "credit_limit": "$8,000"
                    },
                    {
                        "creditor_name": "WELLS FARGO AUTO",
                        "account_number": "WF12345678",
                        "account_balance": "$18,420",
                        "credit_limit": "$25,000"
                    }
                ],
                difficulty_level="extreme",
                common_issues=["ocr_errors", "character_substitution", "0_O_confusion"]
            ),
            
            # Edge Case: Minimal Information
            RealWorldTestCase(
                name="minimal_information",
                description="Tradeline with minimal available information",
                bureau="equifax",
                text_sample="""
EQUIFAX CREDIT REPORT

ACCOUNT INFORMATION

UNKNOWN CREDITOR - Account #: ****************1234
Account Status: Closed | Balance: $0
Date Opened: Unknown | Last Activity: 01/2024

MEDICAL COLLECTIONS - Account #: MC789456123
Account Status: Collection | Balance: $567
Original Creditor: MEMORIAL HOSPITAL
Date Opened: 12/2023

AUTHORIZED USER ACCOUNT
PRIMARY: SMITH, JOHN
Account Status: Current | Balance: $1,245
Account Type: Credit Card
                """,
                expected_tradelines=[
                    {
                        "creditor_name": "UNKNOWN CREDITOR",
                        "account_number": "****************1234",
                        "account_balance": "$0",
                        "account_status": "Closed"
                    },
                    {
                        "creditor_name": "MEDICAL COLLECTIONS",
                        "account_number": "MC789456123",
                        "account_balance": "$567",
                        "account_status": "Collection"
                    }
                ],
                difficulty_level="extreme",
                common_issues=["minimal_data", "unknown_fields", "authorized_user"]
            )
        ]
    
    async def validate_real_world_cases(self) -> Dict[str, Any]:
        """Validate all real-world test cases."""
        print("🔍 Running Real-World Validation Tests...")
        
        results = []
        total_accuracy = 0
        
        for i, test_case in enumerate(self.test_cases, 1):
            print(f"🧪 Test {i}/{len(self.test_cases)}: {test_case.name} ({test_case.difficulty_level})")
            
            start_time = time.time()
            result = await self.validate_single_case(test_case)
            processing_time = time.time() - start_time
            
            result["processing_time"] = processing_time
            results.append(result)
            total_accuracy += result["accuracy"]
            
            print(f"   ✅ Accuracy: {result['accuracy']:.1f}% | Time: {processing_time:.2f}s")
        
        overall_accuracy = total_accuracy / len(self.test_cases)
        
        report = {
            "overall_accuracy": overall_accuracy,
            "total_cases": len(self.test_cases),
            "results": results,
            "difficulty_breakdown": self.get_difficulty_breakdown(results),
            "issue_analysis": self.analyze_common_issues(results)
        }
        
        print(f"\n📊 Real-World Validation Results:")
        print(f"   Overall Accuracy: {overall_accuracy:.2f}%")
        print(f"   Cases Passed: {sum(1 for r in results if r['accuracy'] >= 90)}/{len(self.test_cases)}")
        
        return report
    
    async def validate_single_case(self, test_case: RealWorldTestCase) -> Dict[str, Any]:
        """Validate a single real-world test case."""
        
        try:
            # Parse the text sample directly (simulating extracted text)
            parsing_result = self.parser.get_best_result(test_case.text_sample)
            
            if not parsing_result.success:
                # Try error correction
                corrected_result, corrections = await self.corrector.detect_and_correct_errors(
                    parsing_result=parsing_result,
                    original_text=test_case.text_sample
                )
                parsing_result = corrected_result
            
            # Validate extracted tradelines
            validated_tradelines = []
            for tradeline_data in parsing_result.tradelines:
                validation_result = await self.validator.validate_and_correct_tradeline(
                    tradeline=tradeline_data,
                    context_text=test_case.text_sample[:1000]
                )
                
                if validation_result.is_valid:
                    validated_tradelines.append(validation_result.corrected_tradeline or tradeline_data)
            
            # Calculate accuracy by matching expected vs extracted
            matches = self.match_real_world_tradelines(
                expected=test_case.expected_tradelines,
                extracted=validated_tradelines
            )
            
            accuracy = (matches / len(test_case.expected_tradelines)) * 100 if test_case.expected_tradelines else 0
            
            return {
                "test_name": test_case.name,
                "bureau": test_case.bureau,
                "difficulty": test_case.difficulty_level,
                "expected_count": len(test_case.expected_tradelines),
                "extracted_count": len(validated_tradelines),
                "matches": matches,
                "accuracy": accuracy,
                "success": accuracy >= 90,
                "issues_found": self.identify_issues(test_case, validated_tradelines),
                "confidence": parsing_result.confidence
            }
            
        except Exception as e:
            return {
                "test_name": test_case.name,
                "bureau": test_case.bureau,
                "difficulty": test_case.difficulty_level,
                "expected_count": len(test_case.expected_tradelines),
                "extracted_count": 0,
                "matches": 0,
                "accuracy": 0,
                "success": False,
                "error": str(e),
                "confidence": 0.0
            }
    
    def match_real_world_tradelines(
        self,
        expected: List[Dict[str, Any]],
        extracted: List[Any]
    ) -> int:
        """Match expected tradelines to extracted ones with real-world flexibility."""
        matches = 0
        
        for exp_tradeline in expected:
            for ext_tradeline in extracted:
                match_score = 0
                total_fields = 0
                
                # Check each field with fuzzy matching
                for field, expected_value in exp_tradeline.items():
                    if not expected_value:  # Skip empty expected values
                        continue
                    
                    total_fields += 1
                    extracted_value = getattr(ext_tradeline, field, "") or ""
                    
                    if self.fuzzy_match_field(str(expected_value), str(extracted_value), field):
                        match_score += 1
                
                # Consider it a match if >= 70% of fields match
                if total_fields > 0 and (match_score / total_fields) >= 0.7:
                    matches += 1
                    break
        
        return matches
    
    def fuzzy_match_field(self, expected: str, extracted: str, field_name: str) -> bool:
        """Field-specific fuzzy matching with context awareness."""
        expected = expected.lower().strip()
        extracted = extracted.lower().strip()
        
        if not expected or not extracted:
            return False
        
        # Exact match
        if expected == extracted:
            return True
        
        # Account number matching (handle masking)
        if "account" in field_name:
            # Handle masked account numbers like ****1234
            exp_last4 = re.search(r'\d{4}$', expected)
            ext_last4 = re.search(r'\d{4}$', extracted)
            if exp_last4 and ext_last4:
                return exp_last4.group() == ext_last4.group()
        
        # Currency amount matching
        if "$" in expected or "$" in extracted:
            exp_amount = re.search(r'[\d,]+\.?\d*', expected.replace(',', ''))
            ext_amount = re.search(r'[\d,]+\.?\d*', extracted.replace(',', ''))
            if exp_amount and ext_amount:
                try:
                    exp_val = float(exp_amount.group().replace(',', ''))
                    ext_val = float(ext_amount.group().replace(',', ''))
                    return abs(exp_val - ext_val) < 0.01  # Allow minor rounding differences
                except:
                    pass
        
        # Name/creditor matching (handle common variations)
        if "creditor" in field_name or "name" in field_name:
            # Remove common suffixes and prefixes
            exp_clean = re.sub(r'\b(bank|n\.?a\.?|inc\.?|llc|corp\.?|company)\b', '', expected)
            ext_clean = re.sub(r'\b(bank|n\.?a\.?|inc\.?|llc|corp\.?|company)\b', '', extracted)
            
            # Check if core name matches
            exp_words = set(exp_clean.split())
            ext_words = set(ext_clean.split())
            
            if exp_words and ext_words:
                overlap = len(exp_words.intersection(ext_words))
                return overlap / len(exp_words) >= 0.6
        
        # General similarity for other fields
        return self.calculate_similarity(expected, extracted) >= 0.8
    
    def calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using Jaccard similarity."""
        set1 = set(str1.lower())
        set2 = set(str2.lower())
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def identify_issues(self, test_case: RealWorldTestCase, extracted_tradelines: List[Any]) -> List[str]:
        """Identify specific issues found during parsing."""
        issues = []
        
        # Check for expected issue types
        if "ocr_errors" in test_case.common_issues:
            if len(extracted_tradelines) < len(test_case.expected_tradelines):
                issues.append("OCR errors affected extraction")
        
        if "negative_accounts" in test_case.common_issues:
            negative_found = any(getattr(tl, 'is_negative', False) for tl in extracted_tradelines)
            if not negative_found:
                issues.append("Failed to identify negative accounts")
        
        if "minimal_data" in test_case.common_issues:
            if not extracted_tradelines:
                issues.append("Unable to extract minimal data tradelines")
        
        return issues
    
    def get_difficulty_breakdown(self, results: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Analyze results by difficulty level."""
        difficulty_stats = {}
        
        for difficulty in ["easy", "medium", "hard", "extreme"]:
            difficulty_results = [r for r in results if r["difficulty"] == difficulty]
            
            if difficulty_results:
                avg_accuracy = sum(r["accuracy"] for r in difficulty_results) / len(difficulty_results)
                success_rate = sum(1 for r in difficulty_results if r["success"]) / len(difficulty_results) * 100
                
                difficulty_stats[difficulty] = {
                    "count": len(difficulty_results),
                    "average_accuracy": avg_accuracy,
                    "success_rate": success_rate,
                    "cases": [r["test_name"] for r in difficulty_results]
                }
        
        return difficulty_stats
    
    def analyze_common_issues(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze common issues across test cases."""
        total_issues = []
        
        for result in results:
            if "issues_found" in result:
                total_issues.extend(result["issues_found"])
        
        # Count issue frequency
        issue_counts = {}
        for issue in total_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        return {
            "total_issues": len(total_issues),
            "unique_issues": len(issue_counts),
            "most_common": sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        }


# Edge case testing functions
class EdgeCaseTester:
    """Test edge cases and boundary conditions."""
    
    def __init__(self):
        self.validator = RealWorldValidator()
    
    async def test_edge_cases(self) -> Dict[str, Any]:
        """Test various edge cases."""
        print("🔬 Testing Edge Cases...")
        
        edge_cases = [
            await self.test_empty_document(),
            await self.test_non_credit_document(),
            await self.test_corrupted_text(),
            await self.test_foreign_language(),
            await self.test_extreme_formatting(),
            await self.test_very_long_document(),
            await self.test_duplicate_accounts(),
            await self.test_unusual_account_types()
        ]
        
        return {
            "edge_case_results": edge_cases,
            "total_edge_cases": len(edge_cases),
            "passed_edge_cases": sum(1 for case in edge_cases if case.get("success", False))
        }
    
    async def test_empty_document(self) -> Dict[str, Any]:
        """Test empty or nearly empty document."""
        return await self.run_edge_case(
            name="empty_document",
            text="",
            description="Empty document test"
        )
    
    async def test_non_credit_document(self) -> Dict[str, Any]:
        """Test document that's not a credit report."""
        return await self.run_edge_case(
            name="non_credit_document",
            text="""
            INVOICE
            
            Company: ABC Corp
            Invoice #: 12345
            Date: 2024-03-01
            
            Items:
            - Widget A: $100
            - Widget B: $200
            
            Total: $300
            """,
            description="Non-credit document test"
        )
    
    async def test_corrupted_text(self) -> Dict[str, Any]:
        """Test heavily corrupted OCR text."""
        return await self.run_edge_case(
            name="corrupted_text",
            text="""
            �������� ���� ������
            
            ������� ����������
            
            ��������: $@#$%^&*()
            ������: 123abc!@#
            
            ���������� ��������
            """,
            description="Heavily corrupted text test"
        )
    
    async def test_foreign_language(self) -> Dict[str, Any]:
        """Test foreign language content."""
        return await self.run_edge_case(
            name="foreign_language",
            text="""
            RAPPORT DE CRÉDIT
            
            Informations sur le compte:
            Créancier: Banque Nationale
            Numéro de compte: 1234567890
            Solde: 1000€
            Statut: Courant
            """,
            description="Foreign language test"
        )
    
    async def test_extreme_formatting(self) -> Dict[str, Any]:
        """Test extremely poor formatting."""
        return await self.run_edge_case(
            name="extreme_formatting",
            text="CAPITALONEBANKAccount:1234Balance$500StatusCurrentCHASEBANKAccount:5678Balance$1000StatusCurrent",
            description="No spaces or formatting test"
        )
    
    async def test_very_long_document(self) -> Dict[str, Any]:
        """Test very long document."""
        long_text = "EXPERIAN CREDIT REPORT\n\n"
        for i in range(100):  # Create 100 fake tradelines
            long_text += f"""
            CREDITOR {i}
            Account: {i:010d}
            Balance: ${i * 100}
            Status: Current
            
            """
        
        return await self.run_edge_case(
            name="very_long_document",
            text=long_text,
            description="Very long document test"
        )
    
    async def test_duplicate_accounts(self) -> Dict[str, Any]:
        """Test duplicate account entries."""
        return await self.run_edge_case(
            name="duplicate_accounts",
            text="""
            CAPITAL ONE BANK
            Account: 1234567890
            Balance: $500
            Status: Current
            
            CAPITAL ONE BANK
            Account: 1234567890
            Balance: $500
            Status: Current
            
            CAPITAL ONE BANK USA N.A.
            Account: 1234567890
            Balance: $525
            Status: Current
            """,
            description="Duplicate accounts test"
        )
    
    async def test_unusual_account_types(self) -> Dict[str, Any]:
        """Test unusual account types."""
        return await self.run_edge_case(
            name="unusual_account_types",
            text="""
            BITCOIN EXCHANGE
            Account: BTC123456789
            Balance: 0.5 BTC
            Status: Active
            
            CRYPTOCURRENCY LENDING
            Account: ETH987654321
            Balance: 10 ETH
            Status: Current
            
            PEER TO PEER LOAN
            Account: P2P555666777
            Balance: $5000
            Status: Default
            """,
            description="Unusual account types test"
        )
    
    async def run_edge_case(self, name: str, text: str, description: str) -> Dict[str, Any]:
        """Run a single edge case test."""
        start_time = time.time()
        
        try:
            # Try to parse the edge case
            parsing_result = self.validator.parser.get_best_result(text)
            
            processing_time = time.time() - start_time
            
            return {
                "name": name,
                "description": description,
                "success": parsing_result.success,
                "tradelines_found": len(parsing_result.tradelines) if parsing_result.success else 0,
                "confidence": parsing_result.confidence if parsing_result.success else 0.0,
                "processing_time": processing_time,
                "error_handled": not parsing_result.success  # Edge cases should often fail gracefully
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            return {
                "name": name,
                "description": description,
                "success": False,
                "error": str(e),
                "processing_time": processing_time,
                "error_handled": True  # Exception was caught
            }


async def run_real_world_validation():
    """Main function to run real-world validation."""
    validator = RealWorldValidator()
    edge_tester = EdgeCaseTester()
    
    print("🌍 Starting Real-World Validation Suite")
    
    # Run real-world cases
    real_world_results = await validator.validate_real_world_cases()
    
    # Run edge cases
    edge_case_results = await edge_tester.test_edge_cases()
    
    # Combined report
    combined_report = {
        "real_world_validation": real_world_results,
        "edge_case_testing": edge_case_results,
        "overall_robustness": {
            "real_world_accuracy": real_world_results["overall_accuracy"],
            "edge_cases_handled": edge_case_results["passed_edge_cases"] / edge_case_results["total_edge_cases"] * 100
        }
    }
    
    print(f"\n🎯 Real-World Validation Complete:")
    print(f"   Real-World Accuracy: {real_world_results['overall_accuracy']:.2f}%")
    print(f"   Edge Cases Handled: {edge_case_results['passed_edge_cases']}/{edge_case_results['total_edge_cases']}")
    
    # Save results
    with open("/tmp/real_world_validation_results.json", 'w') as f:
        json.dump(combined_report, f, indent=2)
    
    return combined_report


if __name__ == "__main__":
    asyncio.run(run_real_world_validation())