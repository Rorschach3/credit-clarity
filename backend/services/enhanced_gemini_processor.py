"""
Enhanced Gemini Processor for Credit Report Analysis
Provides refined Gemini AI integration with improved prompts and validation
"""
import os
import logging
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

# Gemini AI imports (with error handling)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False
    # Note: logger not yet configured at this point

from dotenv import load_dotenv
load_dotenv()

from services.advanced_parsing.negative_tradeline_classifier import NegativeTradelineClassifier

logger = logging.getLogger(__name__)

# Environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini
gemini_model = None
if GEMINI_AVAILABLE and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-2.5-flash')
        logger.info("✅ Enhanced Gemini processor initialized")
    except Exception as e:
        logger.error(f"❌ Gemini initialization failed: {e}")
        gemini_model = None


class EnhancedGeminiProcessor:
    """
    Enhanced Gemini processor with refined prompts and comprehensive validation
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gemini_available = GEMINI_AVAILABLE and gemini_model is not None
        self.negative_classifier = NegativeTradelineClassifier()

        if not self.gemini_available:
            self.logger.warning("⚠️ Enhanced Gemini processor initialized but Gemini AI not available")

    def extract_tradelines(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract tradelines using enhanced Gemini AI with comprehensive error handling
        """
        try:
            self.logger.info(f"🧠 Starting enhanced Gemini tradeline extraction from {len(text)} characters")

            # Check if Gemini is available
            if not self.gemini_available:
                self.logger.warning("⚠️ Gemini not available - using fallback basic parsing")
                return self._fallback_basic_parsing(text)

            if not gemini_model:
                self.logger.error("❌ Gemini model not initialized")
                return self._fallback_basic_parsing(text)

            # If text is too long, process in chunks (but limit total processing time)
            if len(text) > 20000:  # Increased threshold
                return self._extract_tradelines_chunked(text)
            else:
                return self._extract_tradelines_single(text)

        except ImportError as e:
            self.logger.error(f"❌ Import error in enhanced Gemini processing: {str(e)}")
            return self._fallback_basic_parsing(text)
        except Exception as e:
            self.logger.error(f"❌ Enhanced Gemini processing failed: {str(e)}")
            return self._fallback_basic_parsing(text)

    def _extract_tradelines_single(self, text: str) -> List[Dict[str, Any]]:
        """Extract tradelines from a single text chunk with enhanced error handling"""
        try:
            self.logger.info("🧠 ENHANCED GEMINI EXTRACTION - INPUT DATA:")
            self.logger.info(f"  Text length: {len(text)} characters")

            # Double-check Gemini availability
            if not self.gemini_available or not gemini_model:
                self.logger.warning("⚠️ Gemini not available during single extraction")
                return self._fallback_basic_parsing(text)

            prompt = f"""
            You are analyzing a credit report section. Your job is to extract ALL tradeline information comprehensively.

            CRITICAL: Extract EVERY account mentioned, including both positive and negative accounts.

            Extract each tradeline as a JSON object with these exact fields:
            {{
                "creditor_name": "Bank/Company name (e.g., CHASE CARD, SCHOOLSFIRST FEDERAL CREDIT UNION, CAPITAL ONE)",
                "account_number": "Account number with masking (e.g., ****1234, 755678...., XXXX-XXXX-XXXX-1234)",
                "account_balance": "Current balance amount (e.g., $1,975, $808, $0 for paid accounts)",
                "credit_limit": "Credit limit or high credit amount (e.g., $2,000, $500)",
                "monthly_payment": "Monthly payment amount (e.g., $40, $174, $0 for paid accounts)",
                "date_opened": "CRITICAL: Date account was opened - ALWAYS normalize to MM/DD/YYYY format (e.g., 01/15/2024)",
                "date_closed": "Date account was closed (if applicable) - normalize to MM/DD/YYYY format",
                "last_payment_date": "Date of last payment - normalize to MM/DD/YYYY format",
                "account_type": "Credit Card, Auto Loan, Mortgage, Installment, Personal Loan, Student Loan, Secured Card, Store Card",
                "account_status": "Current, Open, Closed, Paid Closed, Account charged off, Collection, Late, Satisfactory, etc.",
                "is_negative": true if account has problems (charged off, collection, late payments, past due), false for current/good accounts,
                "reasoning": "1-2 sentences explaining why is_negative is true/false, referencing status or payment history"
            }}

            COMPREHENSIVE EXTRACTION RULES:

            📅 DATE EXTRACTION AND NORMALIZATION (MOST IMPORTANT):
            ALL dates MUST be normalized to MM/DD/YYYY format. Follow these rules:
            
            🔍 RECOGNIZE THESE DATE FORMATS:
            - Month-name formats: "Jan 10", "January 10, 2024", "Jan 2024", "10 Jan 2024"
            - ISO dates: "2024-01-15", "2024-1-5"  
            - MM/DD/YY: "01/15/24", "1/5/24"
            - MM/DD/YYYY: "01/15/2024"
            - MM-YY: "01-24"
            - MM-YYYY: "01-2024"
            - MM/YY: "01/24", "1/24"
            - MM/YYYY: "01/2024"
            
            🔄 NORMALIZATION RULES:
            - ALWAYS output dates as MM/DD/YYYY (e.g., "01/15/2024")
            - For month/year only inputs (MM/YYYY, MM-YY, "Jan 2024"), default day to 01:
              * "01/2024" → "01/01/2024"
              * "Jan 2024" → "01/01/2024"
              * "01-24" → "01/01/2024"
              * "1/24" → "01/01/2024"
            - For 2-digit years, use cutoff of 50:
              * 00-49 → 2000-2049 (e.g., "01/15/24" → "01/15/2024")
              * 50-99 → 1950-1999 (e.g., "01/15/85" → "01/15/1985")
            - Convert month names to numbers:
              * "January 10, 2024" → "01/10/2024"
              * "Jan 10" → "01/10/2025" (use current year if not specified)
            
            📅 DATE EXTRACTION EXAMPLES:
            
            FULL DATES (with day):
            ✅ "01/15/2024" → "01/15/2024" (no change)
            ✅ "01/15/24" → "01/15/2024" (2-digit year expanded)
            ✅ "2024-01-15" → "01/15/2024" (ISO converted)
            ✅ "January 15, 2024" → "01/15/2024" (month name)
            ✅ "Jan 15, 2024" → "01/15/2024" (short month)
            ✅ "15 Jan 2024" → "01/15/2024" (day-first format)
            ✅ "Jan 15" → "01/15/2025" (current year assumed)
            
            MONTH NAMES (partial - day defaults to 01):
            ✅ "Jan 2024" → "01/01/2024"
            ✅ "January 2024" → "01/01/2024"
            ✅ "Jan 24" → "01/01/2024" (2-digit year)
            ✅ "December 2019" → "12/01/2019"
            
            PARTIAL DATES (day defaults to 01):
            ✅ "01/2024" → "01/01/2024"
            ✅ "1/24" → "01/01/2024"
            ✅ "01-2024" → "01/01/2024"
            ✅ "01-24" → "01/01/2024"
            ✅ "12/2019" → "12/01/2019"
            
            📍 WHERE TO FIND DATES:
            - Search for "Date Opened:", "Opened:", "Since:", "Date Open:", "Open Date:" patterns
            - Look for "Date Closed:", "Closed:", "Close Date:" patterns
            - Search for "Last Payment:", "Last Pmt:", "Last Activity:" patterns
            - Check text immediately before and after each creditor name
            - Don't skip if date format is unusual - extract and normalize any reasonable date pattern
            
            EXTRACTION FROM TEXT EXAMPLES:
            ✅ "Opened: Jan 2014" → date_opened: "01/01/2014"
            ✅ "Date Opened: 01/2014" → date_opened: "01/01/2014"
            ✅ "Since: 2024-01-15" → date_opened: "01/15/2024"
            ✅ "Opened 01/15/24" → date_opened: "01/15/2024"
            ✅ "January 10, 2024" → "01/10/2024"
            ✅ "Closed: 12-23" → date_closed: "12/01/2023"
            ✅ "Last Payment: Feb 2024" → last_payment_date: "02/01/2024"

            📊 ACCOUNT TYPES TO FIND:
            - Credit Cards: Chase, Capital One, Discover, Amex, store cards
            - Auto Loans: Ford Credit, GM Financial, Toyota Financial, etc.
            - Mortgages: Wells Fargo, Bank of America, Quicken Loans
            - Personal/Installment Loans: OneMain, Avant, LendingClub
            - Student Loans: Great Lakes, Navient, Federal loans
            - Secured Cards: Capital One Secured, Discover Secured

            ✅ POSITIVE ACCOUNTS (Don't Skip These!):
            - Accounts marked "Current", "Paid as Agreed", "Satisfactory"
            - Accounts "In Good Standing", "Open", "Never Late"
            - Closed accounts that were "Paid in Full", "Paid Closed"
            - Zero balance accounts that are current

            🚨 NEGATIVE ACCOUNT DETECTION (CRITICAL):
            You MUST accurately identify negative accounts. Set "is_negative": true for ANY of these:
            CHARGE-OFFS:
            - "Charge Off", "Charged Off", "Chargeoff", "Paid Charge Off"
            - Example: "CAPITAL ONE - Account Status: CHARGE OFF, Balance: $2,500"
            COLLECTIONS:
            - "Collection", "Collections", "In Collection", "Placed for Collection"
            - Example: "MIDLAND FUNDING LLC - Collection Account, Balance: $1,892"
            LATE PAYMENTS:
            - "Late 30 Days", "Late 60 Days", "Late 90 Days", "Late 120+ Days"
            - "30 Days Past Due", "60 Days Past Due", "90 Days Past Due"
            - "Past Due", "Delinquent", "Seriously Delinquent"
            - Example: "SYNCHRONY BANK - 60 DAYS PAST DUE, Balance: $1,750"
            DEFAULTS & REPOSSESSIONS:
            - "Default", "Defaulted", "Repossession", "Repo", "Voluntary Surrender"
            - Example: "FORD CREDIT - Repossession, Balance: $8,500"
            FORECLOSURES:
            - "Foreclosure", "Foreclosed", "Pre-Foreclosure"
            - Example: "WELLS FARGO MORTGAGE - Foreclosure, Balance: $125,000"
            SETTLEMENTS:
            - "Settled", "Settlement", "Settled for Less", "Settled Less Than Full Balance"
            - Example: "DISCOVER CARD - Settled, Original Balance: $5,000, Settled: $2,000"
            BANKRUPTCY:
            - "Bankruptcy", "Chapter 7", "Chapter 13", "Included in Bankruptcy", "Discharged"
            - Example: "CHASE CARD - Included in Chapter 7 Bankruptcy"
            ⚠️ IMPORTANT DISTINCTIONS:
            - "Closed" with $0 balance and "Paid as Agreed" = is_negative: false (POSITIVE)
            - "Closed" with balance > $0 or negative remarks = is_negative: true (NEGATIVE)
            - "Current" or "Open" with late payment history = is_negative: true (NEGATIVE)
            - "Paid Charge Off" = is_negative: true (still negative even if paid)
            ✅ POSITIVE ACCOUNTS (is_negative: false):
            - "Current", "Open", "Paid as Agreed", "Good Standing", "Never Late"
            - "Closed - Paid in Full", "Paid Closed", "Satisfactory"
            - Zero balance with no negative history
            EXTRACTION RULE: When in doubt, check the account status AND payment history together.

            🔍 MISSING FIELD INFERENCE FOR NEGATIVE ACCOUNTS:
            When extracting negative accounts, if fields are missing, infer from context:
            - If "charge off" status but no balance: Look for "charged off amount" nearby
            - If "collection" status but no creditor: Look for collection agency name in surrounding text
            - If negative status but no date_opened: Search for "opened", "since", or "date opened" within 200 characters
            - If no monthly_payment for collection: Default to "$0.00" (collections typically don't have monthly payments)
            - If no credit_limit for charge-off: Use account_balance as estimate
            - Always include reasoning field explaining any inferences made

            🎯 SECTION-SPECIFIC GUIDANCE:
            - Positive sections: Focus on current, good standing accounts
            - Negative sections: Include all derogatory accounts
            - Mixed sections: Extract both positive and negative
            - Account summaries: Often contain the most complete information
            - MULTIPLE ACCOUNTS PER CREDITOR: When you see the same creditor multiple times (e.g., SCHOOLSFIRST appears 4 times), extract EACH occurrence as a separate account

            🔧 TECHNICAL RULES:
            - Extract partial account numbers: ****1234, XXXX-XXXX-XXXX-5678
            - Include $0 balances for paid accounts
            - Map store cards as "Credit Card" type
            - Mark closed good accounts as NOT negative (is_negative: false)

            EXAMPLES OF WHAT TO EXTRACT:
            ✅ "CHASE CARD ****1234 - Current, $500 balance, $2000 limit, Opened 01/2015" → date_opened: "01/01/2015"
            ✅ "AUTO LOAN - Ford Credit, Paid Closed, $0 balance, Opened 03/2018" → date_opened: "03/01/2018"
            ✅ "DISCOVER CARD - Good Standing, $0 balance, Opened 12/2020" → date_opened: "12/01/2020"
            ✅ "STUDENT LOAN - Great Lakes, Current, $15000 balance, Since 09/2016" → date_opened: "09/01/2016"

            🚨 CRITICAL: If you see the SAME CREDITOR multiple times with DIFFERENT account numbers or account types, they are SEPARATE ACCOUNTS:
            ✅ "SCHOOLSFIRST - Checking Account 420973****" = Account 1
            ✅ "SCHOOLSFIRST - Savings Account 755678****" = Account 2
            ✅ "SCHOOLSFIRST - Auto Loan 755678...." = Account 3
            ✅ "SCHOOLSFIRST - Credit Card 755678...." = Account 4
            ALL FOUR are different accounts - extract each one!

            NEGATIVE ACCOUNT FIELD REQUIREMENTS:
            - creditor_name: MUST be a banking institution or collection agency name (not numeric codes)
            - account_number: MUST be alphanumeric only (remove *, X, -, . before returning)
            - account_balance: MUST be whole number with $ (e.g., "$2500" not "$2,500.00")
            - credit_limit: MUST be whole number with $ (e.g., "$5000" not "$5,000.00")
            - monthly_payment: MUST have 2 decimal places (e.g., "$25.00" not "$25")
            - date_opened: MUST be MM/DD/YYYY format (e.g., "01/15/2024")
            - account_status: MUST be descriptive (e.g., "Charge Off", "Collection", "Late 90 Days")
            - credit_bureau: MUST be one of: "Experian", "Equifax", "TransUnion"

            VALIDATION:
            - For every tradeline, double-check the is_negative flag against status + payment history before returning.
            - Include the "reasoning" field that clearly states why an account is marked negative or positive.
            - Edge cases: "Paid Charge Off" is still negative; "Closed - Paid in Full" is positive.
            - Verify all dates are in MM/DD/YYYY format before returning.

            Return as JSON array. Extract EVERYTHING - count every single account mention, even from the same creditor.

            TEXT TO ANALYZE:
            {text}
            """

            # Generate response using Gemini with error handling
            try:
                response = gemini_model.generate_content(prompt)
            except Exception as api_error:
                self.logger.error(f"❌ Gemini API call failed: {str(api_error)}")
                return self._fallback_basic_parsing(text)

            if not response or not response.text:
                self.logger.error("Empty response from Gemini")
                return self._fallback_basic_parsing(text)

            response_text = response.text.strip()
            self.logger.info(f"🧠 Gemini raw response: {response_text[:500]}...")

            # Parse JSON response
            import json
            import re

            # Clean up response text and extract JSON
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
                try:
                    tradelines = json.loads(json_text)

                    # Log detailed statistics about extracted tradelines
                    positive_count = sum(1 for t in tradelines if not t.get('is_negative', False))
                    negative_count = sum(1 for t in tradelines if t.get('is_negative', False))
                    dates_count = sum(1 for t in tradelines if t.get('date_opened'))

                    self.logger.info(f"✅ Parsed {len(tradelines)} tradelines from enhanced Gemini:")
                    self.logger.info(f"   📈 {positive_count} positive accounts, {negative_count} negative accounts")
                    self.logger.info(f"   📅 {dates_count} accounts with date_opened ({dates_count/max(len(tradelines), 1)*100:.1f}%)")

                    # Validate negative flags using unified classifier
                    tradelines = self._validate_with_classifier(tradelines)
                    
                    # Recalculate statistics after validation
                    positive_count = sum(1 for t in tradelines if not t.get('is_negative', False))
                    negative_count = sum(1 for t in tradelines if t.get('is_negative', False))
                    
                    # Log sample tradelines for debugging
                    for i, tradeline in enumerate(tradelines[:3]):  # Log first 3 as examples
                        creditor = tradeline.get('creditor_name', 'Unknown')
                        account = tradeline.get('account_number', 'No account')
                        date_opened = tradeline.get('date_opened', 'No date')
                        status = "NEGATIVE" if tradeline.get('is_negative') else "POSITIVE"
                        conf = tradeline.get('negative_confidence', 0.0)
                        self.logger.info(f"   📋 Sample {i+1}: {creditor} | {account} | {date_opened} | {status} (conf={conf:.2f})")

                    return tradelines
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON parsing failed: {e}")
                    self.logger.error(f"Problematic JSON: {json_text[:200]}...")
                    return self._fallback_basic_parsing(text)
            else:
                self.logger.error("No JSON array found in Gemini response")
                self.logger.error(f"Full response: {response_text[:1000]}...")
                return self._fallback_basic_parsing(text)

        except ImportError as e:
            self.logger.error(f"❌ Import error during enhanced Gemini processing: {str(e)}")
            return self._fallback_basic_parsing(text)
        except Exception as e:
            self.logger.error(f"❌ Failed to process enhanced Gemini response: {str(e)}")
            return self._fallback_basic_parsing(text)

    def _extract_tradelines_chunked(self, text: str) -> List[Dict[str, Any]]:
        """Extract tradelines from large text by chunking with overlap"""
        try:
            chunks = []
            chunk_size = 20000  # Increased chunk size for better context
            overlap_size = 3000  # Larger overlap to prevent missing tradelines
            max_chunks = 15  # Increased limit to process more comprehensive reports

            # Create overlapping chunks
            for i in range(0, len(text), chunk_size - overlap_size):
                end_pos = min(i + chunk_size, len(text))
                chunk = text[i:end_pos]

                # Only add chunk if it has substantial content
                if len(chunk.strip()) > 500:
                    chunks.append(chunk)

                # Stop if we've reached the end
                if end_pos >= len(text):
                    break

            # Only limit chunks if we have an excessive number (>15)
            if len(chunks) > max_chunks:
                self.logger.warning(f"⚠️ Large document with {len(chunks)} chunks, processing first {max_chunks} for performance")
                chunks = chunks[:max_chunks]

            self.logger.info(f"🧠 Processing {len(chunks)} overlapping chunks for comprehensive extraction")

            all_tradelines = []
            seen_tradelines = set()  # Track unique tradelines to avoid duplicates from overlap
            positive_count = 0
            negative_count = 0
            dates_found = 0

            for i, chunk in enumerate(chunks):
                try:
                    self.logger.info(f"🔍 Processing chunk {i+1}/{len(chunks)} ({len(chunk)} chars)")
                    chunk_tradelines = self._extract_tradelines_single(chunk)

                    # Deduplicate based on creditor_name + account_number
                    unique_tradelines = []
                    chunk_positive = 0
                    chunk_negative = 0
                    chunk_dates = 0

                    for tradeline in chunk_tradelines:
                        # Create unique identifier
                        identifier = f"{tradeline.get('creditor_name', '')}-{tradeline.get('account_number', '')}"
                        if identifier not in seen_tradelines:
                            seen_tradelines.add(identifier)
                            unique_tradelines.append(tradeline)

                            # Track statistics
                            if tradeline.get('is_negative'):
                                chunk_negative += 1
                                negative_count += 1
                            else:
                                chunk_positive += 1
                                positive_count += 1

                            if tradeline.get('date_opened'):
                                chunk_dates += 1
                                dates_found += 1

                    all_tradelines.extend(unique_tradelines)
                    self.logger.info(f"✅ Chunk {i+1}/{len(chunks)}: {len(unique_tradelines)} unique tradelines "
                                    f"({chunk_positive} positive, {chunk_negative} negative, {chunk_dates} with dates)")
                except Exception as e:
                    self.logger.error(f"❌ Failed processing chunk {i+1}: {str(e)}")
                    continue

            # Validate all tradelines with classifier before returning
            all_tradelines = self._validate_with_classifier(all_tradelines)
            
            # Recalculate statistics after validation
            positive_count = sum(1 for t in all_tradelines if not t.get('is_negative', False))
            negative_count = sum(1 for t in all_tradelines if t.get('is_negative', False))
            dates_found = sum(1 for t in all_tradelines if t.get('date_opened'))
            
            # Log final statistics
            self.logger.info(f"📊 Chunked extraction complete: {len(all_tradelines)} total tradelines (after classifier validation)")
            self.logger.info(f"📈 Statistics: {positive_count} positive, {negative_count} negative")
            self.logger.info(f"📅 Date extraction: {dates_found}/{len(all_tradelines)} tradelines have dates "
                            f"({dates_found/max(len(all_tradelines), 1)*100:.1f}%)")

            return all_tradelines

        except Exception as e:
            self.logger.error(f"❌ Chunked processing failed: {str(e)}")
            return self._fallback_basic_parsing(text)

    def _fallback_basic_parsing(self, text: str) -> List[Dict[str, Any]]:
        """Fallback basic parsing when Gemini is not available"""
        try:
            self.logger.info("🔧 Using basic parsing fallback (Gemini unavailable)")

            # Basic pattern matching for common credit report patterns
            tradelines = []
            lines = text.split('\n')

            current_tradeline = {}
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Look for creditor names (basic heuristic)
                if any(keyword in line.lower() for keyword in ['bank', 'credit', 'card', 'loan', 'mortgage']):
                    if 'account' in line.lower() or 'acct' in line.lower():
                        # Try to extract basic info
                        words = line.split()
                        if len(words) >= 2:
                            current_tradeline = {
                                "creditor_name": ' '.join(words[:2]),
                                "account_number": "Unknown",
                                "account_balance": "",
                                "credit_limit": "",
                                "monthly_payment": "",
                                "date_opened": "",
                                "account_type": "Unknown",
                                "account_status": "Unknown",
                                "is_negative": False
                            }
                            tradelines.append(current_tradeline)

            self.logger.info(f"🔧 Basic parsing found {len(tradelines)} potential tradelines")
            return tradelines[:10]  # Limit to 10 to avoid noise

        except Exception as e:
            self.logger.error(f"❌ Basic parsing fallback failed: {str(e)}")
            return []
    
    def _validate_with_classifier(self, tradelines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate and correct is_negative flags using the unified negative tradeline classifier.
        This provides AI fallback/validation by comparing Gemini's determination with rule-based scoring.
        """
        if not tradelines:
            return tradelines
        
        validated_tradelines = []
        corrections_made = 0
        ai_to_classifier_disagreements = 0
        
        for tradeline in tradelines:
            # Get Gemini's original determination
            gemini_is_negative = tradeline.get('is_negative', False)
            gemini_reasoning = tradeline.get('reasoning', '')
            
            # Run through classifier
            result = self.negative_classifier.classify(tradeline)
            
            classifier_is_negative = result.is_negative
            classifier_confidence = result.confidence
            
            # Decision logic: Use classifier as validation/correction
            # High confidence classifier overrides Gemini
            if classifier_confidence >= 0.80:
                final_is_negative = classifier_is_negative
                if final_is_negative != gemini_is_negative:
                    corrections_made += 1
                    self.logger.debug(
                        f"🔄 Classifier correction (high conf={classifier_confidence:.2f}): "
                        f"{tradeline.get('creditor_name', 'Unknown')} - "
                        f"Gemini said {'NEGATIVE' if gemini_is_negative else 'POSITIVE'}, "
                        f"Classifier says {'NEGATIVE' if classifier_is_negative else 'POSITIVE'} "
                        f"(score={result.score:.2f}, factors={result.indicators})"
                    )
            # Medium confidence: Log disagreement but trust Gemini (it has more context)
            elif classifier_confidence >= 0.60:
                final_is_negative = gemini_is_negative
                if classifier_is_negative != gemini_is_negative:
                    ai_to_classifier_disagreements += 1
                    self.logger.debug(
                        f"⚠️ AI vs Classifier disagreement (medium conf={classifier_confidence:.2f}): "
                        f"{tradeline.get('creditor_name', 'Unknown')} - "
                        f"Keeping Gemini's {'NEGATIVE' if gemini_is_negative else 'POSITIVE'} determination "
                        f"(Classifier score={result.score:.2f})"
                    )
            # Low confidence: Trust Gemini
            else:
                final_is_negative = gemini_is_negative
                self.logger.debug(
                    f"ℹ️ Low classifier confidence ({classifier_confidence:.2f}) - "
                    f"trusting Gemini for {tradeline.get('creditor_name', 'Unknown')}"
                )
            
            # Update tradeline with validated information
            tradeline['is_negative'] = final_is_negative
            tradeline['negative_confidence'] = classifier_confidence
            tradeline['classifier_score'] = result.score
            tradeline['classifier_factors'] = result.factors
            
            # Enhance reasoning with classifier insights if correction was made
            if corrections_made > 0 and final_is_negative != gemini_is_negative:
                original_reasoning = gemini_reasoning
                classifier_reasoning = f"Classifier override (conf={classifier_confidence:.2f}, score={result.score:.2f}): {', '.join(result.indicators[:3])}"
                tradeline['reasoning'] = f"{classifier_reasoning}. Original AI: {original_reasoning}"
            
            validated_tradelines.append(tradeline)
        
        # Log summary
        if corrections_made > 0:
            self.logger.info(
                f"✅ Classifier validation complete: {corrections_made} corrections made out of {len(tradelines)} tradelines"
            )
        if ai_to_classifier_disagreements > 0:
            self.logger.info(
                f"ℹ️ AI vs Classifier: {ai_to_classifier_disagreements} disagreements noted (trusted AI)"
            )
        
        return validated_tradelines
