"""
Comprehensive Monitoring and Observability System
Provides error tracking, performance monitoring, and health checks
"""
import logging
import time
import traceback
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from functools import wraps
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict
import asyncio
import psutil
import json

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ErrorInfo:
    """Structured error information"""
    error_id: str
    timestamp: str
    error_type: str
    error_message: str
    stack_trace: str
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    severity: str = "error"
    tags: Dict[str, Any] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = {}

@dataclass
class PerformanceMetric:
    """Performance measurement data"""
    metric_name: str
    value: float
    timestamp: str
    unit: str = "ms"
    tags: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}

@dataclass
class SystemHealth:
    """System health status"""
    status: str  # healthy, warning, critical
    timestamp: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_connections: int
    response_time_avg: float
    error_rate: float
    uptime: float

class MonitoringService:
    """Central monitoring and observability service"""
    
    def __init__(self):
        self.errors: List[ErrorInfo] = []
        self.metrics: List[PerformanceMetric] = []
        self.request_times: List[float] = []
        self.error_count = 0
        self.request_count = 0
        self.start_time = time.time()
        self.max_stored_errors = 1000
        self.max_stored_metrics = 5000
        
    def track_error(self, 
                   error: Exception,
                   request: Optional[Request] = None,
                   user_id: Optional[str] = None,
                   severity: str = "error",
                   tags: Optional[Dict[str, Any]] = None) -> str:
        """Track and store error information"""
        
        error_id = f"err_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        error_info = ErrorInfo(
            error_id=error_id,
            timestamp=datetime.utcnow().isoformat(),
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            request_id=getattr(request.state, 'request_id', None) if request else None,
            user_id=user_id,
            endpoint=str(request.url.path) if request else None,
            method=request.method if request else None,
            severity=severity,
            tags=tags or {}
        )
        
        # Store error
        self.errors.append(error_info)
        
        # Rotate if too many errors
        if len(self.errors) > self.max_stored_errors:
            self.errors = self.errors[-self.max_stored_errors:]
        
        self.error_count += 1
        
        # Log error
        logger.error(
            f"Error tracked: {error_id}",
            extra={
                "error_id": error_id,
                "error_type": error_info.error_type,
                "error_message": error_info.error_message,
                "endpoint": error_info.endpoint,
                "user_id": user_id,
                "severity": severity
            }
        )
        
        return error_id
    
    def track_metric(self, 
                    name: str, 
                    value: float, 
                    unit: str = "ms",
                    tags: Optional[Dict[str, Any]] = None):
        """Track performance metric"""
        
        metric = PerformanceMetric(
            metric_name=name,
            value=value,
            timestamp=datetime.utcnow().isoformat(),
            unit=unit,
            tags=tags or {}
        )
        
        self.metrics.append(metric)
        
        # Rotate if too many metrics
        if len(self.metrics) > self.max_stored_metrics:
            self.metrics = self.metrics[-self.max_stored_metrics:]
    
    def track_request_time(self, duration: float):
        """Track API request duration"""
        self.request_times.append(duration)
        self.request_count += 1
        
        # Keep only recent request times for averaging
        if len(self.request_times) > 1000:
            self.request_times = self.request_times[-1000:]
        
        # Track as metric
        self.track_metric("request_duration", duration, "ms")
    
    def get_system_health(self) -> SystemHealth:
        """Get current system health status"""
        
        # Calculate metrics
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Calculate averages
        avg_response_time = sum(self.request_times) / len(self.request_times) if self.request_times else 0
        
        # Calculate error rate (errors per 100 requests)
        error_rate = (self.error_count / max(self.request_count, 1)) * 100
        
        # Determine health status
        status = "healthy"
        if cpu_usage > 80 or memory.percent > 85 or error_rate > 5:
            status = "warning"
        if cpu_usage > 95 or memory.percent > 95 or error_rate > 15:
            status = "critical"
        
        return SystemHealth(
            status=status,
            timestamp=datetime.utcnow().isoformat(),
            cpu_usage=cpu_usage,
            memory_usage=memory.percent,
            disk_usage=disk.percent,
            active_connections=0,  # Would need to track this separately
            response_time_avg=avg_response_time,
            error_rate=error_rate,
            uptime=time.time() - self.start_time
        )
    
    def get_recent_errors(self, limit: int = 50, severity: Optional[str] = None) -> List[Dict]:
        """Get recent errors"""
        errors = self.errors
        
        if severity:
            errors = [e for e in errors if e.severity == severity]
        
        return [asdict(error) for error in errors[-limit:]]
    
    def get_metrics_summary(self, metric_name: Optional[str] = None, 
                           time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get metrics summary for the specified time window"""
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        relevant_metrics = [
            m for m in self.metrics 
            if datetime.fromisoformat(m.timestamp.replace('Z', '+00:00')) >= cutoff_time
        ]
        
        if metric_name:
            relevant_metrics = [m for m in relevant_metrics if m.metric_name == metric_name]
        
        if not relevant_metrics:
            return {"count": 0, "average": 0, "min": 0, "max": 0}
        
        values = [m.value for m in relevant_metrics]
        
        return {
            "count": len(values),
            "average": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "time_window_minutes": time_window_minutes
        }

# Global monitoring instance
monitoring = MonitoringService()

class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to track requests and responses"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = f"req_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        request.state.request_id = request_id
        
        # Track start time
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Track metrics
            monitoring.track_request_time(duration)
            monitoring.track_metric(
                "endpoint_response_time",
                duration,
                "ms",
                {
                    "endpoint": str(request.url.path),
                    "method": request.method,
                    "status_code": response.status_code
                }
            )
            
            # Add monitoring headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration:.2f}ms"
            
            return response
            
        except Exception as e:
            # Track error
            error_id = monitoring.track_error(
                e, 
                request=request,
                severity="error" if not isinstance(e, HTTPException) else "warning"
            )
            
            # Calculate duration for failed requests too
            duration = (time.time() - start_time) * 1000
            monitoring.track_request_time(duration)
            
            # Return error response with tracking info
            status_code = 500
            if isinstance(e, HTTPException):
                status_code = e.status_code
            
            return JSONResponse(
                status_code=status_code,
                content={
                    "error": str(e),
                    "error_id": error_id,
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat()
                },
                headers={
                    "X-Request-ID": request_id,
                    "X-Error-ID": error_id,
                    "X-Response-Time": f"{duration:.2f}ms"
                }
            )

def track_performance(metric_name: str, tags: Optional[Dict[str, Any]] = None):
    """Decorator to track function performance"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                monitoring.track_error(e, severity="error", tags=tags)
                raise
            finally:
                duration = (time.time() - start_time) * 1000
                monitoring.track_metric(metric_name, duration, "ms", tags)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                monitoring.track_error(e, severity="error", tags=tags)
                raise
            finally:
                duration = (time.time() - start_time) * 1000
                monitoring.track_metric(metric_name, duration, "ms", tags)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

@asynccontextmanager
async def track_operation(operation_name: str, 
                         tags: Optional[Dict[str, Any]] = None,
                         user_id: Optional[str] = None):
    """Context manager to track operation performance"""
    start_time = time.time()
    operation_id = f"op_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    
    logger.info(f"Starting operation: {operation_name} (ID: {operation_id})")
    
    try:
        yield operation_id
        duration = (time.time() - start_time) * 1000
        logger.info(f"Operation completed: {operation_name} (ID: {operation_id}, Duration: {duration:.2f}ms)")
        
        monitoring.track_metric(
            f"operation_{operation_name}",
            duration,
            "ms",
            {**(tags or {}), "operation_id": operation_id, "user_id": user_id}
        )
        
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"Operation failed: {operation_name} (ID: {operation_id}, Duration: {duration:.2f}ms)")
        
        monitoring.track_error(
            e,
            user_id=user_id,
            severity="error",
            tags={**(tags or {}), "operation_name": operation_name, "operation_id": operation_id}
        )
        raise

class HealthChecker:
    """System health checking utilities"""
    
    @staticmethod
    async def check_database_health() -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            from core.database import get_db_connection
            
            start_time = time.time()
            
            # Test database connection
            async with get_db_connection() as db:
                await db.execute("SELECT 1")
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": duration,
                "message": "Database connection successful"
            }
            
        except Exception as e:
            monitoring.track_error(e, severity="critical", tags={"health_check": "database"})
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Database connection failed"
            }
    
    @staticmethod
    async def check_supabase_health() -> Dict[str, Any]:
        """Check Supabase connectivity"""
        try:
            from core.config import get_settings
            import httpx
            
            settings = get_settings()
            
            start_time = time.time()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.SUPABASE_URL}/rest/v1/",
                    headers={"apikey": settings.SUPABASE_ANON_KEY},
                    timeout=5.0
                )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "response_time_ms": duration,
                    "message": "Supabase connection successful"
                }
            else:
                return {
                    "status": "unhealthy",
                    "status_code": response.status_code,
                    "message": "Supabase returned non-200 status"
                }
                
        except Exception as e:
            monitoring.track_error(e, severity="warning", tags={"health_check": "supabase"})
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Supabase connection failed"
            }
    
    @staticmethod
    async def comprehensive_health_check() -> Dict[str, Any]:
        """Run all health checks"""
        
        checks = {
            "system": asdict(monitoring.get_system_health()),
            "database": await HealthChecker.check_database_health(),
            "supabase": await HealthChecker.check_supabase_health(),
        }
        
        # Determine overall status
        statuses = [check.get("status", "unknown") for check in checks.values()]
        
        if "unhealthy" in statuses or "critical" in statuses:
            overall_status = "unhealthy"
        elif "warning" in statuses:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        return {
            "overall_status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks,
            "uptime": time.time() - monitoring.start_time
        }

# Export monitoring utilities
__all__ = [
    'monitoring',
    'MonitoringMiddleware',
    'track_performance',
    'track_operation',
    'HealthChecker',
    'ErrorInfo',
    'PerformanceMetric',
    'SystemHealth'
]