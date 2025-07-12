import re
import json
import tiktoken # type: ignore
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class TokenCounter:
    """Token counting and management for LLM requests"""
    
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self.model_name = model_name
        self.encoding = tiktoken.encoding_for_model(model_name)
        self.total_tokens = 0
        self.session_tokens = {
            "prompt_tokens": 0,
            "completion_tokens": 0
        }
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        try:
            return len(self.encoding.encode(text))
        except Exception as e:
            logger.warning(f"Error counting tokens: {e}")
            # Fallback estimation: ~4 characters per token
            return len(text) // 4
    
    def add_tokens(self, prompt_tokens: int, completion_tokens: int):
        """Add token usage to session tracking"""
        self.session_tokens["prompt_tokens"] += prompt_tokens
        self.session_tokens["completion_tokens"] += completion_tokens
        self.total_tokens += prompt_tokens + completion_tokens
    
    def get_total_tokens(self) -> int:
        """Get total tokens used in session"""
        return self.total_tokens
    
    def get_session_stats(self) -> Dict[str, int]:
        """Get session token statistics"""
        return {
            **self.session_tokens,
            "total_tokens": self.total_tokens
        }
    
    def truncate_prompt(self, prompt: str, max_tokens: int) -> str:
        """Truncate prompt to fit within token limit"""
        tokens = self.encoding.encode(prompt)
        if len(tokens) <= max_tokens:
            return prompt
        
        # Truncate from the middle to preserve structure
        start_tokens = tokens[:max_tokens//3]
        end_tokens = tokens[-(max_tokens//3):]
        
        truncated_tokens = start_tokens + end_tokens
        truncated_text = self.encoding.decode(truncated_tokens)
        
        # Add truncation indicator
        truncated_text += "\n\n[... CONTENT TRUNCATED FOR LENGTH ...]\n\n"
        
        return truncated_text

class ResponseValidator:
    """Validate and clean LLM responses"""
    
    @staticmethod
    def validate_json_response(response: str) -> tuple[bool, Optional[dict], Optional[str]]:
        """
        Validate JSON response from LLM
        
        Returns:
            (is_valid, parsed_data, error_message)
        """
        try:
            # Clean the response
            cleaned = ResponseValidator.clean_json_response(response)
            parsed = json.loads(cleaned)
            return True, parsed, None
        except json.JSONDecodeError as e:
            return False, None, f"JSON decode error: {str(e)}"
        except Exception as e:
            return False, None, f"Validation error: {str(e)}"
    
    @staticmethod
    def clean_json_response(response: str) -> str:
        """Clean LLM response to extract valid JSON"""
        # Remove markdown code blocks
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        
        # Remove leading/trailing whitespace and explanatory text
        response = response.strip()
        
        # Find JSON object boundaries
        start_idx = response.find('{')
        if start_idx == -1:
            # Try finding array start
            start_idx = response.find('[')
        
        if start_idx >= 0:
            # Find matching closing bracket
            bracket_count = 0
            end_idx = start_idx
            start_char = response[start_idx]
            end_char = '}' if start_char == '{' else ']'
            
            for i in range(start_idx, len(response)):
                if response[i] == start_char:
                    bracket_count += 1
                elif response[i] == end_char:
                    bracket_count -= 1
                    if bracket_count == 0:
                        end_idx = i + 1
                        break
            
            response = response[start_idx:end_idx]
        
        return response
    
    @staticmethod
    def validate_tradeline_data(tradeline_data: dict) -> tuple[bool, List[str]]:
        """
        Validate tradeline data structure
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        required_fields = ["creditor_name", "account_type"]
        
        # Check required fields
        for field in required_fields:
            if field not in tradeline_data or not tradeline_data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate data types and formats
        if "balance" in tradeline_data and tradeline_data["balance"] is not None:
            try:
                Decimal(str(tradeline_data["balance"]))
            except:
                errors.append("Invalid balance format")
        
        if "date_opened" in tradeline_data and tradeline_data["date_opened"]:
            if not ResponseValidator._is_valid_date_string(tradeline_data["date_opened"]):
                errors.append("Invalid date_opened format")
        
        # Validate confidence score
        if "confidence_score" in tradeline_data:
            score = tradeline_data["confidence_score"]
            if not isinstance(score, (int, float)) or score < 0 or score > 1:
                errors.append("Invalid confidence_score (must be 0-1)")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _is_valid_date_string(date_string: str) -> bool:
        """Check if string is a valid date format"""
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{2}/\d{2}/\d{4}$',  # MM/DD/YYYY
            r'^\d{2}-\d{2}-\d{4}$',  # MM-DD-YYYY
        ]
        
        return any(re.match(pattern, date_string) for pattern in date_patterns)

class DataNormalizer:
    """Utilities for normalizing extracted data"""
    
    @staticmethod
    def normalize_currency(value: Any) -> Optional[Decimal]:
        """Normalize currency values to Decimal"""
        if value is None:
            return None
        
        if isinstance(value, (int, float, Decimal)):
            return Decimal(str(value))
        
        if isinstance(value, str):
            # Remove currency symbols and formatting
            cleaned = re.sub(r'[$,\s]', '', value.strip())
            
            # Handle parentheses as negative
            if cleaned.startswith('(') and cleaned.endswith(')'):
                cleaned = '-' + cleaned[1:-1]
            
            try:
                return Decimal(cleaned)
            except:
                return None
        
        return None
    
    @staticmethod
    def normalize_date(value: Any) -> Optional[date]:
        """Normalize date values"""
        if value is None:
            return None
        
        if isinstance(value, date):
            return value
        
        if isinstance(value, datetime):
            return value.date()
        
        if isinstance(value, str):
            # Try common date formats
            date_formats = [
                "%Y-%m-%d",
                "%m/%d/%Y",
                "%m-%d-%Y",
                "%Y/%m/%d",
                "%d/%m/%Y",
                "%B %d, %Y",
                "%b %d, %Y"
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(value.strip(), fmt).date()
                except:
                    continue
        
        return None
    
    @staticmethod
    def normalize_account_type(value: str) -> str:
        """Normalize account type to standard categories"""
        if not value:
            return "Unknown"
        
        value_lower = value.lower().strip()
        
        # Account type mappings
        type_mappings = {
            "credit card": ["credit card", "cc", "visa", "mastercard", "amex", "discover"],
            "mortgage": ["mortgage", "home loan", "real estate"],
            "auto loan": ["auto", "car loan", "vehicle", "automobile"],
            "student loan": ["student", "education", "sallie mae"],
            "personal loan": ["personal", "signature", "unsecured"],
            "line of credit": ["line of credit", "loc", "credit line", "heloc"],
            "installment": ["installment", "term loan"],
            "collection": ["collection", "charged off", "charge off"]
        }
        
        for standard_type, variations in type_mappings.items():
            if any(variation in value_lower for variation in variations):
                return standard_type.title()
        
        return value.title()
    
    @staticmethod
    def normalize_payment_status(value: str) -> str:
        """Normalize payment status to standard terms"""
        if not value:
            return "Unknown"
        
        value_lower = value.lower().strip()
        
        # Status mappings
        status_mappings = {
            "current": ["current", "ok", "pays as agreed", "on time"],
            "30 days late": ["30", "30 days", "30 day"],
            "60 days late": ["60", "60 days", "60 day"],
            "90 days late": ["90", "90 days", "90 day"],
            "120+ days late": ["120", "120+", "120 days", "120 day"],
            "charged off": ["charged off", "charge off", "co"],
            "collection": ["collection", "collections"],
            "settled": ["settled", "settlement"],
            "paid": ["paid", "paid in full", "closed"]
        }
        
        for standard_status, variations in status_mappings.items():
            if any(variation in value_lower for variation in variations):
                return standard_status
        
        return value.title()

class ConfidenceCalculator:
    """Calculate confidence scores for extracted data"""
    
    @staticmethod
    def calculate_tradeline_confidence(
        tradeline_data: dict,
        source_quality: float = 1.0
    ) -> float:
        """Calculate confidence score for a tradeline"""
        
        # Base confidence factors
        factors = {
            "completeness": 0.0,
            "data_quality": 0.0,
            "consistency": 0.0,
            "format_validity": 0.0
        }
        
        # Completeness factor (40% weight)
        required_fields = ["creditor_name", "account_type"]
        optional_fields = ["balance", "credit_limit", "payment_status", "date_opened"]
        
        completeness = len([f for f in required_fields if f in tradeline_data and tradeline_data[f]]) / len(required_fields)
        completeness += 0.5 * len([f for f in optional_fields if f in tradeline_data and tradeline_data[f]]) / len(optional_fields)
        factors["completeness"] = min(completeness, 1.0) * 0.4
        
        # Data quality factor (30% weight)
        quality_score = 1.0
        if "balance" in tradeline_data:
            try:
                Decimal(str(tradeline_data["balance"]))
            except:
                quality_score -= 0.2
        
        if "date_opened" in tradeline_data and tradeline_data["date_opened"]:
            if not ResponseValidator._is_valid_date_string(str(tradeline_data["date_opened"])):
                quality_score -= 0.2
        
        factors["data_quality"] = max(quality_score, 0.0) * 0.3
        
        # Consistency factor (20% weight)
        # Check for logical consistency
        consistency_score = 1.0
        # Add consistency checks here
        factors["consistency"] = consistency_score * 0.2
        
        # Format validity factor (10% weight)
        # Check if data follows expected formats
        format_score = 1.0
        # Add format validation here
        factors["format_validity"] = format_score * 0.1
        
        # Combine factors with source quality
        total_confidence = sum(factors.values()) * source_quality
        
        return round(min(max(total_confidence, 0.0), 1.0), 3)