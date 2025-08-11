"""
AI-Powered Tradeline Identification and Validation System
Uses machine learning to identify, extract, and validate tradeline data
"""
import logging
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import asyncio
from datetime import datetime
import numpy as np

# AI/ML Libraries
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import openai

# Custom imports
from .bureau_specific_parser import TradelineData, ParsingResult
from core.config import get_settings
from core.logging.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

@dataclass
class ValidationResult:
    """Result of AI validation."""
    is_valid: bool
    confidence: float
    corrected_data: TradelineData
    corrections_made: List[str]
    validation_notes: List[str]
    ai_score: float

@dataclass
class FieldValidation:
    """Individual field validation result."""
    field_name: str
    original_value: str
    corrected_value: str
    confidence: float
    correction_method: str
    is_corrected: bool

class AITradelineValidator:
    """
    AI-powered tradeline validation and correction system.
    Uses multiple AI techniques for maximum accuracy.
    """
    
    def __init__(self):
        self.ner_pipeline = None
        self.classification_pipeline = None
        self.openai_client = None
        self.tfidf_vectorizer = None
        self.reference_data = {}
        self.validation_stats = {
            'total_validations': 0,
            'corrections_made': 0,
            'accuracy_improvements': [],
            'field_correction_rates': {}
        }
        
        # Initialize AI models
        asyncio.create_task(self._initialize_ai_models())
    
    async def _initialize_ai_models(self):
        """Initialize AI models for validation."""
        try:
            logger.info("Initializing AI models for tradeline validation...")
            
            # Named Entity Recognition for tradeline data
            self.ner_pipeline = pipeline(
                "ner", 
                model="dbmdz/bert-large-cased-finetuned-conll03-english",
                aggregation_strategy="simple"
            )
            
            # Text classification for tradeline validation
            self.classification_pipeline = pipeline(
                "text-classification",
                model="distilbert-base-uncased-finetuned-sst-2-english"
            )
            
            # OpenAI client if available
            if hasattr(settings, 'openai_api_key') and settings.openai_api_key:
                openai.api_key = settings.openai_api_key
                self.openai_client = openai
            
            # Load reference data for validation
            await self._load_reference_data()
            
            logger.info("AI models initialized successfully")
            
        except Exception as e:
            logger.warning(f"AI model initialization failed: {e}")
    
    async def _load_reference_data(self):
        """Load reference data for validation (creditor names, account types, etc.)."""
        try:
            # In production, this would load from database or external sources
            self.reference_data = {
                'creditor_names': [
                    'Chase', 'Bank of America', 'Wells Fargo', 'Citibank', 'Capital One',
                    'American Express', 'Discover', 'Synchrony Bank', 'Barclays',
                    'US Bank', 'PNC Bank', 'TD Bank', 'Regions Bank', 'Fifth Third Bank'
                ],
                'account_types': [
                    'Credit Card', 'Auto Loan', 'Mortgage', 'Personal Loan', 
                    'Student Loan', 'Line of Credit', 'Store Card', 'Business Credit'
                ],
                'account_statuses': [
                    'Open', 'Closed', 'Current', 'Late 30 Days', 'Late 60 Days',
                    'Late 90 Days', 'Charge Off', 'Collection', 'Foreclosure',
                    'Repossession', 'Settled', 'Paid', 'Included in Bankruptcy'
                ],
                'payment_terms': [
                    '12 months', '24 months', '36 months', '48 months', '60 months',
                    '72 months', '84 months', 'Revolving', 'Open-ended'
                ]
            }
            
            # Create TF-IDF vectorizer for similarity matching
            all_reference_text = []
            for category, items in self.reference_data.items():
                all_reference_text.extend(items)
            
            self.tfidf_vectorizer = TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 2),
                max_features=1000
            )
            self.tfidf_vectorizer.fit(all_reference_text)
            
        except Exception as e:
            logger.error(f"Failed to load reference data: {e}")
    
    async def validate_and_correct_tradeline(
        self, 
        tradeline: TradelineData,
        context_text: str = ""
    ) -> ValidationResult:
        """
        Validate and correct a tradeline using AI techniques.
        
        Args:
            tradeline: The tradeline to validate
            context_text: Original context text for better understanding
            
        Returns:
            ValidationResult with corrections and confidence scores
        """
        logger.info(f"Starting AI validation for tradeline: {tradeline.creditor_name}")
        
        corrected_tradeline = TradelineData(**asdict(tradeline))  # Create copy
        corrections_made = []
        validation_notes = []
        field_validations = []
        
        try:
            # Validate each field
            field_validations.extend(await self._validate_creditor_name(corrected_tradeline, context_text))
            field_validations.extend(await self._validate_account_type(corrected_tradeline, context_text))
            field_validations.extend(await self._validate_account_status(corrected_tradeline, context_text))
            field_validations.extend(await self._validate_financial_amounts(corrected_tradeline, context_text))
            field_validations.extend(await self._validate_dates(corrected_tradeline, context_text))
            field_validations.extend(await self._validate_account_number(corrected_tradeline, context_text))
            
            # Apply corrections
            for field_val in field_validations:
                if field_val.is_corrected:
                    setattr(corrected_tradeline, field_val.field_name, field_val.corrected_value)
                    corrections_made.append(
                        f"{field_val.field_name}: '{field_val.original_value}' -> '{field_val.corrected_value}' "
                        f"({field_val.correction_method})"
                    )
            
            # Cross-field validation
            cross_validation_notes = await self._cross_validate_fields(corrected_tradeline)
            validation_notes.extend(cross_validation_notes)
            
            # AI-powered completeness check
            if self.openai_client:
                ai_validation = await self._openai_validate_tradeline(corrected_tradeline, context_text)
                validation_notes.extend(ai_validation.get('notes', []))
                
                # Apply any AI suggestions
                ai_corrections = ai_validation.get('corrections', {})
                for field, value in ai_corrections.items():
                    if hasattr(corrected_tradeline, field) and value:
                        original_value = getattr(corrected_tradeline, field)
                        if original_value != value:
                            setattr(corrected_tradeline, field, value)
                            corrections_made.append(f"{field}: AI correction applied")
            
            # Calculate overall confidence and validity
            avg_confidence = np.mean([fv.confidence for fv in field_validations]) if field_validations else 0.5
            is_valid = avg_confidence > 0.7 and corrected_tradeline.creditor_name.strip() != ""
            
            # Calculate AI score based on multiple factors
            ai_score = await self._calculate_ai_score(corrected_tradeline, field_validations, context_text)
            
            # Update statistics
            self._update_validation_stats(field_validations, corrections_made)
            
            return ValidationResult(
                is_valid=is_valid,
                confidence=avg_confidence,
                corrected_data=corrected_tradeline,
                corrections_made=corrections_made,
                validation_notes=validation_notes,
                ai_score=ai_score
            )
            
        except Exception as e:
            logger.error(f"AI validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                corrected_data=tradeline,  # Return original on error
                corrections_made=[],
                validation_notes=[f"Validation error: {str(e)}"],
                ai_score=0.0
            )
    
    async def _validate_creditor_name(
        self, 
        tradeline: TradelineData, 
        context: str
    ) -> List[FieldValidation]:
        """Validate and correct creditor name."""
        validations = []
        
        if not tradeline.creditor_name or len(tradeline.creditor_name.strip()) < 2:
            # Try to extract from context using NER
            if self.ner_pipeline and context:
                try:
                    entities = self.ner_pipeline(context)
                    for entity in entities:
                        if entity['entity_group'] in ['ORG', 'MISC'] and len(entity['word']) > 3:
                            # Check if this could be a creditor name
                            similarity = self._calculate_similarity(
                                entity['word'], 
                                self.reference_data['creditor_names']
                            )
                            if similarity > 0.6:
                                validations.append(FieldValidation(
                                    field_name='creditor_name',
                                    original_value=tradeline.creditor_name,
                                    corrected_value=entity['word'],
                                    confidence=entity['score'] * similarity,
                                    correction_method='ner_extraction',
                                    is_corrected=True
                                ))
                                break
                except Exception as e:
                    logger.warning(f"NER creditor extraction failed: {e}")
        
        # Validate existing creditor name
        if tradeline.creditor_name:
            # Clean up common OCR errors
            cleaned_name = self._clean_creditor_name(tradeline.creditor_name)
            
            # Check against known creditors
            similarity = self._calculate_similarity(
                cleaned_name, 
                self.reference_data['creditor_names']
            )
            
            is_corrected = cleaned_name != tradeline.creditor_name
            
            validations.append(FieldValidation(
                field_name='creditor_name',
                original_value=tradeline.creditor_name,
                corrected_value=cleaned_name,
                confidence=min(0.9, 0.5 + similarity),
                correction_method='cleaning_and_matching',
                is_corrected=is_corrected
            ))
        
        return validations
    
    def _clean_creditor_name(self, name: str) -> str:
        """Clean up creditor name from OCR errors."""
        if not name:
            return ""
        
        # Common OCR corrections
        corrections = {
            r'\bBANK\s+0F\b': 'BANK OF',
            r'\bCHAS[E3]\b': 'CHASE',
            r'\bCITI[B8]ANK\b': 'CITIBANK',
            r'\bAM[E3]RICAN\s+[E3]XPR[E3]SS\b': 'AMERICAN EXPRESS',
            r'\bW[E3]LLS\s+FARG[O0]\b': 'WELLS FARGO',
            r'\bCAPITAL\s+[O0]N[E3]\b': 'CAPITAL ONE',
            r'\b[O0][N1][E3]\s+MAIN\s+FINANCIAL\b': 'ONE MAIN FINANCIAL',
        }
        
        cleaned = name.upper()
        for pattern, replacement in corrections.items():
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    async def _validate_account_type(
        self, 
        tradeline: TradelineData, 
        context: str
    ) -> List[FieldValidation]:
        """Validate account type."""
        validations = []
        
        if not tradeline.account_type:
            # Try to infer from context or creditor name
            inferred_type = self._infer_account_type(tradeline.creditor_name, context)
            if inferred_type:
                validations.append(FieldValidation(
                    field_name='account_type',
                    original_value="",
                    corrected_value=inferred_type,
                    confidence=0.7,
                    correction_method='inference',
                    is_corrected=True
                ))
        else:
            # Validate existing account type
            similarity = self._calculate_similarity(
                tradeline.account_type,
                self.reference_data['account_types']
            )
            
            best_match = self._find_best_match(
                tradeline.account_type,
                self.reference_data['account_types']
            )
            
            is_corrected = best_match != tradeline.account_type and similarity > 0.8
            
            validations.append(FieldValidation(
                field_name='account_type',
                original_value=tradeline.account_type,
                corrected_value=best_match if is_corrected else tradeline.account_type,
                confidence=similarity,
                correction_method='similarity_matching',
                is_corrected=is_corrected
            ))
        
        return validations
    
    def _infer_account_type(self, creditor_name: str, context: str) -> Optional[str]:
        """Infer account type from creditor name or context."""
        if not creditor_name:
            return None
        
        creditor_lower = creditor_name.lower()
        context_lower = context.lower() if context else ""
        
        # Credit card indicators
        credit_card_indicators = [
            'visa', 'mastercard', 'american express', 'amex', 'discover',
            'store card', 'credit card', 'revolving'
        ]
        
        # Auto loan indicators
        auto_indicators = [
            'auto', 'vehicle', 'car', 'ford', 'toyota', 'honda', 'gm financial'
        ]
        
        # Mortgage indicators
        mortgage_indicators = [
            'mortgage', 'home', 'fha', 'va loan', 'real estate'
        ]
        
        combined_text = f"{creditor_lower} {context_lower}"
        
        if any(indicator in combined_text for indicator in credit_card_indicators):
            return "Credit Card"
        elif any(indicator in combined_text for indicator in auto_indicators):
            return "Auto Loan"
        elif any(indicator in combined_text for indicator in mortgage_indicators):
            return "Mortgage"
        
        return None
    
    async def _validate_account_status(
        self, 
        tradeline: TradelineData, 
        context: str
    ) -> List[FieldValidation]:
        """Validate account status."""
        validations = []
        
        if tradeline.account_status:
            # Clean and standardize status
            cleaned_status = self._clean_account_status(tradeline.account_status)
            
            # Find best match
            similarity = self._calculate_similarity(
                cleaned_status,
                self.reference_data['account_statuses']
            )
            
            best_match = self._find_best_match(
                cleaned_status,
                self.reference_data['account_statuses']
            )
            
            is_corrected = best_match != tradeline.account_status
            
            validations.append(FieldValidation(
                field_name='account_status',
                original_value=tradeline.account_status,
                corrected_value=best_match,
                confidence=similarity,
                correction_method='status_standardization',
                is_corrected=is_corrected
            ))
        
        return validations
    
    def _clean_account_status(self, status: str) -> str:
        """Clean and standardize account status."""
        if not status:
            return ""
        
        status_mappings = {
            r'(?i)open|current|ok|good': 'Current',
            r'(?i)closed|close': 'Closed',
            r'(?i)charge.?off|charged.?off': 'Charge Off',
            r'(?i)collection|collections': 'Collection',
            r'(?i)late\s*30|30\s*days?': 'Late 30 Days',
            r'(?i)late\s*60|60\s*days?': 'Late 60 Days',
            r'(?i)late\s*90|90\s*days?': 'Late 90 Days',
            r'(?i)foreclosure': 'Foreclosure',
            r'(?i)repo|repossession': 'Repossession',
            r'(?i)settled?|settlement': 'Settled',
            r'(?i)bankruptcy|bk': 'Included in Bankruptcy'
        }
        
        for pattern, standard_status in status_mappings.items():
            if re.search(pattern, status):
                return standard_status
        
        return status.title()  # Default to title case
    
    async def _validate_financial_amounts(
        self, 
        tradeline: TradelineData, 
        context: str
    ) -> List[FieldValidation]:
        """Validate financial amounts (balance, credit limit, payment)."""
        validations = []
        
        financial_fields = [
            ('account_balance', 'Balance'),
            ('credit_limit', 'Credit Limit'),
            ('monthly_payment', 'Monthly Payment'),
            ('high_balance', 'High Balance')
        ]
        
        for field_name, field_display in financial_fields:
            field_value = getattr(tradeline, field_name, "")
            if field_value:
                cleaned_amount = self._clean_financial_amount(field_value)
                is_valid = self._validate_amount_format(cleaned_amount)
                
                validations.append(FieldValidation(
                    field_name=field_name,
                    original_value=field_value,
                    corrected_value=cleaned_amount,
                    confidence=0.9 if is_valid else 0.3,
                    correction_method='amount_cleaning',
                    is_corrected=cleaned_amount != field_value
                ))
        
        return validations
    
    def _clean_financial_amount(self, amount: str) -> str:
        """Clean financial amount string."""
        if not amount:
            return ""
        
        # Remove currency symbols and clean
        cleaned = re.sub(r'[$,\s]', '', amount)
        
        # Handle parentheses for negative amounts
        if '(' in amount and ')' in amount:
            cleaned = f"-{cleaned.replace('(', '').replace(')', '')}"
        
        # Validate it's a proper number
        try:
            float(cleaned)
            return cleaned
        except ValueError:
            return amount  # Return original if can't parse
    
    def _validate_amount_format(self, amount: str) -> bool:
        """Validate that amount is in proper format."""
        if not amount:
            return False
        
        try:
            value = float(amount)
            return -999999999 <= value <= 999999999  # Reasonable range
        except ValueError:
            return False
    
    async def _validate_dates(
        self, 
        tradeline: TradelineData, 
        context: str
    ) -> List[FieldValidation]:
        """Validate date fields."""
        validations = []
        
        date_fields = [
            ('date_opened', 'Date Opened'),
            ('date_closed', 'Date Closed'),
            ('last_payment_date', 'Last Payment Date')
        ]
        
        for field_name, field_display in date_fields:
            field_value = getattr(tradeline, field_name, "")
            if field_value:
                cleaned_date = self._clean_date(field_value)
                is_valid = self._validate_date_format(cleaned_date)
                
                validations.append(FieldValidation(
                    field_name=field_name,
                    original_value=field_value,
                    corrected_value=cleaned_date,
                    confidence=0.9 if is_valid else 0.4,
                    correction_method='date_standardization',
                    is_corrected=cleaned_date != field_value
                ))
        
        return validations
    
    def _clean_date(self, date_str: str) -> str:
        """Clean and standardize date format."""
        if not date_str:
            return ""
        
        # Common date patterns and their standardized formats
        patterns = [
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', r'\1/\2/\3'),      # MM/DD/YYYY
            (r'(\d{1,2})/(\d{1,2})/(\d{2})', self._expand_year), # MM/DD/YY
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', r'\2/\3/\1'),      # YYYY-MM-DD to MM/DD/YYYY
            (r'(\d{1,2})-(\d{1,2})-(\d{4})', r'\1/\2/\3'),      # MM-DD-YYYY to MM/DD/YYYY
            (r'(\d{2})/(\d{4})', r'\1/01/\2'),                   # MM/YYYY to MM/01/YYYY
        ]
        
        for pattern, replacement in patterns:
            if callable(replacement):
                match = re.search(pattern, date_str)
                if match:
                    return replacement(match)
            else:
                result = re.sub(pattern, replacement, date_str)
                if result != date_str:
                    return result
        
        return date_str
    
    def _expand_year(self, match) -> str:
        """Expand 2-digit year to 4-digit."""
        month, day, year = match.groups()
        year_int = int(year)
        full_year = 2000 + year_int if year_int < 50 else 1900 + year_int
        return f"{month}/{day}/{full_year}"
    
    def _validate_date_format(self, date_str: str) -> bool:
        """Validate date format."""
        if not date_str:
            return False
        
        date_patterns = [
            r'^\d{1,2}/\d{1,2}/\d{4}$',  # MM/DD/YYYY
            r'^\d{2}/\d{4}$',            # MM/YYYY
        ]
        
        return any(re.match(pattern, date_str) for pattern in date_patterns)
    
    async def _validate_account_number(
        self, 
        tradeline: TradelineData, 
        context: str
    ) -> List[FieldValidation]:
        """Validate account number format."""
        validations = []
        
        if tradeline.account_number:
            cleaned_number = self._clean_account_number(tradeline.account_number)
            is_valid = self._validate_account_number_format(cleaned_number)
            
            validations.append(FieldValidation(
                field_name='account_number',
                original_value=tradeline.account_number,
                corrected_value=cleaned_number,
                confidence=0.8 if is_valid else 0.5,
                correction_method='number_cleaning',
                is_corrected=cleaned_number != tradeline.account_number
            ))
        
        return validations
    
    def _clean_account_number(self, number: str) -> str:
        """Clean account number."""
        if not number:
            return ""
        
        # Remove extra spaces and standardize masking
        cleaned = re.sub(r'\s+', '', number)
        
        # Standardize masking characters
        cleaned = re.sub(r'[*X#]', '*', cleaned)
        
        return cleaned
    
    def _validate_account_number_format(self, number: str) -> bool:
        """Validate account number format."""
        if not number:
            return False
        
        # Should contain at least some digits or masking characters
        return bool(re.search(r'[\d*X#]', number))
    
    async def _cross_validate_fields(self, tradeline: TradelineData) -> List[str]:
        """Cross-validate fields for logical consistency."""
        notes = []
        
        # Balance vs Credit Limit validation
        if tradeline.account_balance and tradeline.credit_limit:
            try:
                balance = float(tradeline.account_balance.replace('$', '').replace(',', ''))
                limit = float(tradeline.credit_limit.replace('$', '').replace(',', ''))
                
                if balance > limit * 1.1:  # Allow 10% over-limit
                    notes.append(f"Balance ({balance}) exceeds credit limit ({limit})")
            except ValueError:
                pass
        
        # Date consistency validation
        if tradeline.date_opened and tradeline.date_closed:
            # Check that close date is after open date
            # Implementation would parse dates and compare
            pass
        
        # Account type vs creditor consistency
        if tradeline.account_type and tradeline.creditor_name:
            # Check if account type matches creditor (e.g., auto loan with car company)
            pass
        
        return notes
    
    async def _openai_validate_tradeline(
        self, 
        tradeline: TradelineData, 
        context: str
    ) -> Dict[str, Any]:
        """Use OpenAI to validate and enhance tradeline data."""
        if not self.openai_client:
            return {'notes': [], 'corrections': {}}
        
        try:
            prompt = f"""
            Analyze this credit report tradeline data and provide validation feedback:
            
            Creditor: {tradeline.creditor_name}
            Account Type: {tradeline.account_type}
            Status: {tradeline.account_status}
            Balance: {tradeline.account_balance}
            Credit Limit: {tradeline.credit_limit}
            Monthly Payment: {tradeline.monthly_payment}
            Date Opened: {tradeline.date_opened}
            
            Original context: {context[:500]}...
            
            Please provide:
            1. Any corrections needed
            2. Validation notes
            3. Confidence assessment
            
            Respond in JSON format.
            """
            
            # Note: This is a placeholder - actual OpenAI integration would be implemented here
            # For now, return empty result
            return {'notes': ['AI validation not available'], 'corrections': {}}
            
        except Exception as e:
            logger.error(f"OpenAI validation failed: {e}")
            return {'notes': [f'AI validation error: {str(e)}'], 'corrections': {}}
    
    async def _calculate_ai_score(
        self, 
        tradeline: TradelineData, 
        field_validations: List[FieldValidation],
        context: str
    ) -> float:
        """Calculate AI confidence score for the tradeline."""
        if not field_validations:
            return 0.5
        
        # Base score from field validations
        field_scores = [fv.confidence for fv in field_validations]
        base_score = np.mean(field_scores)
        
        # Completeness bonus (more complete data = higher score)
        filled_fields = sum(1 for field in [
            tradeline.creditor_name, tradeline.account_type, tradeline.account_status,
            tradeline.account_balance, tradeline.credit_limit, tradeline.date_opened
        ] if field and field.strip())
        
        completeness_score = filled_fields / 6.0  # 6 essential fields
        
        # Context relevance score
        context_score = 0.5
        if context and tradeline.creditor_name:
            # Simple relevance check
            context_score = min(1.0, context.lower().count(tradeline.creditor_name.lower()) / 10)
        
        # Weighted final score
        final_score = (base_score * 0.5 + completeness_score * 0.3 + context_score * 0.2)
        
        return min(1.0, final_score)
    
    def _calculate_similarity(self, text: str, reference_list: List[str]) -> float:
        """Calculate similarity between text and reference list."""
        if not text or not reference_list or not self.tfidf_vectorizer:
            return 0.0
        
        try:
            # Transform text and reference list
            text_vector = self.tfidf_vectorizer.transform([text])
            reference_vectors = self.tfidf_vectorizer.transform(reference_list)
            
            # Calculate cosine similarity
            similarities = cosine_similarity(text_vector, reference_vectors).flatten()
            return float(np.max(similarities))
            
        except Exception as e:
            logger.warning(f"Similarity calculation failed: {e}")
            return 0.0
    
    def _find_best_match(self, text: str, reference_list: List[str]) -> str:
        """Find best match from reference list."""
        if not text or not reference_list:
            return text
        
        try:
            if self.tfidf_vectorizer:
                text_vector = self.tfidf_vectorizer.transform([text])
                reference_vectors = self.tfidf_vectorizer.transform(reference_list)
                similarities = cosine_similarity(text_vector, reference_vectors).flatten()
                best_idx = np.argmax(similarities)
                
                if similarities[best_idx] > 0.8:  # High similarity threshold
                    return reference_list[best_idx]
            
            return text  # Return original if no good match
            
        except Exception as e:
            logger.warning(f"Best match finding failed: {e}")
            return text
    
    def _update_validation_stats(
        self, 
        field_validations: List[FieldValidation], 
        corrections_made: List[str]
    ):
        """Update validation statistics."""
        self.validation_stats['total_validations'] += 1
        
        if corrections_made:
            self.validation_stats['corrections_made'] += 1
        
        for fv in field_validations:
            field_name = fv.field_name
            if field_name not in self.validation_stats['field_correction_rates']:
                self.validation_stats['field_correction_rates'][field_name] = {'total': 0, 'corrected': 0}
            
            self.validation_stats['field_correction_rates'][field_name]['total'] += 1
            if fv.is_corrected:
                self.validation_stats['field_correction_rates'][field_name]['corrected'] += 1
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics."""
        stats = self.validation_stats.copy()
        
        # Calculate correction rates
        for field_name, data in stats['field_correction_rates'].items():
            if data['total'] > 0:
                data['correction_rate'] = data['corrected'] / data['total']
            else:
                data['correction_rate'] = 0.0
        
        return stats

    async def batch_validate_tradelines(
        self, 
        tradelines: List[TradelineData],
        context_text: str = ""
    ) -> List[ValidationResult]:
        """Validate multiple tradelines in batch for efficiency."""
        logger.info(f"Starting batch validation of {len(tradelines)} tradelines")
        
        # Process in batches to avoid overwhelming the AI services
        batch_size = 5
        results = []
        
        for i in range(0, len(tradelines), batch_size):
            batch = tradelines[i:i+batch_size]
            batch_tasks = [
                self.validate_and_correct_tradeline(tradeline, context_text)
                for tradeline in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, ValidationResult):
                    results.append(result)
                else:
                    # Handle exception
                    logger.error(f"Batch validation error: {result}")
                    results.append(ValidationResult(
                        is_valid=False,
                        confidence=0.0,
                        corrected_data=TradelineData(),
                        corrections_made=[],
                        validation_notes=[f"Validation failed: {str(result)}"],
                        ai_score=0.0
                    ))
        
        logger.info(f"Batch validation completed. {sum(1 for r in results if r.is_valid)} valid tradelines")
        return results