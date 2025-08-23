"""
LLM Parser Service
Handles AI-powered parsing of credit reports using Gemini AI
"""
import json
import asyncio
import time
import re
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
from decimal import Decimal
import logging

# Gemini AI imports (with error handling)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False

# Local utilities
try:
    from utils.text_parsing import parse_tradelines_basic
except ImportError:
    def parse_tradelines_basic(text):
        return []

logger = logging.getLogger(__name__)


class GeminiProcessor:
    """Enhanced Gemini processor with comprehensive error handling"""
    
    def __init__(self, api_key: str = None):
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if GEMINI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.logger.info("✅ GeminiProcessor initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Gemini: {e}")
                self.model = None
        else:
            self.model = None
            self.logger.warning("⚠️ GeminiProcessor initialized but Gemini AI not available")

    async def extract_tradelines(self, text: str, max_retries: int = 3) -> List[Dict[str, Any]]:
        """
        Extract tradelines from credit report text using Gemini AI with comprehensive error handling
        """
        if not self.model:
            self.logger.warning("Gemini not available, using fallback parsing")
            return parse_tradelines_basic(text)
        
        if not text or len(text.strip()) < 50:
            self.logger.warning("Text too short for meaningful extraction")
            return []

        # Enhanced prompt for better tradeline extraction
        prompt = f"""
Extract tradeline information from this credit report text. Each tradeline should be a separate account/loan.

TEXT:
{text[:8000]}  

Return a JSON list of tradeline objects. Each object should have these fields:
- creditor_name: Name of the creditor/lender
- account_number: Account number (mask sensitive digits if needed)
- account_type: Type (Credit Card, Auto Loan, Mortgage, Personal Loan, etc.)
- account_status: Status (Open, Closed, Charge Off, etc.)
- account_balance: Current balance amount (as string)
- credit_limit: Credit limit or original amount (as string)
- monthly_payment: Monthly payment amount (as string)
- date_opened: Date account was opened (MM/DD/YYYY format)
- credit_bureau: Which bureau reported this (Experian, Equifax, TransUnion)
- is_negative: true if this is a negative account (collections, charge-offs, etc.)
- dispute_count: number of times disputed (0 if not mentioned)

Only include actual account information, not personal info or credit scores. 
Return empty list [] if no tradelines found.

JSON Response:
"""

        for attempt in range(max_retries):
            try:
                self.logger.debug(f"Attempting Gemini extraction (attempt {attempt + 1})")
                
                # Generate content with timeout
                response = await asyncio.wait_for(
                    self._generate_content_async(prompt),
                    timeout=30.0
                )
                
                if not response or not response.text:
                    self.logger.warning(f"Empty response from Gemini on attempt {attempt + 1}")
                    continue
                
                # Clean and parse response
                response_text = response.text.strip()
                self.logger.debug(f"Raw Gemini response: {response_text[:200]}...")
                
                # Extract JSON from response
                tradelines = self._extract_json_from_response(response_text)
                
                if tradelines is None:
                    self.logger.warning(f"Failed to parse JSON on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)
                        continue
                    else:
                        return parse_tradelines_basic(text)
                
                # Validate and clean tradelines
                valid_tradelines = []
                for i, tradeline in enumerate(tradelines):
                    if self._validate_tradeline_data(tradeline):
                        # Clean and normalize the tradeline
                        cleaned_tradeline = self._clean_tradeline_data(tradeline)
                        valid_tradelines.append(cleaned_tradeline)
                    else:
                        self.logger.debug(f"Invalid tradeline {i}: {tradeline}")
                
                self.logger.info(f"✅ Gemini extracted {len(valid_tradelines)} valid tradelines")
                return valid_tradelines
                
            except asyncio.TimeoutError:
                self.logger.warning(f"Gemini request timed out on attempt {attempt + 1}")
            except Exception as e:
                self.logger.error(f"Gemini extraction error on attempt {attempt + 1}: {str(e)}")
            
            # Wait before retry
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
        
        # All attempts failed, use fallback
        self.logger.warning("All Gemini attempts failed, using fallback parser")
        return parse_tradelines_basic(text)

    async def _generate_content_async(self, prompt: str):
        """Generate content asynchronously"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.model.generate_content, prompt)

    def _extract_json_from_response(self, response_text: str) -> Optional[List[Dict]]:
        """Extract JSON array from Gemini response with multiple strategies"""
        
        # Strategy 1: Look for JSON array markers
        json_patterns = [
            r'\[[\s\S]*\]',  # Find content between [ and ]
            r'```json\s*([\s\S]*?)\s*```',  # Extract from code blocks
            r'```\s*([\s\S]*?)\s*```',  # Extract from any code blocks
        ]
        
        for pattern in json_patterns:
            matches = re.finditer(pattern, response_text, re.MULTILINE | re.DOTALL)
            for match in matches:
                try:
                    json_str = match.group(1) if '```' in pattern else match.group(0)
                    json_str = json_str.strip()
                    
                    if json_str.startswith('[') and json_str.endswith(']'):
                        parsed = json.loads(json_str)
                        if isinstance(parsed, list):
                            return parsed
                except json.JSONDecodeError:
                    continue
        
        # Strategy 2: Try to parse the entire response as JSON
        try:
            parsed = json.loads(response_text)
            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict) and 'tradelines' in parsed:
                return parsed['tradelines']
        except json.JSONDecodeError:
            pass
        
        # Strategy 3: Look for individual objects and combine
        object_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        objects = re.findall(object_pattern, response_text)
        tradelines = []
        
        for obj_str in objects:
            try:
                obj = json.loads(obj_str)
                if self._looks_like_tradeline(obj):
                    tradelines.append(obj)
            except json.JSONDecodeError:
                continue
        
        return tradelines if tradelines else None

    def _looks_like_tradeline(self, obj: Dict) -> bool:
        """Check if object looks like a tradeline"""
        tradeline_fields = ['creditor_name', 'account_number', 'account_type', 'creditor', 'account']
        return any(field in str(obj).lower() for field in tradeline_fields)

    def _validate_tradeline_data(self, tradeline: Dict) -> bool:
        """Validate that tradeline has required fields"""
        if not isinstance(tradeline, dict):
            return False
        
        # Must have creditor name
        creditor_name = tradeline.get('creditor_name', '').strip()
        if not creditor_name:
            return False
        
        # Must have some form of account identifier
        account_number = tradeline.get('account_number', '').strip()
        if not account_number or account_number.lower() in ['unknown', 'n/a', 'null', 'none']:
            return False
        
        return True

    def _clean_tradeline_data(self, tradeline: Dict) -> Dict[str, Any]:
        """Clean and normalize tradeline data"""
        cleaned = {
            'creditor_name': str(tradeline.get('creditor_name', '')).strip(),
            'account_number': str(tradeline.get('account_number', '')).strip(),
            'account_type': str(tradeline.get('account_type', 'Credit Card')).strip(),
            'account_status': str(tradeline.get('account_status', 'Open')).strip(),
            'account_balance': self._clean_amount(tradeline.get('account_balance', '')),
            'credit_limit': self._clean_amount(tradeline.get('credit_limit', '')),
            'monthly_payment': self._clean_amount(tradeline.get('monthly_payment', '')),
            'date_opened': self._clean_date(tradeline.get('date_opened', '')),
            'credit_bureau': str(tradeline.get('credit_bureau', '')).strip(),
            'is_negative': bool(tradeline.get('is_negative', False)),
            'dispute_count': int(tradeline.get('dispute_count', 0)) if str(tradeline.get('dispute_count', 0)).isdigit() else 0
        }
        
        return cleaned

    def _clean_amount(self, amount: Any) -> str:
        """Clean amount field"""
        if not amount:
            return ""
        
        amount_str = str(amount).strip()
        # Remove common prefixes/suffixes
        amount_str = re.sub(r'^[\$\£\€]', '', amount_str)
        amount_str = re.sub(r'[,\s]', '', amount_str)
        
        # Validate it's a number-like string
        if re.match(r'^\d+\.?\d*$', amount_str):
            return amount_str
        
        return ""

    def _clean_date(self, date_val: Any) -> str:
        """Clean date field"""
        if not date_val:
            return ""
        
        date_str = str(date_val).strip()
        
        # Try to parse and reformat common date formats
        date_formats = ['%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y', '%d/%m/%Y']
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime('%m/%d/%Y')  # Standardize format
            except ValueError:
                continue
        
        # If no format worked, return as-is if it looks date-like
        if re.match(r'^\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}$', date_str):
            return date_str
        
        return ""

    def extract_structured_data(self, text: str) -> Dict[str, Any]:
        """Legacy sync method for backward compatibility"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            tradelines = loop.run_until_complete(self.extract_tradelines(text))
            return {
                'tradelines': tradelines,
                'extracted_with': 'gemini',
                'success': True
            }
        except Exception as e:
            self.logger.error(f"Sync extraction failed: {e}")
            return {
                'tradelines': [],
                'extracted_with': 'fallback',
                'success': False,
                'error': str(e)
            }
        finally:
            loop.close()