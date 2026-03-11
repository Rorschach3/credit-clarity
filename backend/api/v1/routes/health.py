"""
Health check and system status endpoints
Provides system health monitoring and diagnostics
"""
from fastapi import APIRouter, Depends, Request
from typing import Dict, Any
from datetime import datetime

from core.security import get_current_user_optional
from schemas.responses import APIResponse, HealthResponse, MetricsResponse
import services.monitoring as monitoring
import services.cache_service as cache_service
import services.background_jobs as background_jobs
from core.config import get_settings
from utils.async_utils import maybe_await

router = APIRouter(prefix="/health", tags=["Health"])
settings = get_settings()

def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}

@router.get("/", response_model=APIResponse[HealthResponse])
@monitoring.monitor_api_call
async def health_check(request: Request):
    """
    Comprehensive health check endpoint.
    Returns system status, service availability, and basic metrics.
    """
    try:
        # Basic service checks
        services_status = {
            "api": True,
            "cache": True,
            "background_jobs": background_jobs.job_processor.is_running if background_jobs.job_processor else False,
            "monitoring": monitoring.metrics_collector is not None,
            "database": True  # Add actual DB health check
        }
        
        # Get system health if available
        system_health = None
        try:
            system_health = monitoring.metrics_collector.get_health_status()
            if not isinstance(system_health, dict):
                system_health = None
        except Exception:
            pass
        
        # Get cache stats
        cache_stats = None
        try:
            cache_stats = cache_service.cache.stats()
            if not isinstance(cache_stats, dict):
                cache_stats = None
        except Exception:
            pass
        
        health_data = HealthResponse(
            status="healthy",
            timestamp=datetime.now(),
            version="1.0",
            environment=settings.environment,
            services=services_status,
            system_health=system_health
        )
        
        return APIResponse[HealthResponse](
            success=True,
            data=health_data,
            message="System is healthy"
        )
        
    except Exception as e:
        return APIResponse[HealthResponse](
            success=False,
            message=f"Health check failed: {str(e)}"
        )

@router.get("/live", response_model=APIResponse[Dict[str, str]])
async def liveness_check():
    """
    Kubernetes/Docker liveness probe endpoint.
    Simple check that API is responding.
    """
    return APIResponse[Dict[str, str]](
        success=True,
        data={"status": "alive"},
        message="API is alive"
    )

@router.get("/ready", response_model=APIResponse[Dict[str, Any]])
async def readiness_check():
    """
    Kubernetes/Docker readiness probe endpoint.
    Checks if all services are ready to handle requests.
    """
    services_ready = {
        "cache": True,
        "background_jobs": background_jobs.job_processor.is_running if background_jobs.job_processor else False,
        "monitoring": monitoring.metrics_collector is not None,
    }
    
    all_ready = all(services_ready.values())
    
    return APIResponse[Dict[str, Any]](
        success=all_ready,
        data={
            "ready": all_ready,
            "services": services_ready
        },
        message="All services ready" if all_ready else "Some services not ready"
    )

@router.get("/metrics", response_model=APIResponse[MetricsResponse])
@monitoring.monitor_api_call
async def get_basic_metrics(
    request: Request,
    minutes: int = 5,
    current_user: Dict[str, Any] = Depends(get_current_user_optional)
):
    """
    Basic system metrics endpoint.
    Returns simplified metrics for monitoring dashboards.
    """
    try:
        # Get basic metrics
        system_metrics = _safe_dict(monitoring.metrics_collector.get_system_metrics_summary(minutes))
        api_metrics = _safe_dict(monitoring.metrics_collector.get_api_metrics_summary(minutes))
        business_metrics = _safe_dict(monitoring.metrics_collector.get_business_metrics_summary(minutes))
        
        # Get service stats
        job_stats = (
            await maybe_await(background_jobs.job_processor.get_stats())
            if background_jobs.job_processor
            else {}
        )
        cache_stats = _safe_dict(cache_service.cache.stats())
        
        metrics_data = MetricsResponse(
            system=system_metrics,
            api=api_metrics,
            business=business_metrics,
            background_jobs=job_stats,
            cache=cache_stats
        )
        
        return APIResponse[MetricsResponse](
            success=True,
            data=metrics_data,
            message=f"Metrics for last {minutes} minutes"
        )
        
    except Exception as e:
        return APIResponse[MetricsResponse](
            success=False,
            message=f"Failed to get metrics: {str(e)}"
        )
