import logging
import re
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from supabase import Client

logger = logging.getLogger(__name__)

class EnhancedTradelineService:
    """Enhanced tradeline service with duplicate detection and progressive enrichment"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
    
    def get_account_first_4(self, account_number: str) -> str:
        """Get first 4 alphanumeric characters from account number"""
        if not account_number:
            return ''
        # Remove non-alphanumeric characters and get first 4
        cleaned = re.sub(r'[^A-Za-z0-9]', '', account_number)
        return cleaned[:4].upper()
    
    def should_update_field(self, existing_value: Any, new_value: Any) -> bool:
        """Check if a field should be updated based on enrichment rules"""
        if existing_value is None:
            return True
        if existing_value == '':
            return True
        if existing_value in ['$0', '$0.00', '0', 0]:
            return True
        return False


    # Pre-save validation to prevent the issues seen in logs
    def validate_and_fix_tradeline(tradeline: dict, detected_bureau: str, user_id: str) -> dict:
        """
        Validate and fix tradeline data before saving to prevent common issues.
        """
        
        # Force correct credit bureau (critical fix)
        if tradeline.get('credit_bureau') != detected_bureau:
            logger.warning(f"🔧 Fixing credit bureau: {tradeline.get('credit_bureau')} → {detected_bureau}")
            tradeline['credit_bureau'] = detected_bureau
        
        # Ensure user_id is set
        if not tradeline.get('user_id'):
            tradeline['user_id'] = user_id
        
        # Clean and validate creditor name
        if tradeline.get('creditor_name'):
            tradeline['creditor_name'] = tradeline['creditor_name'].strip().upper()
        else:
            logger.error("❌ Tradeline missing creditor_name - will fail")
            return None
        
        # Clean account number if present
        if tradeline.get('account_number'):
            # Remove any extra whitespace or special characters
            account_num = str(tradeline['account_number']).strip()
            if account_num and account_num not in ['', 'NULL', 'None']:
                tradeline['account_number'] = account_num
            else:
                tradeline['account_number'] = ''
                logger.info(f"ℹ️ {tradeline['creditor_name']}: No account number found")
        else:
            tradeline['account_number'] = ''
            logger.info(f"ℹ️ {tradeline['creditor_name']}: No account number found")
        
        # Ensure required fields exist with defaults
        required_fields = {
            'account_balance': '',
            'credit_limit': '',
            'monthly_payment': '',
            'date_opened': '',
            'account_type': 'other',
            'account_status': 'other',
            'is_negative': False,
            'dispute_count': 0
        }
        
        for field, default_value in required_fields.items():
            if field not in tradeline or tradeline[field] is None:
                tradeline[field] = default_value
        
        # Add timestamps if missing
        current_time = datetime.now().isoformat()
        if not tradeline.get('created_at'):
            tradeline['created_at'] = current_time
        if not tradeline.get('updated_at'):
            tradeline['updated_at'] = current_time
        
        # Generate ID if missing
        if not tradeline.get('id'):
            tradeline['id'] = str(uuid.uuid4())
        
        logger.info(f"✅ Validated tradeline: {tradeline['creditor_name']} - Bureau: {tradeline['credit_bureau']}")
        return tradeline

    def process_and_validate_all_tradelines(tradelines: list, detected_bureau: str, user_id: str) -> list:
        """
        Process and validate all tradelines before saving to prevent failures.
        """
        
        logger.info(f"🔍 Validating {len(tradelines)} tradelines for {detected_bureau}")
        
        validated_tradelines = []
        failed_count = 0
        
        for i, tradeline in enumerate(tradelines, 1):
            logger.info(f"📋 Validating tradeline {i}/{len(tradelines)}: {tradeline.get('creditor_name', 'UNKNOWN')}")
            
            validated = validate_and_fix_tradeline(tradeline, detected_bureau, user_id)
            
            if validated:
                validated_tradelines.append(validated)
            else:
                failed_count += 1
                logger.error(f"❌ Tradeline {i} failed validation: {tradeline}")
        
        logger.info(f"✅ Validation complete: {len(validated_tradelines)} valid, {failed_count} failed")
        
        # Log summary of account numbers
        with_accounts = sum(1 for t in validated_tradelines if t.get('account_number'))
        without_accounts = len(validated_tradelines) - with_accounts
        
        logger.info(f"📊 Account number summary: {with_accounts} with accounts, {without_accounts} without accounts")
        
        return validated_tradelines

    # Enhanced main processing function with validation
    async def process_credit_report_with_validation(file_path: str, user_id: str):
        """
        Complete processing with enhanced validation to prevent the issues in logs.
        """
        try:
            # Extract text using Document AI
            extracted_text = await document_ai.extract_text(file_path)
            logger.info(f"✅ Document AI text extraction successful")
            
            # Enhanced credit bureau detection
            detected_bureau = detect_credit_bureau(extracted_text)
            logger.info(f"🏢 Enhanced credit bureau detected: {detected_bureau}")
            
            # Use enhanced Gemini extraction with account focus
            if gemini_model:
                logger.info("🧠 Starting enhanced Gemini extraction with account focus...")
                enhanced_processor = EnhancedGeminiProcessorWithAccountFocus(gemini_model)
                tradelines = enhanced_processor.extract_tradelines_with_account_focus(extracted_text, detected_bureau)
                
                if tradelines:
                    logger.info(f"✅ Enhanced extraction found: {len(tradelines)} tradelines")
                    
                    # CRITICAL: Validate all tradelines before saving
                    validated_tradelines = process_and_validate_all_tradelines(tradelines, detected_bureau, user_id)
                    
                    if not validated_tradelines:
                        logger.error("❌ No valid tradelines after validation")
                        raise Exception("All tradelines failed validation")
                    
                    # Log final summary before saving
                    logger.info(f"📊 Final summary before saving:")
                    logger.info(f"   - Total tradelines: {len(validated_tradelines)}")
                    logger.info(f"   - Credit bureau: {detected_bureau}")
                    logger.info(f"   - User ID: {user_id}")
                    
                    # Show sample tradeline for verification
                    if validated_tradelines:
                        sample = validated_tradelines[0]
                        logger.info(f"   - Sample: {sample['creditor_name']} ({sample.get('account_number', 'NO_ACCOUNT')}) - {sample['credit_bureau']}")
                    
                    return {
                        'tradelines': validated_tradelines,
                        'processing_method': "enhanced_gemini_with_validation",
                        'credit_bureau': detected_bureau,
                        'total_found': len(validated_tradelines),
                        'validation_passed': True
                    }
                else:
                    logger.warning("⚠️ Enhanced Gemini found no tradelines")
            
            # Fallback processing
            logger.error("❌ Enhanced processing failed")
            raise Exception("Enhanced processing failed")
            
        except Exception as e:
            logger.error(f"❌ Enhanced processing with validation failed: {e}")
            raise

    # Quick fix for your enhanced_tradeline_service 
    def ensure_correct_bureau_before_save(tradeline_data: dict, expected_bureau: str = "TransUnion"):
        """
        Last-chance fix to ensure correct credit bureau before database save.
        Call this in your enhanced_tradeline_service before each save operation.
        """
        
        if tradeline_data.get('credit_bureau') != expected_bureau:
            logger.warning(f"🚨 CRITICAL: Fixing credit bureau just before save: {tradeline_data.get('credit_bureau')} → {expected_bureau}")
            tradeline_data['credit_bureau'] = expected_bureau
            
            # Also log the creditor for tracking
            creditor = tradeline_data.get('creditor_name', 'UNKNOWN')
            logger.warning(f"🚨 Fixed bureau for: {creditor}")
        
        return tradeline_data