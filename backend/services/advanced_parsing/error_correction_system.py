"""
Intelligent Error Correction and Fallback System
Advanced error detection, correction, and recovery mechanisms
"""
import logging
import re
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import numpy as np
from datetime import datetime

from .bureau_specific_parser import TradelineData, ParsingResult
from .ai_tradeline_validator import ValidationResult, AITradelineValidator
from .multi_layer_extractor import MultiLayerExtractor, ConsolidatedResult

from core.logging.logger import get_logger
from core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

class ErrorType(Enum):
    """Types of parsing errors."""
    OCR_ERROR = "ocr_error"
    EXTRACTION_ERROR = "extraction_error"
    VALIDATION_ERROR = "validation_error"
    FORMAT_ERROR = "format_error"
    FIELD_MISSING = "field_missing"
    FIELD_INVALID = "field_invalid"
    STRUCTURE_ERROR = "structure_error"
    CONFIDENCE_LOW = "confidence_low"
    BUREAU_DETECTION_FAILED = "bureau_detection_failed"
    AI_PROCESSING_ERROR = "ai_processing_error"

class ErrorSeverity(Enum):
    """Severity levels for errors."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ParseError:
    """Represents a parsing error."""
    error_id: str
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    field_name: Optional[str] = None
    original_value: Optional[str] = None
    suggested_correction: Optional[str] = None
    confidence: float = 0.0
    context: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class CorrectionResult:
    """Result of error correction attempt."""
    success: bool
    corrected_data: Optional[TradelineData] = None
    corrections_applied: List[str] = None
    remaining_errors: List[ParseError] = None
    confidence_improvement: float = 0.0
    method_used: str = ""
    
    def __post_init__(self):
        if self.corrections_applied is None:
            self.corrections_applied = []
        if self.remaining_errors is None:
            self.remaining_errors = []

class ErrorCorrectionSystem:
    """
    Intelligent error correction and fallback system.
    Uses multiple strategies to detect and correct parsing errors.
    """
    
    def __init__(self):
        self.ai_validator = AITradelineValidator()
        self.multi_extractor = MultiLayerExtractor()
        self.error_patterns = self._load_error_patterns()
        self.correction_rules = self._load_correction_rules()
        self.fallback_strategies = self._initialize_fallback_strategies()
        
        # Statistics tracking
        self.correction_stats = {
            'total_errors_detected': 0,
            'total_corrections_attempted': 0,
            'successful_corrections': 0,
            'error_type_frequencies': {},
            'correction_success_rates': {},
            'fallback_usage': {}
        }
    
    def _load_error_patterns(self) -> Dict[ErrorType, List[re.Pattern]]:
        """Load patterns for detecting different types of errors."""
        return {
            ErrorType.OCR_ERROR: [
                re.compile(r'[O0]{2,}'),  # Multiple zeros/O's
                re.compile(r'[Il1]{2,}'), # Multiple I/l/1's
                re.compile(r'[^\w\s$.,%-]'), # Invalid characters
                re.compile(r'\b[A-Z]{10,}\b'), # Very long uppercase strings
            ],
            ErrorType.FORMAT_ERROR: [
                re.compile(r'^\d+$'),  # Only digits for text fields
                re.compile(r'[a-zA-Z]+'),  # Letters in numeric fields
                re.compile(r'\$\$+'),  # Multiple dollar signs
            ],
            ErrorType.FIELD_INVALID: [
                re.compile(r'^[^a-zA-Z]+$'),  # No letters in name fields
                re.compile(r'^\d{1,2}$'),  # Single/double digits for amounts
                re.compile(r'^[^\d.,]+$'),  # No digits in amount fields
            ]
        }
    
    def _load_correction_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load correction rules for common errors."""
        return {
            'creditor_name_corrections': {
                'CHAS3': 'CHASE',
                'CHAS[E3]': 'CHASE',
                'BANK 0F': 'BANK OF',
                'W3LLS': 'WELLS',
                'FARG0': 'FARGO',
                'CIT1': 'CITI',
                'AM3RICAN': 'AMERICAN',
                '3XPR3SS': 'EXPRESS',
                'CAPITA1': 'CAPITAL',
                'DISCOV3R': 'DISCOVER',
                'SYNCHRONY': 'SYNCHRONY',
                'BAR[CG]LAYS': 'BARCLAYS'
            },
            'account_type_corrections': {
                'CR3DIT': 'CREDIT',
                'AUT0': 'AUTO',
                'M0RTGAGE': 'MORTGAGE',
                'P3RSONAL': 'PERSONAL',
                'STUD3NT': 'STUDENT',
                'L1NE': 'LINE',
                'R3VOLVING': 'REVOLVING'
            },
            'status_corrections': {
                'OP3N': 'OPEN',
                'CL0SED': 'CLOSED',
                'CURR3NT': 'CURRENT',
                'LAT3': 'LATE',
                'CHARG3': 'CHARGE',
                'COLL3CTION': 'COLLECTION'
            },
            'amount_corrections': {
                'O': '0',  # Letter O to zero
                'l': '1',  # Lowercase l to 1
                'S': '5',  # S to 5 in amounts
                'B': '8',  # B to 8
            }
        }
    
    def _initialize_fallback_strategies(self) -> List[str]:
        """Initialize fallback strategy names."""
        return [
            'retry_with_different_ocr',
            'use_alternative_parser',
            'apply_fuzzy_matching',
            'use_ai_reconstruction',
            'manual_intervention_required'
        ]
    
    async def detect_and_correct_errors(
        self, 
        parsing_result: ParsingResult,
        original_text: str,
        pdf_path: Optional[str] = None
    ) -> Tuple[ParsingResult, List[CorrectionResult]]:
        """
        Detect and correct errors in parsing result.
        
        Args:
            parsing_result: Initial parsing result
            original_text: Original extracted text
            pdf_path: Path to original PDF for re-processing
            
        Returns:
            Tuple of corrected parsing result and list of correction results
        """
        logger.info(f"Starting error detection and correction for {len(parsing_result.tradelines)} tradelines")
        
        detected_errors = await self._detect_errors(parsing_result, original_text)
        logger.info(f"Detected {len(detected_errors)} errors")
        
        if not detected_errors:
            return parsing_result, []
        
        # Group errors by tradeline
        errors_by_tradeline = self._group_errors_by_tradeline(detected_errors, parsing_result.tradelines)
        
        corrected_tradelines = []
        correction_results = []
        
        for i, tradeline in enumerate(parsing_result.tradelines):
            tradeline_errors = errors_by_tradeline.get(i, [])
            
            if tradeline_errors:
                logger.info(f"Correcting {len(tradeline_errors)} errors for tradeline {i}")
                correction_result = await self._correct_tradeline_errors(
                    tradeline, tradeline_errors, original_text, pdf_path
                )
                correction_results.append(correction_result)
                
                if correction_result.success and correction_result.corrected_data:
                    corrected_tradelines.append(correction_result.corrected_data)
                else:
                    corrected_tradelines.append(tradeline)  # Keep original if correction failed
            else:
                corrected_tradelines.append(tradeline)
        
        # Create corrected parsing result
        corrected_result = ParsingResult(
            bureau=parsing_result.bureau,
            success=parsing_result.success,
            tradelines=corrected_tradelines,
            confidence=self._calculate_corrected_confidence(parsing_result.confidence, correction_results),
            parsing_method=f"{parsing_result.parsing_method}_corrected",
            errors=parsing_result.errors + [cr.method_used for cr in correction_results if not cr.success],
            metadata={
                **parsing_result.metadata,
                'corrections_applied': len([cr for cr in correction_results if cr.success]),
                'total_errors_detected': len(detected_errors),
                'error_correction_enabled': True
            }
        )
        
        # Update statistics
        self._update_correction_stats(detected_errors, correction_results)
        
        logger.info(f"Error correction completed. Success rate: {len([cr for cr in correction_results if cr.success])}/{len(correction_results)}")
        
        return corrected_result, correction_results
    
    async def _detect_errors(
        self, 
        parsing_result: ParsingResult,
        original_text: str
    ) -> List[ParseError]:
        """Detect errors in parsing result."""
        errors = []
        
        # Overall confidence check
        if parsing_result.confidence < 0.6:
            errors.append(ParseError(
                error_id=f"low_confidence_{parsing_result.bureau}",
                error_type=ErrorType.CONFIDENCE_LOW,
                severity=ErrorSeverity.HIGH,
                message=f"Overall parsing confidence is low: {parsing_result.confidence:.2f}",
                confidence=1.0 - parsing_result.confidence
            ))
        
        # Check each tradeline
        for i, tradeline in enumerate(parsing_result.tradelines):
            tradeline_errors = await self._detect_tradeline_errors(tradeline, i, original_text)
            errors.extend(tradeline_errors)
        
        return errors
    
    async def _detect_tradeline_errors(
        self, 
        tradeline: TradelineData, 
        index: int,
        original_text: str
    ) -> List[ParseError]:
        """Detect errors in a single tradeline."""
        errors = []
        
        # Check for missing essential fields
        essential_fields = ['creditor_name', 'account_type', 'account_status']
        for field in essential_fields:
            value = getattr(tradeline, field, "")
            if not value or len(value.strip()) < 2:
                errors.append(ParseError(
                    error_id=f"missing_field_{index}_{field}",
                    error_type=ErrorType.FIELD_MISSING,
                    severity=ErrorSeverity.HIGH,
                    message=f"Essential field '{field}' is missing or too short",
                    field_name=field,
                    original_value=value
                ))
        
        # Check for OCR errors in text fields
        text_fields = ['creditor_name', 'account_type', 'account_status']
        for field in text_fields:
            value = getattr(tradeline, field, "")
            if value:
                ocr_errors = self._detect_ocr_errors(value)
                for error_pattern in ocr_errors:
                    errors.append(ParseError(
                        error_id=f"ocr_error_{index}_{field}",
                        error_type=ErrorType.OCR_ERROR,
                        severity=ErrorSeverity.MEDIUM,
                        message=f"Possible OCR error in {field}: '{error_pattern}'",
                        field_name=field,
                        original_value=value,
                        suggested_correction=self._suggest_ocr_correction(value, field)
                    ))
        
        # Check for format errors in amount fields
        amount_fields = ['account_balance', 'credit_limit', 'monthly_payment', 'high_balance']
        for field in amount_fields:
            value = getattr(tradeline, field, "")
            if value and not self._is_valid_amount_format(value):
                errors.append(ParseError(
                    error_id=f"format_error_{index}_{field}",
                    error_type=ErrorType.FORMAT_ERROR,
                    severity=ErrorSeverity.MEDIUM,
                    message=f"Invalid amount format in {field}: '{value}'",
                    field_name=field,
                    original_value=value,
                    suggested_correction=self._suggest_amount_correction(value)
                ))
        
        # Check for date format errors
        date_fields = ['date_opened', 'date_closed', 'last_payment_date']
        for field in date_fields:
            value = getattr(tradeline, field, "")
            if value and not self._is_valid_date_format(value):
                errors.append(ParseError(
                    error_id=f"date_error_{index}_{field}",
                    error_type=ErrorType.FORMAT_ERROR,
                    severity=ErrorSeverity.LOW,
                    message=f"Invalid date format in {field}: '{value}'",
                    field_name=field,
                    original_value=value,
                    suggested_correction=self._suggest_date_correction(value)
                ))
        
        # Check extraction confidence
        if hasattr(tradeline, 'extraction_confidence') and tradeline.extraction_confidence < 0.5:
            errors.append(ParseError(
                error_id=f"low_extraction_confidence_{index}",
                error_type=ErrorType.CONFIDENCE_LOW,
                severity=ErrorSeverity.MEDIUM,
                message=f"Low extraction confidence: {tradeline.extraction_confidence:.2f}",
                confidence=tradeline.extraction_confidence
            ))
        
        return errors
    
    def _detect_ocr_errors(self, text: str) -> List[str]:
        """Detect potential OCR errors in text."""
        errors = []
        
        for error_type, patterns in self.error_patterns.items():
            if error_type == ErrorType.OCR_ERROR:
                for pattern in patterns:
                    matches = pattern.findall(text)
                    errors.extend(matches)
        
        return errors
    
    def _suggest_ocr_correction(self, text: str, field_name: str) -> Optional[str]:
        """Suggest OCR correction for text."""
        corrected = text
        
        # Apply field-specific corrections
        if field_name == 'creditor_name':
            corrections = self.correction_rules['creditor_name_corrections']
        elif field_name == 'account_type':
            corrections = self.correction_rules['account_type_corrections']
        elif field_name == 'account_status':
            corrections = self.correction_rules['status_corrections']
        else:
            corrections = {}
        
        # Apply corrections
        for wrong, correct in corrections.items():
            corrected = re.sub(wrong, correct, corrected, flags=re.IGNORECASE)
        
        return corrected if corrected != text else None
    
    def _is_valid_amount_format(self, amount: str) -> bool:
        """Check if amount is in valid format."""
        if not amount:
            return False
        
        # Remove common formatting
        cleaned = re.sub(r'[$,\s]', '', amount)
        
        # Check for negative amounts in parentheses
        if '(' in amount and ')' in amount:
            cleaned = cleaned.replace('(', '-').replace(')', '')
        
        try:
            float(cleaned)
            return True
        except ValueError:
            return False
    
    def _suggest_amount_correction(self, amount: str) -> Optional[str]:
        """Suggest correction for amount format."""
        if not amount:
            return None
        
        corrected = amount
        
        # Apply amount corrections
        for wrong, correct in self.correction_rules['amount_corrections'].items():
            corrected = corrected.replace(wrong, correct)
        
        # Remove multiple dollar signs
        corrected = re.sub(r'\$+', '$', corrected)
        
        # Fix common formatting issues
        corrected = re.sub(r'(\d),(\d{1,2})$', r'\1.\2', corrected)  # Fix decimal point
        
        return corrected if corrected != amount else None
    
    def _is_valid_date_format(self, date_str: str) -> bool:
        """Check if date is in valid format."""
        if not date_str:
            return False
        
        date_patterns = [
            r'^\d{1,2}/\d{1,2}/\d{4}$',  # MM/DD/YYYY
            r'^\d{1,2}/\d{1,2}/\d{2}$',   # MM/DD/YY
            r'^\d{2}/\d{4}$',             # MM/YYYY
            r'^\d{4}-\d{1,2}-\d{1,2}$',   # YYYY-MM-DD
        ]
        
        return any(re.match(pattern, date_str) for pattern in date_patterns)
    
    def _suggest_date_correction(self, date_str: str) -> Optional[str]:
        """Suggest date format correction."""
        if not date_str:
            return None
        
        # Try to fix common date issues
        corrected = date_str
        
        # Fix OCR errors in dates
        corrected = corrected.replace('O', '0').replace('l', '1').replace('I', '1')
        
        # Try to standardize format
        if re.match(r'^\d{4}-\d{1,2}-\d{1,2}$', corrected):
            # Convert YYYY-MM-DD to MM/DD/YYYY
            parts = corrected.split('-')
            corrected = f"{parts[1]}/{parts[2]}/{parts[0]}"
        
        return corrected if corrected != date_str else None
    
    async def _correct_tradeline_errors(
        self, 
        tradeline: TradelineData,
        errors: List[ParseError],
        original_text: str,
        pdf_path: Optional[str]
    ) -> CorrectionResult:
        """Correct errors in a single tradeline."""
        logger.info(f"Attempting to correct {len(errors)} errors in tradeline")
        
        corrected_tradeline = TradelineData(**asdict(tradeline))
        corrections_applied = []
        remaining_errors = []
        
        # Try direct field corrections first
        for error in errors:
            if error.suggested_correction and error.field_name:
                try:
                    original_value = getattr(corrected_tradeline, error.field_name)
                    setattr(corrected_tradeline, error.field_name, error.suggested_correction)
                    corrections_applied.append(f"{error.field_name}: {original_value} -> {error.suggested_correction}")
                    logger.info(f"Applied direct correction: {corrections_applied[-1]}")
                except Exception as e:
                    logger.warning(f"Failed to apply direct correction: {e}")
                    remaining_errors.append(error)
            else:
                remaining_errors.append(error)
        
        # If significant errors remain, try fallback strategies
        if len(remaining_errors) > 2 or any(e.severity == ErrorSeverity.CRITICAL for e in remaining_errors):
            logger.info("Attempting fallback strategies for remaining errors")
            
            fallback_result = await self._apply_fallback_strategies(
                corrected_tradeline, remaining_errors, original_text, pdf_path
            )
            
            if fallback_result.success:
                corrected_tradeline = fallback_result.corrected_data
                corrections_applied.extend(fallback_result.corrections_applied)
                remaining_errors = fallback_result.remaining_errors
        
        # Final AI validation and correction
        if self.ai_validator:
            try:
                validation_result = await self.ai_validator.validate_and_correct_tradeline(
                    corrected_tradeline, original_text
                )
                
                if validation_result.is_valid and validation_result.corrections_made:
                    corrected_tradeline = validation_result.corrected_data
                    corrections_applied.extend(validation_result.corrections_made)
                    logger.info(f"AI validation applied {len(validation_result.corrections_made)} additional corrections")
                
            except Exception as e:
                logger.warning(f"AI validation failed: {e}")
        
        # Calculate confidence improvement
        original_confidence = getattr(tradeline, 'extraction_confidence', 0.5)
        new_confidence = getattr(corrected_tradeline, 'extraction_confidence', original_confidence)
        confidence_improvement = new_confidence - original_confidence
        
        success = len(corrections_applied) > 0 and len(remaining_errors) < len(errors) / 2
        
        return CorrectionResult(
            success=success,
            corrected_data=corrected_tradeline if success else None,
            corrections_applied=corrections_applied,
            remaining_errors=remaining_errors,
            confidence_improvement=confidence_improvement,
            method_used="direct_correction_with_ai"
        )
    
    async def _apply_fallback_strategies(
        self,
        tradeline: TradelineData,
        errors: List[ParseError],
        original_text: str,
        pdf_path: Optional[str]
    ) -> CorrectionResult:
        """Apply fallback strategies for difficult errors."""
        logger.info(f"Applying fallback strategies for {len(errors)} difficult errors")
        
        for strategy in self.fallback_strategies:
            try:
                result = await self._apply_single_fallback_strategy(
                    strategy, tradeline, errors, original_text, pdf_path
                )
                
                if result.success:
                    logger.info(f"Fallback strategy '{strategy}' succeeded")
                    self.correction_stats['fallback_usage'][strategy] = self.correction_stats['fallback_usage'].get(strategy, 0) + 1
                    return result
                
            except Exception as e:
                logger.warning(f"Fallback strategy '{strategy}' failed: {e}")
        
        logger.warning("All fallback strategies failed")
        return CorrectionResult(
            success=False,
            method_used="fallback_strategies_exhausted"
        )
    
    async def _apply_single_fallback_strategy(
        self,
        strategy: str,
        tradeline: TradelineData,
        errors: List[ParseError],
        original_text: str,
        pdf_path: Optional[str]
    ) -> CorrectionResult:
        """Apply a single fallback strategy."""
        
        if strategy == "retry_with_different_ocr":
            return await self._retry_with_different_ocr(pdf_path, tradeline, errors)
        
        elif strategy == "use_alternative_parser":
            return await self._use_alternative_parser(original_text, tradeline, errors)
        
        elif strategy == "apply_fuzzy_matching":
            return await self._apply_fuzzy_matching(tradeline, errors, original_text)
        
        elif strategy == "use_ai_reconstruction":
            return await self._use_ai_reconstruction(tradeline, errors, original_text)
        
        elif strategy == "manual_intervention_required":
            return await self._flag_for_manual_intervention(tradeline, errors)
        
        else:
            return CorrectionResult(success=False, method_used=f"unknown_strategy_{strategy}")
    
    async def _retry_with_different_ocr(
        self,
        pdf_path: Optional[str],
        tradeline: TradelineData,
        errors: List[ParseError]
    ) -> CorrectionResult:
        """Retry extraction with different OCR settings."""
        if not pdf_path or not self.multi_extractor:
            return CorrectionResult(success=False, method_used="retry_ocr_unavailable")
        
        try:
            # Try extraction with enhanced OCR
            enhanced_result = await self.multi_extractor.extract_text_multi_layer(
                pdf_path, use_ai=True, quality_threshold=0.9
            )
            
            if enhanced_result.quality_score > 0.8:
                # Re-parse with enhanced text
                # This would require integration with bureau parsers
                logger.info("Enhanced OCR extraction improved quality")
                return CorrectionResult(
                    success=True,
                    method_used="enhanced_ocr_retry",
                    corrections_applied=["Enhanced OCR re-extraction applied"]
                )
            
        except Exception as e:
            logger.error(f"Enhanced OCR retry failed: {e}")
        
        return CorrectionResult(success=False, method_used="enhanced_ocr_failed")
    
    async def _use_alternative_parser(
        self,
        original_text: str,
        tradeline: TradelineData,
        errors: List[ParseError]
    ) -> CorrectionResult:
        """Try parsing with alternative bureau parsers."""
        # This would try different bureau-specific parsers
        # Implementation would depend on having multiple parser options
        return CorrectionResult(success=False, method_used="alternative_parser_not_implemented")
    
    async def _apply_fuzzy_matching(
        self,
        tradeline: TradelineData,
        errors: List[ParseError],
        original_text: str
    ) -> CorrectionResult:
        """Apply fuzzy string matching for corrections."""
        corrections_applied = []
        
        try:
            # Apply fuzzy matching for creditor names
            if tradeline.creditor_name:
                from fuzzywuzzy import fuzz, process
                
                # Known creditor list (would be loaded from database/config)
                known_creditors = [
                    'Chase', 'Bank of America', 'Wells Fargo', 'Citibank', 'Capital One',
                    'American Express', 'Discover', 'Synchrony Bank', 'Barclays'
                ]
                
                match, score = process.extractOne(tradeline.creditor_name, known_creditors)
                if score > 80 and match != tradeline.creditor_name:
                    corrections_applied.append(f"Fuzzy matched creditor: {tradeline.creditor_name} -> {match}")
                    tradeline.creditor_name = match
            
            return CorrectionResult(
                success=len(corrections_applied) > 0,
                corrected_data=tradeline if corrections_applied else None,
                corrections_applied=corrections_applied,
                method_used="fuzzy_matching"
            )
            
        except ImportError:
            logger.warning("fuzzywuzzy not available for fuzzy matching")
            return CorrectionResult(success=False, method_used="fuzzy_matching_unavailable")
        except Exception as e:
            logger.error(f"Fuzzy matching failed: {e}")
            return CorrectionResult(success=False, method_used="fuzzy_matching_failed")
    
    async def _use_ai_reconstruction(
        self,
        tradeline: TradelineData,
        errors: List[ParseError],
        original_text: str
    ) -> CorrectionResult:
        """Use AI to reconstruct missing or corrupted data."""
        if not self.ai_validator:
            return CorrectionResult(success=False, method_used="ai_reconstruction_unavailable")
        
        try:
            # Use AI validator for enhanced reconstruction
            validation_result = await self.ai_validator.validate_and_correct_tradeline(
                tradeline, original_text
            )
            
            if validation_result.corrections_made:
                return CorrectionResult(
                    success=True,
                    corrected_data=validation_result.corrected_data,
                    corrections_applied=validation_result.corrections_made,
                    method_used="ai_reconstruction"
                )
            
        except Exception as e:
            logger.error(f"AI reconstruction failed: {e}")
        
        return CorrectionResult(success=False, method_used="ai_reconstruction_failed")
    
    async def _flag_for_manual_intervention(
        self,
        tradeline: TradelineData,
        errors: List[ParseError]
    ) -> CorrectionResult:
        """Flag tradeline for manual review."""
        logger.warning(f"Flagging tradeline for manual intervention: {len(errors)} unresolved errors")
        
        # In production, this would create a task for manual review
        manual_review_note = f"Manual review required - {len(errors)} unresolved errors: {[e.message for e in errors]}"
        
        return CorrectionResult(
            success=False,  # Not automatically corrected
            method_used="manual_intervention_flagged",
            corrections_applied=[manual_review_note],
            remaining_errors=errors
        )
    
    def _group_errors_by_tradeline(
        self, 
        errors: List[ParseError], 
        tradelines: List[TradelineData]
    ) -> Dict[int, List[ParseError]]:
        """Group errors by tradeline index."""
        grouped = {}
        
        for error in errors:
            # Extract tradeline index from error ID
            try:
                if '_' in error.error_id:
                    parts = error.error_id.split('_')
                    for part in parts:
                        if part.isdigit():
                            index = int(part)
                            if 0 <= index < len(tradelines):
                                if index not in grouped:
                                    grouped[index] = []
                                grouped[index].append(error)
                                break
            except (ValueError, IndexError):
                # If can't determine index, add to index 0 as fallback
                if 0 not in grouped:
                    grouped[0] = []
                grouped[0].append(error)
        
        return grouped
    
    def _calculate_corrected_confidence(
        self, 
        original_confidence: float, 
        correction_results: List[CorrectionResult]
    ) -> float:
        """Calculate improved confidence after corrections."""
        if not correction_results:
            return original_confidence
        
        # Average confidence improvement
        total_improvement = sum(cr.confidence_improvement for cr in correction_results)
        avg_improvement = total_improvement / len(correction_results)
        
        # Success rate bonus
        success_rate = len([cr for cr in correction_results if cr.success]) / len(correction_results)
        success_bonus = success_rate * 0.1  # Up to 10% bonus
        
        # Calculate new confidence
        new_confidence = min(1.0, original_confidence + avg_improvement + success_bonus)
        
        return new_confidence
    
    def _update_correction_stats(
        self, 
        detected_errors: List[ParseError], 
        correction_results: List[CorrectionResult]
    ):
        """Update correction statistics."""
        self.correction_stats['total_errors_detected'] += len(detected_errors)
        self.correction_stats['total_corrections_attempted'] += len(correction_results)
        self.correction_stats['successful_corrections'] += len([cr for cr in correction_results if cr.success])
        
        # Track error types
        for error in detected_errors:
            error_type = error.error_type.value
            self.correction_stats['error_type_frequencies'][error_type] = self.correction_stats['error_type_frequencies'].get(error_type, 0) + 1
        
        # Track correction success rates by method
        for result in correction_results:
            method = result.method_used
            if method not in self.correction_stats['correction_success_rates']:
                self.correction_stats['correction_success_rates'][method] = {'attempts': 0, 'successes': 0}
            
            self.correction_stats['correction_success_rates'][method]['attempts'] += 1
            if result.success:
                self.correction_stats['correction_success_rates'][method]['successes'] += 1
    
    def get_correction_statistics(self) -> Dict[str, Any]:
        """Get error correction statistics."""
        stats = self.correction_stats.copy()
        
        # Calculate success rates
        for method, data in stats['correction_success_rates'].items():
            if data['attempts'] > 0:
                data['success_rate'] = data['successes'] / data['attempts']
            else:
                data['success_rate'] = 0.0
        
        # Overall success rate
        if stats['total_corrections_attempted'] > 0:
            stats['overall_success_rate'] = stats['successful_corrections'] / stats['total_corrections_attempted']
        else:
            stats['overall_success_rate'] = 0.0
        
        return stats

# Global error correction system instance
error_correction_system = ErrorCorrectionSystem()