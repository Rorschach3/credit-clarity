from typing import List, Dict, Optional, Tuple
import hashlib
from dataclasses import dataclass
from sqlalchemy.orm import Session
from models.tradeline_models import Tradelines  
from main import TradelineSchema

@dataclass
class TradelineKey:
    """Represents the unique identifier for a tradeline"""
    creditor_name: str
    account_number_first4: str
    date_opened: str
    
    def __post_init__(self):
        # Normalize the data for consistent comparison
        self.creditor_name = self.creditor_name.upper().strip()
        self.account_number_first4 = self.account_number_first4[:4] if self.account_number_first4 else ""
        self.date_opened = self.date_opened.strip()
    
    def to_hash(self) -> str:
        """Generate a hash for this tradeline key"""
        combined = f"{self.creditor_name}_{self.account_number_first4}_{self.date_opened}"
        return hashlib.md5(combined.encode()).hexdigest()

class TradelineDeduplicator:
    """Handles tradeline deduplication with smart merging logic"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        
    def create_tradeline_key(self, tradeline: TradelineSchema) -> TradelineKey:
        """Create a tradeline key from a tradeline object"""
        return TradelineKey(
            creditor_name=tradeline.creditor_name or "",
            account_number_first4=tradeline.account_number[:4] if tradeline.account_number else "",
            date_opened=tradeline.date_opened or ""
        )
    
    def is_empty_or_null(self, value: any) -> bool:
        """Check if a field is empty, null, or contains placeholder values"""
        if value is None:
            return True
        if isinstance(value, str):
            return value.strip() in ["", "NULL", "null", "N/A", "n/a", "xx/xx/xxxxx", "0"]
        if isinstance(value, (int, float)):
            return value == 0
        return False
    
    def merge_tradelines(self, existing: TradelineSchema, new_tradeline: TradelineSchema) -> TradelineSchema:
        """
        Merge two tradelines, only updating empty/null fields in existing with new data
        """
        merged = existing.copy()
        
        # Define fields that should be merged
        mergeable_fields = [
            'account_balance', 'credit_limit', 'monthly_payment', 
            'account_type', 'account_status', 'date_opened'
        ]
        
        for field in mergeable_fields:
            existing_value = getattr(existing, field)
            new_value = getattr(new_tradeline, field)
            
            # Only update if existing field is empty/null and new field has data
            if self.is_empty_or_null(existing_value) and not self.is_empty_or_null(new_value):
                setattr(merged, field, new_value)
                
        # Special handling for account_number - keep the most complete one
        if (self.is_empty_or_null(existing.account_number) or 
            len(new_tradeline.account_number or "") > len(existing.account_number or "")):
            merged.account_number = new_tradeline.account_number
            
        # Update metadata
        merged.dispute_count = max(existing.dispute_count, new_tradeline.dispute_count)
        
        return merged
    
    def find_existing_tradeline(self, tradeline_key: TradelineKey, credit_bureau: str, user_id: str) -> Optional[TradelineSchema]:
        """
        Find existing tradeline in database with same key and credit bureau
        """
        try:
            existing = self.db_session.query(Tradelines).filter(
                Tradelines.user_id == user_id,
                Tradelines.creditor_name.ilike(f"%{tradeline_key.creditor_name}%"),
                Tradelines.account_number.like(f"{tradeline_key.account_number_first4}%"),
                Tradelines.date_opened == tradeline_key.date_opened,
                Tradelines.credit_bureau == credit_bureau
            ).first()
            
            if existing:
                return TradelineSchema.from_orm(existing)
            return None
            
        except Exception as e:
            print(f"Error finding existing tradeline: {e}")
            return None
    
    def process_tradeline(self, new_tradeline: TradelineSchema, user_id: str) -> Tuple[bool, TradelineSchema, str]:
        """
        Process a new tradeline with deduplication logic
        
        Returns:
            (should_save: bool, tradeline_to_save: TradelineSchema, action: str)
        """
        # Create the unique key
        tradeline_key = self.create_tradeline_key(new_tradeline)
        
        # Validate minimum required data
        if not all([tradeline_key.creditor_name, tradeline_key.account_number_first4, new_tradeline.credit_bureau]):
            return False, new_tradeline, "INVALID_DATA"
        
        # Look for existing tradeline with same key and credit bureau
        existing = self.find_existing_tradeline(tradeline_key, new_tradeline.credit_bureau, user_id)
        
        if existing:
            # Same credit bureau - merge data
            merged_tradeline = self.merge_tradelines(existing, new_tradeline)
            merged_tradeline.user_id = user_id  # Ensure user_id is set
            return True, merged_tradeline, "MERGED"
        else:
            # No existing tradeline with same credit bureau - save new one
            new_tradeline.user_id = user_id
            return True, new_tradeline, "NEW"
    
    def process_tradeline_batch(self, tradelines: List[TradelineSchema], user_id: str) -> Dict[str, List[TradelineSchema]]:
        """
        Process a batch of tradelines with deduplication
        
        Returns:
            {
                'to_save': [TradelineSchema],
                'merged': [TradelineSchema],
                'invalid': [TradelineSchema]
            }
        """
        results = {
            'to_save': [],
            'merged': [],
            'invalid': [],
            'new': []
        }
        
        for tradeline in tradelines:
            should_save, processed_tradeline, action = self.process_tradeline(tradeline, user_id)
            
            if should_save:
                results['to_save'].append(processed_tradeline)
                if action == "MERGED":
                    results['merged'].append(processed_tradeline)
                elif action == "NEW":
                    results['new'].append(processed_tradeline)
            else:
                results['invalid'].append(tradeline)
        
        return results

# Usage example in your main processing function
def process_tradelines_with_deduplication(extracted_tradelines: List[TradelineSchema], user_id: str, db_session: Session):
    """
    Main function to process extracted tradelines with deduplication
    """
    deduplicator = TradelineDeduplicator(db_session)
    results = deduplicator.process_tradeline_batch(extracted_tradelines, user_id)
    
    print(f"Processing results:")
    print(f"  - New tradelines: {len(results['new'])}")
    print(f"  - Merged tradelines: {len(results['merged'])}")
    print(f"  - Invalid tradelines: {len(results['invalid'])}")
    print(f"  - Total to save: {len(results['to_save'])}")
    
    # Save the processed tradelines to database
    try:
        for tradeline in results['to_save']:
            # Convert to your database model and save
            db_tradeline = Tradelines(**tradeline.dict())
            db_session.merge(db_tradeline)  # Use merge instead of add for upsert behavior
            
        db_session.commit()
        print(f"Successfully saved {len(results['to_save'])} tradelines")
        
    except Exception as e:
        db_session.rollback()
        print(f"Error saving tradelines: {e}")
        raise
    
    return results