"""
Performance monitoring and metrics collection service
Tracks system resources, API performance, and business metrics
"""
import asyncio
import logging
import psutil
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
import threading
from functools import wraps
import weakref

from core.config import get_settings
from services.cache_service import cache

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class SystemMetrics:
    """System resource metrics."""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_free_gb: float
    network_sent_mb: float
    network_recv_mb: float
    process_count: int
    thread_count: int


@dataclass
class APIMetrics:
    """API performance metrics."""
    timestamp: str
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    request_size_bytes: int
    response_size_bytes: int
    user_id: Optional[str]
    error_message: Optional[str] = None


@dataclass
class BusinessMetrics:
    """Business logic metrics."""
    timestamp: str
    metric_name: str
    metric_value: float
    metric_type: str  # counter, gauge, histogram
    tags: Dict[str, str]


class MetricsCollector:
    """Collects and aggregates various performance metrics."""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.system_metrics: deque = deque(maxlen=max_history)
        self.api_metrics: deque = deque(maxlen=max_history)
        self.business_metrics: deque = deque(maxlen=max_history)
        
        # Aggregated metrics
        self.endpoint_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'error_count': 0,
            'avg_response_time': 0.0,
            'min_response_time': float('inf'),
            'max_response_time': 0.0,
            'last_called': None
        })
        
        # System metrics tracking
        self.last_network_io = None
        self.is_collecting = False
        self.collection_task = None
    
    async def start_collection(self, interval: int = 60):
        """Start automatic metrics collection."""
        if self.is_collecting:
            return
        
        self.is_collecting = True
        self.collection_task = asyncio.create_task(self._collection_loop(interval))
        logger.info(f"Started metrics collection with {interval}s interval")
    
    async def stop_collection(self):
        """Stop metrics collection."""
        if not self.is_collecting:
            return
        
        self.is_collecting = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped metrics collection")
    
    async def _collection_loop(self, interval: int):
        """Main metrics collection loop."""
        while self.is_collecting:
            try:
                await self.collect_system_metrics()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(interval)
    
    async def collect_system_metrics(self):
        """Collect current system metrics."""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network IO
            network = psutil.net_io_counters()
            network_sent_mb = network.bytes_sent / 1024 / 1024
            network_recv_mb = network.bytes_recv / 1024 / 1024
            
            # Process info
            current_process = psutil.Process()
            process_count = len(psutil.pids())
            thread_count = current_process.num_threads()
            
            metrics = SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / 1024 / 1024,
                memory_available_mb=memory.available / 1024 / 1024,
                disk_percent=disk.percent,
                disk_used_gb=disk.used / 1024 / 1024 / 1024,
                disk_free_gb=disk.free / 1024 / 1024 / 1024,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                process_count=process_count,
                thread_count=thread_count
            )
            
            self.system_metrics.append(metrics)
            
            # Cache latest metrics
            await cache.set("latest_system_metrics", asdict(metrics), ttl=300)
            
            # Log warnings for high resource usage
            if cpu_percent > 80:
                logger.warning(f"High CPU usage: {cpu_percent:.1f}%")
            
            if memory.percent > 80:
                logger.warning(f"High memory usage: {memory.percent:.1f}%")
            
            if disk.percent > 90:
                logger.warning(f"High disk usage: {disk.percent:.1f}%")
                
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    def record_api_call(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        request_size_bytes: int = 0,
        response_size_bytes: int = 0,
        user_id: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """Record API call metrics."""
        try:
            metrics = APIMetrics(
                timestamp=datetime.now().isoformat(),
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time_ms=response_time_ms,
                request_size_bytes=request_size_bytes,
                response_size_bytes=response_size_bytes,
                user_id=user_id,
                error_message=error_message
            )
            
            self.api_metrics.append(metrics)
            
            # Update endpoint statistics
            endpoint_key = f"{method} {endpoint}"
            stats = self.endpoint_stats[endpoint_key]
            
            stats['count'] += 1
            stats['total_time'] += response_time_ms
            stats['last_called'] = datetime.now().isoformat()
            
            if status_code >= 400:
                stats['error_count'] += 1
            
            # Update response time stats
            stats['avg_response_time'] = stats['total_time'] / stats['count']
            stats['min_response_time'] = min(stats['min_response_time'], response_time_ms)
            stats['max_response_time'] = max(stats['max_response_time'], response_time_ms)
            
        except Exception as e:
            logger.error(f"Failed to record API metrics: {e}")
    
    def record_business_metric(
        self,
        metric_name: str,
        metric_value: float,
        metric_type: str = "counter",
        tags: Optional[Dict[str, str]] = None
    ):
        """Record business metrics."""
        try:
            metrics = BusinessMetrics(
                timestamp=datetime.now().isoformat(),
                metric_name=metric_name,
                metric_value=metric_value,
                metric_type=metric_type,
                tags=tags or {}
            )
            
            self.business_metrics.append(metrics)
            
        except Exception as e:
            logger.error(f"Failed to record business metric: {e}")
    
    def get_system_metrics_summary(self, minutes: int = 60) -> Dict[str, Any]:
        """Get system metrics summary for the last N minutes."""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        
        recent_metrics = [
            m for m in self.system_metrics
            if datetime.fromisoformat(m.timestamp) > cutoff
        ]
        
        if not recent_metrics:
            return {}
        
        return {
            'period_minutes': minutes,
            'sample_count': len(recent_metrics),
            'avg_cpu_percent': sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
            'max_cpu_percent': max(m.cpu_percent for m in recent_metrics),
            'avg_memory_percent': sum(m.memory_percent for m in recent_metrics) / len(recent_metrics),
            'max_memory_percent': max(m.memory_percent for m in recent_metrics),
            'avg_memory_used_mb': sum(m.memory_used_mb for m in recent_metrics) / len(recent_metrics),
            'disk_percent': recent_metrics[-1].disk_percent,  # Latest value
            'avg_thread_count': sum(m.thread_count for m in recent_metrics) / len(recent_metrics),
            'latest_metrics': asdict(recent_metrics[-1])
        }
    
    def get_api_metrics_summary(self, minutes: int = 60) -> Dict[str, Any]:
        """Get API metrics summary for the last N minutes."""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        
        recent_metrics = [
            m for m in self.api_metrics
            if datetime.fromisoformat(m.timestamp) > cutoff
        ]
        
        if not recent_metrics:
            return {}
        
        # Calculate summaries
        total_requests = len(recent_metrics)
        error_count = sum(1 for m in recent_metrics if m.status_code >= 400)
        avg_response_time = sum(m.response_time_ms for m in recent_metrics) / total_requests
        
        # Group by endpoint
        endpoint_summary = defaultdict(lambda: {'count': 0, 'errors': 0, 'total_time': 0})
        
        for metric in recent_metrics:
            key = f"{metric.method} {metric.endpoint}"
            endpoint_summary[key]['count'] += 1
            endpoint_summary[key]['total_time'] += metric.response_time_ms
            if metric.status_code >= 400:
                endpoint_summary[key]['errors'] += 1
        
        # Calculate averages
        for endpoint, stats in endpoint_summary.items():
            stats['avg_response_time'] = stats['total_time'] / stats['count']
            stats['error_rate'] = (stats['errors'] / stats['count']) * 100
        
        return {
            'period_minutes': minutes,
            'total_requests': total_requests,
            'error_count': error_count,
            'error_rate_percent': (error_count / total_requests) * 100 if total_requests > 0 else 0,
            'avg_response_time_ms': avg_response_time,
            'requests_per_minute': total_requests / minutes,
            'endpoint_summary': dict(endpoint_summary),
            'slowest_endpoints': sorted(
                self.endpoint_stats.items(),
                key=lambda x: x[1]['avg_response_time'],
                reverse=True
            )[:5]
        }
    
    def get_business_metrics_summary(self, minutes: int = 60) -> Dict[str, Any]:
        """Get business metrics summary."""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        
        recent_metrics = [
            m for m in self.business_metrics
            if datetime.fromisoformat(m.timestamp) > cutoff
        ]
        
        # Group by metric name
        metric_summary = defaultdict(list)
        for metric in recent_metrics:
            metric_summary[metric.metric_name].append(metric.metric_value)
        
        # Calculate aggregates
        summary = {}
        for metric_name, values in metric_summary.items():
            summary[metric_name] = {
                'count': len(values),
                'sum': sum(values),
                'avg': sum(values) / len(values),
                'min': min(values),
                'max': max(values)
            }
        
        return {
            'period_minutes': minutes,
            'metrics': summary
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status."""
        latest_system = self.system_metrics[-1] if self.system_metrics else None
        recent_api = self.get_api_metrics_summary(5)  # Last 5 minutes
        
        health_status = "healthy"
        issues = []
        
        if latest_system:
            if latest_system.cpu_percent > 90:
                health_status = "critical"
                issues.append(f"High CPU usage: {latest_system.cpu_percent:.1f}%")
            elif latest_system.cpu_percent > 70:
                health_status = "warning"
                issues.append(f"Elevated CPU usage: {latest_system.cpu_percent:.1f}%")
            
            if latest_system.memory_percent > 90:
                health_status = "critical"
                issues.append(f"High memory usage: {latest_system.memory_percent:.1f}%")
            elif latest_system.memory_percent > 80:
                health_status = "warning"
                issues.append(f"Elevated memory usage: {latest_system.memory_percent:.1f}%")
            
            if latest_system.disk_percent > 95:
                health_status = "critical"
                issues.append(f"Critical disk usage: {latest_system.disk_percent:.1f}%")
        
        if recent_api and recent_api.get('error_rate_percent', 0) > 10:
            health_status = "warning"
            issues.append(f"High API error rate: {recent_api['error_rate_percent']:.1f}%")
        
        return {
            'status': health_status,
            'timestamp': datetime.now().isoformat(),
            'issues': issues,
            'metrics_collected': {
                'system_samples': len(self.system_metrics),
                'api_calls': len(self.api_metrics),
                'business_metrics': len(self.business_metrics)
            }
        }


# Global metrics collector
metrics_collector = MetricsCollector()


# Decorator for API endpoint monitoring
def monitor_api_call(func):
    """Decorator to automatically monitor API endpoints."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        request = kwargs.get('request') or (args[0] if args and hasattr(args[0], 'url') else None)
        
        endpoint = getattr(request, 'url', {}).path if request else func.__name__
        method = getattr(request, 'method', 'UNKNOWN') if request else 'FUNCTION'
        
        try:
            result = await func(*args, **kwargs)
            
            response_time_ms = (time.time() - start_time) * 1000
            status_code = getattr(result, 'status_code', 200)
            
            metrics_collector.record_api_call(
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time_ms=response_time_ms,
                user_id=kwargs.get('user_id')
            )
            
            return result
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            
            metrics_collector.record_api_call(
                endpoint=endpoint,
                method=method,
                status_code=500,
                response_time_ms=response_time_ms,
                error_message=str(e),
                user_id=kwargs.get('user_id')
            )
            
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            
            response_time_ms = (time.time() - start_time) * 1000
            
            metrics_collector.record_api_call(
                endpoint=func.__name__,
                method='FUNCTION',
                status_code=200,
                response_time_ms=response_time_ms
            )
            
            return result
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            
            metrics_collector.record_api_call(
                endpoint=func.__name__,
                method='FUNCTION',
                status_code=500,
                response_time_ms=response_time_ms,
                error_message=str(e)
            )
            
            raise
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


# Performance tracking utilities
class PerformanceTracker:
    """Track performance of specific operations."""
    
    def __init__(self):
        self.operation_times: Dict[str, List[float]] = defaultdict(list)
        self.max_history = 100
    
    def track_operation(self, operation_name: str, duration_ms: float):
        """Track an operation's performance."""
        times = self.operation_times[operation_name]
        times.append(duration_ms)
        
        # Keep only recent measurements
        if len(times) > self.max_history:
            times.pop(0)
    
    def get_operation_stats(self, operation_name: str) -> Dict[str, float]:
        """Get statistics for an operation."""
        times = self.operation_times.get(operation_name, [])
        
        if not times:
            return {}
        
        return {
            'count': len(times),
            'avg_ms': sum(times) / len(times),
            'min_ms': min(times),
            'max_ms': max(times),
            'p95_ms': sorted(times)[int(len(times) * 0.95)] if len(times) > 20 else max(times),
            'p99_ms': sorted(times)[int(len(times) * 0.99)] if len(times) > 100 else max(times)
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get stats for all tracked operations."""
        return {
            operation: self.get_operation_stats(operation)
            for operation in self.operation_times.keys()
        }


# Global performance tracker
performance_tracker = PerformanceTracker()


# Context manager for tracking operations
class track_performance:
    """Context manager for tracking operation performance."""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            performance_tracker.track_operation(self.operation_name, duration_ms)


# Business metrics helpers
def track_pdf_processing_time(processing_time_ms: float, method: str):
    """Track PDF processing performance."""
    metrics_collector.record_business_metric(
        'pdf_processing_time_ms',
        processing_time_ms,
        'histogram',
        {'method': method}
    )


def track_tradelines_extracted(count: int, user_id: str):
    """Track number of tradelines extracted."""
    metrics_collector.record_business_metric(
        'tradelines_extracted',
        count,
        'counter',
        {'user_id': user_id}
    )


def track_user_activity(activity_type: str, user_id: str):
    """Track user activity."""
    metrics_collector.record_business_metric(
        'user_activity',
        1,
        'counter',
        {'activity_type': activity_type, 'user_id': user_id}
    )


# Initialize metrics collection on startup
async def start_monitoring():
    """Start all monitoring services."""
    await metrics_collector.start_collection(interval=60)
    logger.info("Monitoring services started")