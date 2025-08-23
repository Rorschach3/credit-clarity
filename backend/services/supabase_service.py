"""
Supabase Database Service
Handles all database operations for Credit Clarity application
"""
import logging
from typing import Dict, List, Optional, Any
from supabase import Client

logger = logging.getLogger(__name__)


class SupabaseService:
    """Service for managing Supabase database operations"""
    
    def __init__(self, client: Client):
        self.client = client
    
    # User Profile Operations
    def insert_user_profile(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insert a new user profile"""
        try:
            result = self.client.table("user_profiles").insert(user_data).execute()
            logger.info(f"✅ User profile inserted: {user_data.get('id', 'unknown')}")
            return result.data
        except Exception as e:
            logger.error(f"❌ Error inserting user profile: {e}")
            return None
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by ID"""
        try:
            result = self.client.table("user_profiles").select("*").eq("id", user_id).execute()
            if result.data:
                logger.debug(f"✅ User profile retrieved: {user_id}")
                return result.data[0]
            else:
                logger.warning(f"⚠️ User profile not found: {user_id}")
                return None
        except Exception as e:
            logger.error(f"❌ Error getting user profile {user_id}: {e}")
            return None
    
    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Update user profile"""
        try:
            result = self.client.table("user_profiles").update(updates).eq("id", user_id).execute()
            logger.info(f"✅ User profile updated: {user_id}")
            return result.data
        except Exception as e:
            logger.error(f"❌ Error updating user profile {user_id}: {e}")
            return None
    
    def delete_user_profile(self, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """Delete user profile"""
        try:
            result = self.client.table("user_profiles").delete().eq("id", user_id).execute()
            logger.info(f"✅ User profile deleted: {user_id}")
            return result.data
        except Exception as e:
            logger.error(f"❌ Error deleting user profile {user_id}: {e}")
            return None
    
    # Tradeline Operations
    def insert_tradelines(self, tradelines: List[Dict[str, Any]], user_id: str) -> Optional[List[Dict[str, Any]]]:
        """Insert multiple tradelines for a user"""
        try:
            # Add user_id to each tradeline
            for tradeline in tradelines:
                tradeline['user_id'] = user_id
            
            result = self.client.table("tradelines").insert(tradelines).execute()
            logger.info(f"✅ Inserted {len(tradelines)} tradelines for user {user_id}")
            return result.data
        except Exception as e:
            logger.error(f"❌ Error inserting tradelines for user {user_id}: {e}")
            return None
    
    def get_user_tradelines(self, user_id: str, limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """Get all tradelines for a user"""
        try:
            result = (self.client.table("tradelines")
                     .select("*")
                     .eq("user_id", user_id)
                     .order("created_at", desc=True)
                     .limit(limit)
                     .execute())
            
            logger.debug(f"✅ Retrieved {len(result.data)} tradelines for user {user_id}")
            return result.data
        except Exception as e:
            logger.error(f"❌ Error getting tradelines for user {user_id}: {e}")
            return None
    
    def delete_user_tradelines(self, user_id: str) -> bool:
        """Delete all tradelines for a user"""
        try:
            result = self.client.table("tradelines").delete().eq("user_id", user_id).execute()
            logger.info(f"✅ Deleted tradelines for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error deleting tradelines for user {user_id}: {e}")
            return False
    
    # Job Operations
    def insert_processing_job(self, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insert a new processing job"""
        try:
            result = self.client.table("processing_jobs").insert(job_data).execute()
            logger.info(f"✅ Processing job inserted: {job_data.get('job_id', 'unknown')}")
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"❌ Error inserting processing job: {e}")
            return None
    
    def update_job_status(self, job_id: str, status: str, **kwargs) -> bool:
        """Update job status and optional additional fields"""
        try:
            update_data = {"status": status}
            update_data.update(kwargs)
            
            result = self.client.table("processing_jobs").update(update_data).eq("job_id", job_id).execute()
            logger.debug(f"✅ Job status updated: {job_id} -> {status}")
            return True
        except Exception as e:
            logger.error(f"❌ Error updating job {job_id}: {e}")
            return False
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status and details"""
        try:
            result = self.client.table("processing_jobs").select("*").eq("job_id", job_id).execute()
            if result.data:
                return result.data[0]
            else:
                logger.warning(f"⚠️ Job not found: {job_id}")
                return None
        except Exception as e:
            logger.error(f"❌ Error getting job status {job_id}: {e}")
            return None
    
    def get_user_jobs(self, user_id: str, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Get recent jobs for a user"""
        try:
            result = (self.client.table("processing_jobs")
                     .select("*")
                     .eq("user_id", user_id)
                     .order("created_at", desc=True)
                     .limit(limit)
                     .execute())
            
            logger.debug(f"✅ Retrieved {len(result.data)} jobs for user {user_id}")
            return result.data
        except Exception as e:
            logger.error(f"❌ Error getting jobs for user {user_id}: {e}")
            return None
    
    # Credit Report Operations
    def save_credit_report(self, user_id: str, report_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Save processed credit report data"""
        try:
            report_data['user_id'] = user_id
            result = self.client.table("credit_reports").insert(report_data).execute()
            logger.info(f"✅ Credit report saved for user {user_id}")
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"❌ Error saving credit report for user {user_id}: {e}")
            return None
    
    def get_user_credit_reports(self, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get all credit reports for a user"""
        try:
            result = (self.client.table("credit_reports")
                     .select("*")
                     .eq("user_id", user_id)
                     .order("created_at", desc=True)
                     .execute())
            
            logger.debug(f"✅ Retrieved {len(result.data)} credit reports for user {user_id}")
            return result.data
        except Exception as e:
            logger.error(f"❌ Error getting credit reports for user {user_id}: {e}")
            return None
    
    # Analytics and Monitoring
    def log_processing_event(self, event_data: Dict[str, Any]) -> bool:
        """Log processing events for analytics"""
        try:
            result = self.client.table("processing_events").insert(event_data).execute()
            return True
        except Exception as e:
            logger.error(f"❌ Error logging processing event: {e}")
            return False
    
    def get_processing_stats(self, days: int = 30) -> Optional[Dict[str, Any]]:
        """Get processing statistics for the last N days"""
        try:
            from datetime import datetime, timedelta
            
            since_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get job counts by status
            result = (self.client.table("processing_jobs")
                     .select("status")
                     .gte("created_at", since_date)
                     .execute())
            
            if result.data:
                stats = {"total_jobs": len(result.data)}
                for status in ["pending", "processing", "completed", "failed"]:
                    stats[f"{status}_jobs"] = len([j for j in result.data if j.get("status") == status])
                
                logger.debug(f"✅ Retrieved processing stats for last {days} days")
                return stats
            
            return {"total_jobs": 0}
        except Exception as e:
            logger.error(f"❌ Error getting processing stats: {e}")
            return None
    
    # Health Check
    def health_check(self) -> bool:
        """Perform a simple health check on the database connection"""
        try:
            # Simple query to test connection
            result = self.client.table("user_profiles").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            return False