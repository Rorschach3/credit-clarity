import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
from decimal import Decimal
import logging
from dataclasses import dataclass

from ..models.tradeline_models import Tradeline, CreditReport, ConsumerInfo
from ..models.llm_models import LLMRequest, LLMResponse, NormalizationResult
from ..config.llm_config import LLMConfig
from ..utils.llm_helpers import TokenCounter, ResponseValidator
from .prompt_templates import PromptTemplates

logger = logging.getLogger(__name__)

@dataclass
class ProcessingContext:
    """Context for LLM processing operations"""
    job_id: str
    document_type: str
    confidence_threshold: float = 0.7
    max_retries: int = 3

class LLMParserService:
    """Service for parsing and normalizing document data using LLM"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = AsyncOpenAI(api_key=config.openai_api_key) # type: ignore
        self.token_counter = TokenCounter()
        self.response_validator = ResponseValidator()
        self.prompt_templates = PromptTemplates()
        
    async def normalize_tradeline_data(
        self, 
        raw_text: str, 
        table_data: List[Dict], 
        context: ProcessingContext
    ) -> NormalizationResult:
        """
        Main method to normalize tradeline data using LLM
        
        Args:
            raw_text: Raw text from Document AI
            table_data: Structured table data from Document AI
            context: Processing context with job details
            
        Returns:
            NormalizationResult with normalized data and metadata
        """
        try:
            logger.info(f"Starting LLM normalization for job {context.job_id}")
            
            # Step 1: Extract structured data from raw text
            structured_data = await self._extract_structured_data(
                raw_text, table_data, context
            )
            
            # Step 2: Normalize tradeline information
            normalized_tradelines = await self._normalize_tradelines(
                structured_data, context
            )
            
            # Step 3: Extract consumer information
            consumer_info = await self._extract_consumer_info(
                raw_text, context
            )
            
            # Step 4: Validate and generate confidence scores
            validation_results = await self._validate_and_score(
                normalized_tradelines, consumer_info, context
            )
            
            # Step 5: Create final normalized result
            result = NormalizationResult(
                job_id=context.job_id,
                consumer_info=consumer_info,
                tradelines=normalized_tradelines,
                validation_results=validation_results,
                confidence_score=validation_results.overall_confidence,
                processing_metadata={
                    "processed_at": datetime.utcnow().isoformat(),
                    "model_used": self.config.model_name,
                    "tokens_used": self.token_counter.get_total_tokens(),
                    "processing_duration": None  # Will be set by caller
                }
            )
            
            logger.info(f"LLM normalization completed for job {context.job_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error in LLM normalization for job {context.job_id}: {str(e)}")
            raise
    
    async def _extract_structured_data(
        self, 
        raw_text: str, 
        table_data: List[Dict], 
        context: ProcessingContext
    ) -> Dict[str, Any]:
        """Extract structured data from raw text and tables"""
        
        prompt = self.prompt_templates.get_extraction_prompt(
            raw_text=raw_text,
            table_data=table_data,
            document_type=context.document_type
        )
        
        response = await self._make_llm_request(
            prompt=prompt,
            context=context,
            operation="data_extraction"
        )
        
        try:
            structured_data = json.loads(response)
            return structured_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            # Attempt to clean and re-parse
            cleaned_response = self._clean_json_response(response)
            return json.loads(cleaned_response)
    
    async def _normalize_tradelines(
        self, 
        structured_data: Dict[str, Any], 
        context: ProcessingContext
    ) -> List[Tradeline]:
        """Normalize tradeline data into standard format"""
        
        tradelines = []
        raw_tradelines = structured_data.get("tradelines", [])
        
        for idx, raw_tradeline in enumerate(raw_tradelines):
            try:
                # Create normalization prompt for individual tradeline
                prompt = self.prompt_templates.get_tradeline_normalization_prompt(
                    raw_tradeline=raw_tradeline,
                    context=context
                )
                
                response = await self._make_llm_request(
                    prompt=prompt,
                    context=context,
                    operation=f"tradeline_normalization_{idx}"
                )
                
                # Parse and validate tradeline
                normalized_data = json.loads(response)
                tradeline = self._create_tradeline_from_normalized_data(
                    normalized_data, raw_tradeline
                )
                
                tradelines.append(tradeline)
                
            except Exception as e:
                logger.error(f"Error normalizing tradeline {idx}: {str(e)}")
                # Create a basic tradeline with available data
                fallback_tradeline = self._create_fallback_tradeline(raw_tradeline)
                tradelines.append(fallback_tradeline)
        
        return tradelines
    
    async def _extract_consumer_info(
        self, 
        raw_text: str, 
        context: ProcessingContext
    ) -> ConsumerInfo:
        """Extract consumer information from document"""
        
        prompt = self.prompt_templates.get_consumer_info_prompt(
            raw_text=raw_text,
            context=context
        )
        
        response = await self._make_llm_request(
            prompt=prompt,
            context=context,
            operation="consumer_info_extraction"
        )
        
        try:
            consumer_data = json.loads(response)
            return ConsumerInfo(**consumer_data)
        except Exception as e:
            logger.error(f"Error extracting consumer info: {str(e)}")
            return ConsumerInfo(
                name="Unknown",
                ssn=None,
                date_of_birth=None,
                addresses=[],
                confidence_score=0.0
            )
    
    async def _validate_and_score(
        self, 
        tradelines: List[Tradeline], 
        consumer_info: ConsumerInfo, 
        context: ProcessingContext
    ) -> Any:  # ValidationResult type
        """Validate normalized data and generate confidence scores"""
        
        # Create validation prompt
        prompt = self.prompt_templates.get_validation_prompt(
            tradelines=tradelines,
            consumer_info=consumer_info,
            context=context
        )
        
        response = await self._make_llm_request(
            prompt=prompt,
            context=context,
            operation="validation"
        )
        
        try:
            validation_data = json.loads(response)
            return self._create_validation_result(validation_data)
        except Exception as e:
            logger.error(f"Error in validation: {str(e)}")
            return self._create_default_validation_result()
    
    async def _make_llm_request(
        self, 
        prompt: str, 
        context: ProcessingContext, 
        operation: str,
        max_tokens: int = 4000
    ) -> str:
        """Make request to LLM with retry logic"""
        
        for attempt in range(context.max_retries):
            try:
                # Count tokens before making request
                token_count = self.token_counter.count_tokens(prompt)
                
                if token_count > self.config.max_tokens - max_tokens:
                    # Truncate prompt if too long
                    prompt = self.token_counter.truncate_prompt(
                        prompt, 
                        self.config.max_tokens - max_tokens
                    )
                
                response = await self.client.chat.completions.create(
                    model=self.config.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": self.config.system_prompt
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=max_tokens,
                    temperature=self.config.temperature,
                    top_p=self.config.top_p
                )
                
                content = response.choices[0].message.content
                
                # Track token usage
                self.token_counter.add_tokens(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens
                )
                
                logger.info(f"LLM request successful for operation: {operation}")
                return content
                
            except Exception as e:
                logger.error(f"LLM request failed (attempt {attempt + 1}): {str(e)}")
                if attempt == context.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    def _create_tradeline_from_normalized_data(
        self, 
        normalized_data: Dict[str, Any], 
        raw_data: Dict[str, Any]
    ) -> Tradeline:
        """Create Tradeline object from normalized data"""
        
        return Tradeline(
            creditor_name=normalized_data.get("creditor_name", "Unknown"),
            account_number=normalized_data.get("account_number", ""),
            account_type=normalized_data.get("account_type", "Unknown"),
            balance=self._safe_decimal_conversion(normalized_data.get("balance")),
            credit_limit=self._safe_decimal_conversion(normalized_data.get("credit_limit")),
            payment_status=normalized_data.get("payment_status", "Unknown"),
            date_opened=self._safe_date_conversion(normalized_data.get("date_opened")),
            date_closed=self._safe_date_conversion(normalized_data.get("date_closed")),
            payment_history=normalized_data.get("payment_history", []),
            confidence_score=normalized_data.get("confidence_score", 0.5),
            original_data=raw_data  # Keep original for reference
        )
    
    def _create_fallback_tradeline(self, raw_data: Dict[str, Any]) -> Tradeline:
        """Create basic tradeline when normalization fails"""
        return Tradeline(
            creditor_name=raw_data.get("creditor", "Unknown"),
            account_number=raw_data.get("account", ""),
            account_type="Unknown",
            balance=None,
            credit_limit=None,
            payment_status="Unknown",
            date_opened=None,
            date_closed=None,
            payment_history=[],
            confidence_score=0.1,
            original_data=raw_data
        )
    
    def _safe_decimal_conversion(self, value: Any) -> Optional[Decimal]:
        """Safely convert value to Decimal"""
        if value is None:
            return None
        try:
            # Remove common currency symbols and commas
            if isinstance(value, str):
                cleaned = value.replace("$", "").replace(",", "").strip()
                return Decimal(cleaned)
            return Decimal(str(value))
        except:
            return None
    
    def _safe_date_conversion(self, value: Any) -> Optional[date]:
        """Safely convert value to date"""
        if value is None:
            return None
        try:
            if isinstance(value, str):
                # Handle common date formats
                from dateutil.parser import parse # type: ignore
                return parse(value).date()
            return value
        except:
            return None
    
    def _clean_json_response(self, response: str) -> str:
        """Clean LLM response to extract valid JSON"""
        # Remove code blocks
        response = response.replace("```json", "").replace("```", "")
        
        # Find JSON object boundaries
        start_idx = response.find("{")
        end_idx = response.rfind("}") + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            return response[start_idx:end_idx]
        
        return response
    
    def _create_validation_result(self, validation_data: Dict[str, Any]) -> Any:
        """Create validation result from LLM response"""
        # This would create a proper ValidationResult object
        # Implementation depends on your validation model structure
        pass
    
    def _create_default_validation_result(self) -> Any:
        """Create default validation result when validation fails"""
        # This would create a default ValidationResult object
        # Implementation depends on your validation model structure
        pass