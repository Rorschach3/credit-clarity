"""
Audit Service for Credit Clarity
Handles comprehensive audit logging for all user profile changes
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AuditAction:
    """Audit action types."""
    PROFILE_CREATED = "profile_created"
    PROFILE_UPDATED = "profile_updated"
    EMAIL_CHANGED = "email_changed"
    PASSWORD_CHANGED = "password_changed"
    AVATAR_UPLOADED = "avatar_uploaded"
    AVATAR_REMOVED = "avatar_removed"
    ACCOUNT_DELETED = "account_deleted"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"


class AuditService:
    """
    Service for logging and managing audit trails.
    
    Stores audit logs for compliance and security monitoring.
    """
    
    def __init__(self, storage_path: str = "storage/audit"):
        """
        Initialize audit service.
        
        Args:
            storage_path: Directory for audit log storage
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.log_file = self.storage_path / "audit.log"
        
        # In-memory cache for recent logs (for performance)
        self._recent_logs: list = []
        self._max_recent_logs = 1000
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.utcnow().isoformat() + "Z"
    
    def _create_log_entry(
        self,
        user_id: str,
        action: str,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        ip_address: str = "unknown",
        user_agent: str = "unknown",
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized audit log entry.
        
        Args:
            user_id: User identifier
            action: Action type (e.g., profile_updated)
            old_value: Previous state (for updates)
            new_value: New state (for creates/updates)
            ip_address: Client IP address
            user_agent: Client user agent
            request_id: Request correlation ID
            metadata: Additional context
            
        Returns:
            Audit log entry dictionary
        """
        return {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "action": action,
            "old_value": old_value,
            "new_value": new_value,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": self._get_timestamp(),
            "request_id": request_id or str(uuid.uuid4())[:8],
            "metadata": metadata or {}
        }
    
    def _serialize_for_json(self, value: Any) -> Any:
        """Serialize value for JSON storage."""
        if isinstance(value, datetime):
            return value.isoformat()
        elif hasattr(value, 'model_dump'):
            return value.model_dump()
        elif isinstance(value, dict):
            return {k: self._serialize_for_json(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._serialize_for_json(item) for item in value]
        else:
            return value
    
    async def _write_log(self, log_entry: Dict[str, Any]) -> None:
        """
        Write audit log entry to storage.
        
        Args:
            log_entry: Audit log entry to write
        """
        try:
            # Add to in-memory cache
            self._recent_logs.append(log_entry)
            if len(self._recent_logs) > self._max_recent_logs:
                self._recent_logs.pop(0)
            
            # Write to log file
            serializable_entry = self._serialize_for_json(log_entry)
            log_line = json.dumps(serializable_entry) + "\n"
            
            async with aiofiles.open(self.log_file, 'a', encoding='utf-8') as f:
                await f.write(log_line)
                
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    async def log_profile_created(
        self,
        user_id: str,
        profile_data: Dict[str, Any],
        ip_address: str = "unknown",
        user_agent: str = "unknown",
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log initial profile creation.
        
        Args:
            user_id: User identifier
            profile_data: Initial profile data
            ip_address: Client IP address
            user_agent: Client user agent
            request_id: Request correlation ID
            
        Returns:
            Created audit log entry
        """
        log_entry = self._create_log_entry(
            user_id=user_id,
            action=AuditAction.PROFILE_CREATED,
            old_value=None,
            new_value=profile_data,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            metadata={"event_type": "security"}
        )
        
        await self._write_log(log_entry)
        
        logger.info(
            f"AUDIT: Profile created for user {user_id}, "
            f"request_id={log_entry['request_id']}"
        )
        
        return log_entry
    
    async def log_profile_updated(
        self,
        user_id: str,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any],
        ip_address: str = "unknown",
        user_agent: str = "unknown",
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log profile update event.
        
        Args:
            user_id: User identifier
            old_data: Previous profile data
            new_data: Updated profile data
            ip_address: Client IP address
            user_agent: Client user agent
            request_id: Request correlation ID
            
        Returns:
            Created audit log entry
        """
        # Calculate changed fields for metadata
        changed_fields = []
        for key in set(old_data.keys()) | set(new_data.keys()):
            if old_data.get(key) != new_data.get(key):
                changed_fields.append(key)
        
        log_entry = self._create_log_entry(
            user_id=user_id,
            action=AuditAction.PROFILE_UPDATED,
            old_value=old_data,
            new_value=new_data,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            metadata={
                "event_type": "security",
                "changed_fields": changed_fields
            }
        )
        
        await self._write_log(log_entry)
        
        logger.info(
            f"AUDIT: Profile updated for user {user_id}, "
            f"changes={changed_fields}, request_id={log_entry['request_id']}"
        )
        
        return log_entry
    
    async def log_email_changed(
        self,
        user_id: str,
        old_email: str,
        new_email: str,
        ip_address: str = "unknown",
        user_agent: str = "unknown",
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log email change event.
        
        Args:
            user_id: User identifier
            old_email: Previous email address
            new_email: New email address
            ip_address: Client IP address
            user_agent: Client user agent
            request_id: Request correlation ID
            
        Returns:
            Created audit log entry
        """
        log_entry = self._create_log_entry(
            user_id=user_id,
            action=AuditAction.EMAIL_CHANGED,
            old_value={"email": self._mask_email(old_email)},
            new_value={"email": self._mask_email(new_email)},
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            metadata={
                "event_type": "security",
                "unmasked_old_email": old_email,
                "unmasked_new_email": new_email
            }
        )
        
        await self._write_log(log_entry)
        
        logger.info(
            f"AUDIT: Email changed for user {user_id}, "
            f"old={self._mask_email(old_email)}, new={self._mask_email(new_email)}, "
            f"request_id={log_entry['request_id']}"
        )
        
        return log_entry
    
    async def log_password_changed(
        self,
        user_id: str,
        ip_address: str = "unknown",
        user_agent: str = "unknown",
        request_id: Optional[str] = None,
        reason: str = "user_initiated"
    ) -> Dict[str, Any]:
        """
        Log password change event.
        
        Args:
            user_id: User identifier
            ip_address: Client IP address
            user_agent: Client user agent
            request_id: Request correlation ID
            reason: Reason for password change
            
        Returns:
            Created audit log entry
        """
        log_entry = self._create_log_entry(
            user_id=user_id,
            action=AuditAction.PASSWORD_CHANGED,
            old_value=None,
            new_value={"timestamp": self._get_timestamp(), "reason": reason},
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            metadata={"event_type": "security", "reason": reason}
        )
        
        await self._write_log(log_entry)
        
        logger.info(
            f"AUDIT: Password changed for user {user_id}, "
            f"reason={reason}, request_id={log_entry['request_id']}"
        )
        
        return log_entry
    
    async def log_avatar_uploaded(
        self,
        user_id: str,
        avatar_url: str,
        ip_address: str = "unknown",
        user_agent: str = "unknown",
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log avatar upload event.
        
        Args:
            user_id: User identifier
            avatar_url: New avatar URL
            ip_address: Client IP address
            user_agent: Client user agent
            request_id: Request correlation ID
            
        Returns:
            Created audit log entry
        """
        log_entry = self._create_log_entry(
            user_id=user_id,
            action=AuditAction.AVATAR_UPLOADED,
            old_value=None,
            new_value={"avatar_url": avatar_url},
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            metadata={"event_type": "profile"}
        )
        
        await self._write_log(log_entry)
        
        logger.info(
            f"AUDIT: Avatar uploaded for user {user_id}, "
            f"request_id={log_entry['request_id']}"
        )
        
        return log_entry
    
    async def log_avatar_removed(
        self,
        user_id: str,
        ip_address: str = "unknown",
        user_agent: str = "unknown",
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log avatar removal event.
        
        Args:
            user_id: User identifier
            ip_address: Client IP address
            user_agent: Client user agent
            request_id: Request correlation ID
            
        Returns:
            Created audit log entry
        """
        log_entry = self._create_log_entry(
            user_id=user_id,
            action=AuditAction.AVATAR_REMOVED,
            old_value=None,
            new_value={"removed_at": self._get_timestamp()},
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            metadata={"event_type": "profile"}
        )
        
        await self._write_log(log_entry)
        
        logger.info(
            f"AUDIT: Avatar removed for user {user_id}, "
            f"request_id={log_entry['request_id']}"
        )
        
        return log_entry
    
    async def log_account_deleted(
        self,
        user_id: str,
        ip_address: str = "unknown",
        user_agent: str = "unknown",
        request_id: Optional[str] = None,
        reason: str = "user_request"
    ) -> Dict[str, Any]:
        """
        Log account deletion event.
        
        Args:
            user_id: User identifier
            ip_address: Client IP address
            user_agent: Client user agent
            request_id: Request correlation ID
            reason: Reason for deletion
            
        Returns:
            Created audit log entry
        """
        log_entry = self._create_log_entry(
            user_id=user_id,
            action=AuditAction.ACCOUNT_DELETED,
            old_value={"deleted_at": self._get_timestamp()},
            new_value=None,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            metadata={"event_type": "security", "reason": reason}
        )
        
        await self._write_log(log_entry)
        
        logger.warning(
            f"AUDIT: Account deleted for user {user_id}, "
            f"reason={reason}, request_id={log_entry['request_id']}"
        )
        
        return log_entry
    
    async def get_user_audit_logs(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
        action_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve audit logs for a specific user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            action_filter: Filter by action type
            
        Returns:
            Dictionary containing logs and pagination info
        """
        logs = []
        
        # Read from log file
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            log_entry = json.loads(line)
                            if log_entry.get("user_id") == user_id:
                                if action_filter is None or log_entry.get("action") == action_filter:
                                    logs.append(log_entry)
        except Exception as e:
            logger.error(f"Failed to read audit logs: {e}")
        
        # Sort by timestamp descending (newest first)
        logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Apply pagination
        total = len(logs)
        paginated_logs = logs[offset:offset + limit]
        
        return {
            "logs": paginated_logs,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
    
    def _mask_email(self, email: str) -> str:
        """
        Mask email for secure logging.
        
        Args:
            email: Email address to mask
            
        Returns:
            Masked email address
        """
        if "@" not in email:
            return "***"
        
        local, domain = email.rsplit("@", 1)
        
        if len(local) <= 2:
            masked_local = "***"
        else:
            masked_local = local[0] + "***" + local[-1]
        
        return f"{masked_local}@{domain}"
    
    async def get_recent_logs(self, limit: int = 100) -> list:
        """
        Get recent audit logs from cache.
        
        Args:
            limit: Maximum number of logs to return
            
        Returns:
            List of recent log entries
        """
        return self._recent_logs[-limit:]


# Global audit service instance
audit_service = AuditService()


# Import aiofiles for async file operations
import aiofiles
