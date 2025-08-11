"""
Credit Monitoring Service Integration
Connects to multiple credit monitoring providers for real-time updates
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import json
import hashlib
from enum import Enum

import aiohttp
import httpx
from pydantic import BaseModel

from core.config import get_settings
from core.logging.logger import get_logger
from services.cache_service import cache
from services.database_optimizer import db_optimizer

logger = get_logger(__name__)
settings = get_settings()

class ChangeType(Enum):
    """Types of credit report changes."""
    NEW_ACCOUNT = "new_account"
    ACCOUNT_CLOSED = "account_closed"
    BALANCE_CHANGE = "balance_change"
    STATUS_CHANGE = "status_change"
    SCORE_CHANGE = "score_change"
    NEW_INQUIRY = "new_inquiry"
    ADDRESS_CHANGE = "address_change"
    PERSONAL_INFO_CHANGE = "personal_info_change"
    DISPUTE_UPDATE = "dispute_update"
    FRAUD_ALERT = "fraud_alert"

class Severity(Enum):
    """Severity levels for changes."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class CreditChange:
    """Represents a change in credit report."""
    change_id: str
    user_id: str
    change_type: ChangeType
    severity: Severity
    title: str
    description: str
    old_value: Optional[str]
    new_value: Optional[str]
    bureau: str
    detected_at: datetime
    notification_sent: bool = False
    
    # Additional context
    account_number: Optional[str] = None
    creditor_name: Optional[str] = None
    amount: Optional[float] = None
    score_impact: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class CreditScore:
    """Credit score information."""
    score: int
    bureau: str
    model: str
    date: datetime
    factors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class MonitoringStatus:
    """Monitoring service status."""
    service_name: str
    is_connected: bool
    last_check: datetime
    user_enrolled: bool
    subscription_status: str
    next_update: Optional[datetime] = None
    error_message: Optional[str] = None

class CreditMonitoringProvider(ABC):
    """Abstract base class for credit monitoring providers."""
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with the monitoring service."""
        pass
    
    @abstractmethod
    async def get_credit_report(self, user_id: str) -> Dict[str, Any]:
        """Get latest credit report data."""
        pass
    
    @abstractmethod
    async def get_credit_score(self, user_id: str) -> List[CreditScore]:
        """Get current credit scores."""
        pass
    
    @abstractmethod
    async def detect_changes(self, user_id: str, last_check: datetime) -> List[CreditChange]:
        """Detect changes since last check."""
        pass
    
    @abstractmethod
    async def setup_alerts(self, user_id: str, alert_preferences: Dict[str, Any]) -> bool:
        """Setup monitoring alerts."""
        pass

class CreditKarmaProvider(CreditMonitoringProvider):
    """Credit Karma integration (example implementation)."""
    
    def __init__(self):
        super().__init__("CreditKarma")
        self.base_url = "https://api.creditkarma.com/v1"
        self.api_key = getattr(settings, 'credit_karma_api_key', None)
    
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with Credit Karma API."""
        if not self.api_key:
            logger.warning("Credit Karma API key not configured")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with self.session.get(
                f"{self.base_url}/auth/validate",
                headers=headers
            ) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"Credit Karma authentication failed: {e}")
            return False
    
    async def get_credit_report(self, user_id: str) -> Dict[str, Any]:
        """Get credit report from Credit Karma."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            async with self.session.get(
                f"{self.base_url}/users/{user_id}/creditreport",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Credit Karma API returned {response.status}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Failed to get Credit Karma report: {e}")
            return {}
    
    async def get_credit_score(self, user_id: str) -> List[CreditScore]:
        """Get credit scores from Credit Karma."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            async with self.session.get(
                f"{self.base_url}/users/{user_id}/scores",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    scores = []
                    
                    for score_data in data.get('scores', []):
                        scores.append(CreditScore(
                            score=score_data['score'],
                            bureau=score_data['bureau'],
                            model=score_data.get('model', 'VantageScore 3.0'),
                            date=datetime.fromisoformat(score_data['date']),
                            factors=score_data.get('factors', [])
                        ))
                    
                    return scores
                    
        except Exception as e:
            logger.error(f"Failed to get Credit Karma scores: {e}")
            
        return []
    
    async def detect_changes(self, user_id: str, last_check: datetime) -> List[CreditChange]:
        """Detect changes since last check."""
        changes = []
        
        try:
            # Get current report
            current_report = await self.get_credit_report(user_id)
            
            # Get cached previous report for comparison
            cache_key = f"creditkarma_report_{user_id}"
            previous_report = await cache.get(cache_key)
            
            if previous_report and current_report:
                changes = await self._compare_reports(
                    user_id, previous_report, current_report, "TransUnion"
                )
            
            # Cache current report
            await cache.set(cache_key, current_report, ttl=3600)
            
        except Exception as e:
            logger.error(f"Failed to detect Credit Karma changes: {e}")
        
        return changes
    
    async def setup_alerts(self, user_id: str, alert_preferences: Dict[str, Any]) -> bool:
        """Setup Credit Karma alerts."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            alert_data = {
                "user_id": user_id,
                "preferences": alert_preferences
            }
            
            async with self.session.post(
                f"{self.base_url}/users/{user_id}/alerts",
                headers=headers,
                json=alert_data
            ) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"Failed to setup Credit Karma alerts: {e}")
            return False
    
    async def _compare_reports(
        self, 
        user_id: str, 
        old_report: Dict, 
        new_report: Dict,
        bureau: str
    ) -> List[CreditChange]:
        """Compare two reports and identify changes."""
        changes = []
        
        # Compare accounts
        old_accounts = {acc['account_number']: acc for acc in old_report.get('accounts', [])}
        new_accounts = {acc['account_number']: acc for acc in new_report.get('accounts', [])}
        
        # New accounts
        for acc_num, account in new_accounts.items():
            if acc_num not in old_accounts:
                changes.append(CreditChange(
                    change_id=self._generate_change_id(user_id, "new_account", acc_num),
                    user_id=user_id,
                    change_type=ChangeType.NEW_ACCOUNT,
                    severity=Severity.MEDIUM,
                    title="New Account Opened",
                    description=f"New {account.get('type', 'account')} opened with {account.get('creditor', 'unknown creditor')}",
                    old_value=None,
                    new_value=f"{account.get('creditor', 'Unknown')} - {account.get('type', 'Account')}",
                    bureau=bureau,
                    detected_at=datetime.now(),
                    account_number=acc_num,
                    creditor_name=account.get('creditor'),
                    amount=account.get('balance')
                ))
        
        # Closed accounts
        for acc_num, account in old_accounts.items():
            if acc_num not in new_accounts:
                changes.append(CreditChange(
                    change_id=self._generate_change_id(user_id, "closed_account", acc_num),
                    user_id=user_id,
                    change_type=ChangeType.ACCOUNT_CLOSED,
                    severity=Severity.LOW,
                    title="Account Closed",
                    description=f"Account closed: {account.get('creditor', 'unknown creditor')}",
                    old_value=f"{account.get('creditor', 'Unknown')} - Active",
                    new_value="Closed",
                    bureau=bureau,
                    detected_at=datetime.now(),
                    account_number=acc_num,
                    creditor_name=account.get('creditor')
                ))
        
        # Changed accounts
        for acc_num in set(old_accounts.keys()) & set(new_accounts.keys()):
            old_acc = old_accounts[acc_num]
            new_acc = new_accounts[acc_num]
            
            # Balance changes
            old_balance = old_acc.get('balance', 0)
            new_balance = new_acc.get('balance', 0)
            
            if abs(old_balance - new_balance) > 10:  # Significant balance change
                severity = Severity.HIGH if abs(old_balance - new_balance) > 1000 else Severity.MEDIUM
                changes.append(CreditChange(
                    change_id=self._generate_change_id(user_id, "balance_change", acc_num),
                    user_id=user_id,
                    change_type=ChangeType.BALANCE_CHANGE,
                    severity=severity,
                    title="Balance Changed",
                    description=f"Balance changed on {new_acc.get('creditor', 'account')}",
                    old_value=f"${old_balance:,.2f}",
                    new_value=f"${new_balance:,.2f}",
                    bureau=bureau,
                    detected_at=datetime.now(),
                    account_number=acc_num,
                    creditor_name=new_acc.get('creditor'),
                    amount=new_balance - old_balance
                ))
            
            # Status changes
            old_status = old_acc.get('status', '')
            new_status = new_acc.get('status', '')
            
            if old_status != new_status:
                severity = self._determine_status_change_severity(old_status, new_status)
                changes.append(CreditChange(
                    change_id=self._generate_change_id(user_id, "status_change", acc_num),
                    user_id=user_id,
                    change_type=ChangeType.STATUS_CHANGE,
                    severity=severity,
                    title="Account Status Changed",
                    description=f"Status changed on {new_acc.get('creditor', 'account')}",
                    old_value=old_status,
                    new_value=new_status,
                    bureau=bureau,
                    detected_at=datetime.now(),
                    account_number=acc_num,
                    creditor_name=new_acc.get('creditor')
                ))
        
        return changes
    
    def _generate_change_id(self, user_id: str, change_type: str, identifier: str) -> str:
        """Generate unique change ID."""
        content = f"{user_id}_{change_type}_{identifier}_{datetime.now().strftime('%Y%m%d')}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _determine_status_change_severity(self, old_status: str, new_status: str) -> Severity:
        """Determine severity of status change."""
        positive_statuses = ['current', 'paid', 'closed']
        negative_statuses = ['late', 'charge off', 'collection', 'default']
        
        old_is_negative = any(neg in old_status.lower() for neg in negative_statuses)
        new_is_negative = any(neg in new_status.lower() for neg in negative_statuses)
        
        if not old_is_negative and new_is_negative:
            return Severity.CRITICAL  # Good to bad
        elif old_is_negative and not new_is_negative:
            return Severity.MEDIUM    # Bad to good
        else:
            return Severity.LOW       # Neutral change

class ExperianProvider(CreditMonitoringProvider):
    """Experian credit monitoring integration."""
    
    def __init__(self):
        super().__init__("Experian")
        self.base_url = "https://api.experian.com/consumerservices/v1"
        self.api_key = getattr(settings, 'experian_api_key', None)
    
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with Experian API."""
        # Implementation would go here
        return False  # Placeholder
    
    async def get_credit_report(self, user_id: str) -> Dict[str, Any]:
        """Get credit report from Experian."""
        # Implementation would go here
        return {}
    
    async def get_credit_score(self, user_id: str) -> List[CreditScore]:
        """Get credit scores from Experian."""
        # Implementation would go here
        return []
    
    async def detect_changes(self, user_id: str, last_check: datetime) -> List[CreditChange]:
        """Detect changes from Experian."""
        # Implementation would go here
        return []
    
    async def setup_alerts(self, user_id: str, alert_preferences: Dict[str, Any]) -> bool:
        """Setup Experian alerts."""
        # Implementation would go here
        return False

class CreditMonitoringService:
    """Main credit monitoring service that coordinates multiple providers."""
    
    def __init__(self):
        self.providers = {
            'creditkarma': CreditKarmaProvider(),
            'experian': ExperianProvider(),
            # Add more providers as needed
        }
        self.active_providers = []
        self.monitoring_tasks = {}
    
    async def initialize(self):
        """Initialize monitoring service."""
        logger.info("Initializing credit monitoring service...")
        
        # Test provider connections
        for name, provider in self.providers.items():
            try:
                async with provider:
                    if await provider.authenticate({}):
                        self.active_providers.append(name)
                        logger.info(f"✅ {name} provider initialized")
                    else:
                        logger.warning(f"❌ {name} provider failed to authenticate")
            except Exception as e:
                logger.error(f"Failed to initialize {name} provider: {e}")
        
        logger.info(f"Credit monitoring initialized with {len(self.active_providers)} active providers")
    
    async def enroll_user(
        self, 
        user_id: str, 
        provider_credentials: Dict[str, Dict[str, Any]],
        alert_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """Enroll user in credit monitoring."""
        logger.info(f"Enrolling user {user_id} in credit monitoring")
        
        enrollment_results = {}
        
        for provider_name in self.active_providers:
            provider = self.providers[provider_name]
            credentials = provider_credentials.get(provider_name, {})
            
            try:
                async with provider:
                    # Authenticate with user credentials
                    if await provider.authenticate(credentials):
                        # Setup alerts
                        alert_setup = await provider.setup_alerts(
                            user_id, 
                            alert_preferences or self._default_alert_preferences()
                        )
                        
                        enrollment_results[provider_name] = alert_setup
                        
                        if alert_setup:
                            # Start monitoring for this user and provider
                            await self._start_user_monitoring(user_id, provider_name)
                            logger.info(f"✅ User {user_id} enrolled with {provider_name}")
                        else:
                            logger.warning(f"❌ Alert setup failed for {provider_name}")
                    else:
                        enrollment_results[provider_name] = False
                        logger.warning(f"❌ Authentication failed for {provider_name}")
                        
            except Exception as e:
                enrollment_results[provider_name] = False
                logger.error(f"Enrollment failed for {provider_name}: {e}")
        
        # Store enrollment status
        await self._store_enrollment_status(user_id, enrollment_results)
        
        return enrollment_results
    
    async def check_for_changes(self, user_id: str, force_check: bool = False) -> List[CreditChange]:
        """Check for credit report changes for a user."""
        logger.info(f"Checking for credit changes for user {user_id}")
        
        all_changes = []
        
        # Get last check time
        last_check = await self._get_last_check_time(user_id)
        
        # Don't check too frequently unless forced
        if not force_check and last_check:
            time_since_last = datetime.now() - last_check
            if time_since_last < timedelta(hours=6):  # Minimum 6 hours between checks
                logger.info(f"Skipping check for {user_id} - checked {time_since_last} ago")
                return []
        
        for provider_name in self.active_providers:
            provider = self.providers[provider_name]
            
            try:
                async with provider:
                    changes = await provider.detect_changes(user_id, last_check or datetime.now() - timedelta(days=30))
                    
                    if changes:
                        all_changes.extend(changes)
                        logger.info(f"Found {len(changes)} changes from {provider_name}")
                        
            except Exception as e:
                logger.error(f"Failed to check changes from {provider_name}: {e}")
        
        # Update last check time
        await self._update_last_check_time(user_id)
        
        # Store changes
        if all_changes:
            await self._store_changes(all_changes)
        
        logger.info(f"Total changes found for {user_id}: {len(all_changes)}")
        
        return all_changes
    
    async def get_current_scores(self, user_id: str) -> Dict[str, List[CreditScore]]:
        """Get current credit scores from all providers."""
        logger.info(f"Getting current credit scores for user {user_id}")
        
        all_scores = {}
        
        for provider_name in self.active_providers:
            provider = self.providers[provider_name]
            
            try:
                async with provider:
                    scores = await provider.get_credit_score(user_id)
                    if scores:
                        all_scores[provider_name] = scores
                        logger.info(f"Got {len(scores)} scores from {provider_name}")
                        
            except Exception as e:
                logger.error(f"Failed to get scores from {provider_name}: {e}")
        
        return all_scores
    
    async def get_monitoring_status(self, user_id: str) -> List[MonitoringStatus]:
        """Get monitoring status for all providers."""
        statuses = []
        
        for provider_name in self.active_providers:
            try:
                # Get status from database or cache
                status_data = await self._get_provider_status(user_id, provider_name)
                
                status = MonitoringStatus(
                    service_name=provider_name,
                    is_connected=status_data.get('connected', False),
                    last_check=datetime.fromisoformat(status_data.get('last_check', datetime.now().isoformat())),
                    user_enrolled=status_data.get('enrolled', False),
                    subscription_status=status_data.get('subscription', 'inactive'),
                    next_update=datetime.fromisoformat(status_data.get('next_update')) if status_data.get('next_update') else None,
                    error_message=status_data.get('error')
                )
                
                statuses.append(status)
                
            except Exception as e:
                logger.error(f"Failed to get status for {provider_name}: {e}")
        
        return statuses
    
    async def start_continuous_monitoring(self):
        """Start continuous monitoring for all enrolled users."""
        logger.info("Starting continuous credit monitoring...")
        
        # Get all enrolled users
        enrolled_users = await self._get_enrolled_users()
        
        for user_id in enrolled_users:
            # Start monitoring task for each user
            task = asyncio.create_task(self._monitor_user_continuously(user_id))
            self.monitoring_tasks[user_id] = task
        
        logger.info(f"Started continuous monitoring for {len(enrolled_users)} users")
    
    async def stop_continuous_monitoring(self):
        """Stop continuous monitoring."""
        logger.info("Stopping continuous credit monitoring...")
        
        for user_id, task in self.monitoring_tasks.items():
            task.cancel()
        
        # Wait for all tasks to complete
        if self.monitoring_tasks:
            await asyncio.gather(*self.monitoring_tasks.values(), return_exceptions=True)
        
        self.monitoring_tasks.clear()
        logger.info("Continuous monitoring stopped")
    
    async def _monitor_user_continuously(self, user_id: str):
        """Continuously monitor a specific user."""
        logger.info(f"Starting continuous monitoring for user {user_id}")
        
        while True:
            try:
                # Check for changes
                changes = await self.check_for_changes(user_id)
                
                if changes:
                    # Send notifications for important changes
                    await self._send_change_notifications(user_id, changes)
                
                # Wait before next check (4-6 hours)
                await asyncio.sleep(4 * 3600 + (2 * 3600 * asyncio.get_event_loop().time() % 1))
                
            except asyncio.CancelledError:
                logger.info(f"Monitoring cancelled for user {user_id}")
                break
            except Exception as e:
                logger.error(f"Error in continuous monitoring for {user_id}: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error
    
    async def _send_change_notifications(self, user_id: str, changes: List[CreditChange]):
        """Send notifications for credit changes."""
        high_priority_changes = [
            change for change in changes 
            if change.severity in [Severity.HIGH, Severity.CRITICAL]
        ]
        
        if high_priority_changes:
            # Send immediate notifications
            await self._send_immediate_notifications(user_id, high_priority_changes)
        
        # Send daily summary if there are any changes
        if changes:
            await self._schedule_daily_summary(user_id, changes)
    
    async def _send_immediate_notifications(self, user_id: str, changes: List[CreditChange]):
        """Send immediate notifications for critical changes."""
        # Implementation would integrate with notification service
        logger.info(f"Sending {len(changes)} immediate notifications to user {user_id}")
    
    async def _schedule_daily_summary(self, user_id: str, changes: List[CreditChange]):
        """Schedule daily summary notification."""
        # Implementation would schedule summary notification
        logger.info(f"Scheduling daily summary for user {user_id} with {len(changes)} changes")
    
    def _default_alert_preferences(self) -> Dict[str, Any]:
        """Get default alert preferences."""
        return {
            "new_accounts": True,
            "balance_changes": True,
            "status_changes": True,
            "score_changes": True,
            "new_inquiries": True,
            "fraud_alerts": True,
            "daily_summary": True,
            "immediate_critical": True
        }
    
    async def _start_user_monitoring(self, user_id: str, provider_name: str):
        """Start monitoring for a specific user and provider."""
        # Store monitoring configuration
        await cache.set(
            f"monitoring_{user_id}_{provider_name}", 
            {"active": True, "started": datetime.now().isoformat()},
            ttl=86400
        )
    
    async def _store_enrollment_status(self, user_id: str, results: Dict[str, bool]):
        """Store user enrollment status."""
        # Implementation would store in database
        await cache.set(f"enrollment_{user_id}", results, ttl=86400)
    
    async def _get_last_check_time(self, user_id: str) -> Optional[datetime]:
        """Get last check time for user."""
        data = await cache.get(f"last_check_{user_id}")
        if data:
            return datetime.fromisoformat(data)
        return None
    
    async def _update_last_check_time(self, user_id: str):
        """Update last check time."""
        await cache.set(f"last_check_{user_id}", datetime.now().isoformat(), ttl=86400 * 7)
    
    async def _store_changes(self, changes: List[CreditChange]):
        """Store credit changes in database."""
        # Implementation would store changes in database
        for change in changes:
            logger.info(f"Storing change: {change.title} for user {change.user_id}")
    
    async def _get_provider_status(self, user_id: str, provider_name: str) -> Dict[str, Any]:
        """Get provider status for user."""
        return await cache.get(f"status_{user_id}_{provider_name}") or {}
    
    async def _get_enrolled_users(self) -> List[str]:
        """Get list of enrolled users."""
        # Implementation would get from database
        # For now, return empty list
        return []

# Global monitoring service instance
credit_monitoring_service = CreditMonitoringService()