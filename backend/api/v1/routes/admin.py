"""
Admin endpoints for system management
Restricted endpoints for administrative functions
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from core.security import get_supabase_user, require_admin_access
from schemas.responses import APIResponse, MetricsResponse
from schemas.requests import CacheManagementRequest
from services.monitoring import metrics_collector, monitor_api_call
from services.cache_service import cache
from services.background_jobs import job_processor
from services.database_optimizer import db_optimizer

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_admin_access)])

@router.get("/metrics/detailed", response_model=APIResponse[MetricsResponse])
@monitor_api_call
async def get_detailed_metrics(
    minutes: int = Query(60, ge=1, le=1440, description="Time range in minutes"),
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """
    Get detailed system metrics for admin monitoring.
    Includes comprehensive performance data across all subsystems.
    """
    try:
        # Get comprehensive metrics
        system_metrics = metrics_collector.get_system_metrics_summary(minutes)
        api_metrics = metrics_collector.get_api_metrics_summary(minutes)
        business_metrics = metrics_collector.get_business_metrics_summary(minutes)
        
        # Get service-specific stats
        job_stats = job_processor.get_detailed_stats() if job_processor else {}
        cache_stats = cache.detailed_stats()
        db_stats = await db_optimizer.get_performance_stats()
        
        # Add admin-specific metrics
        admin_metrics = {
            "active_users_last_hour": business_metrics.get("metrics", {}).get("user_activity", {}).get("count", 0),
            "error_rate_trend": _calculate_error_trend(api_metrics),
            "performance_alerts": _get_performance_alerts(system_metrics, api_metrics),
            "resource_utilization": _calculate_resource_utilization(system_metrics),
        }
        
        metrics_data = MetricsResponse(
            system={**system_metrics, **admin_metrics},
            api=api_metrics,
            business=business_metrics,
            background_jobs=job_stats,
            cache={**cache_stats, "database": db_stats}
        )
        
        return APIResponse[MetricsResponse](
            success=True,
            data=metrics_data,
            message=f"Detailed metrics for last {minutes} minutes"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")

@router.post("/cache/manage", response_model=APIResponse[Dict[str, Any]])
@monitor_api_call
async def manage_cache(
    request: CacheManagementRequest,
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """
    Manage application cache.
    Supports clear, warm, and stats operations across cache layers.
    """
    try:
        result = {}
        
        if request.action == "clear":
            if request.cache_type == "redis" or request.cache_type == "all":
                await cache.clear()
                result["redis_cleared"] = True
            
            if request.cache_type == "memory" or request.cache_type == "all":
                cache.clear_memory_cache()
                result["memory_cleared"] = True
            
            if request.cache_type == "all":
                db_optimizer.clear_cache()
                result["db_cache_cleared"] = True
            
            result["action"] = "cleared"
            message = f"Cache {request.cache_type or 'all'} cleared successfully"
            
        elif request.action == "warm":
            # Warm up frequently accessed data
            warmed_keys = await cache.warm_cache()
            result = {
                "action": "warmed",
                "warmed_keys": warmed_keys,
                "count": len(warmed_keys)
            }
            message = f"Cache warmed with {len(warmed_keys)} keys"
            
        elif request.action == "stats":
            cache_stats = cache.detailed_stats()
            db_cache_stats = db_optimizer.get_cache_stats()
            
            result = {
                "action": "stats",
                "cache_layers": {
                    "redis": cache_stats.get("redis", {}),
                    "memory": cache_stats.get("memory", {}),
                    "database": db_cache_stats
                },
                "overall_hit_rate": cache_stats.get("overall_hit_rate", 0),
                "total_operations": cache_stats.get("total_operations", 0)
            }
            message = "Cache statistics retrieved"
            
        else:
            raise HTTPException(status_code=400, detail="Invalid cache action")
        
        return APIResponse[Dict[str, Any]](
            success=True,
            data=result,
            message=message
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache management failed: {str(e)}")

@router.get("/jobs/monitor", response_model=APIResponse[Dict[str, Any]])
@monitor_api_call
async def monitor_background_jobs(
    status: Optional[str] = Query(None, description="Filter by job status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum jobs to return"),
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """
    Monitor background job processing.
    Provides admin visibility into job queue and processing status.
    """
    try:
        # Get job queue statistics
        job_stats = job_processor.get_detailed_stats() if job_processor else {}
        
        # Get recent jobs
        recent_jobs = job_processor.job_queue.get_recent_jobs(limit, status_filter=status)
        
        # Get processing performance
        processing_stats = {
            "avg_processing_time": job_processor.get_avg_processing_time(),
            "success_rate": job_processor.get_success_rate(),
            "failure_rate": job_processor.get_failure_rate(),
            "queue_health": job_processor.get_queue_health()
        }
        
        result = {
            "queue_stats": job_stats,
            "recent_jobs": [job.to_dict() for job in recent_jobs],
            "processing_performance": processing_stats,
            "system_status": {
                "worker_status": job_processor.is_running if job_processor else False,
                "queue_size": len(job_processor.job_queue.pending_jobs) if job_processor else 0,
                "active_workers": job_processor.active_workers if job_processor else 0
            }
        }
        
        return APIResponse[Dict[str, Any]](
            success=True,
            data=result,
            message=f"Retrieved {len(recent_jobs)} jobs and system stats"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job monitoring failed: {str(e)}")

@router.post("/jobs/{job_id}/retry", response_model=APIResponse[Dict[str, str]])
@monitor_api_call
async def retry_failed_job(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """Retry a failed background job."""
    try:
        success = await job_processor.retry_job(job_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Job cannot be retried")
        
        return APIResponse[Dict[str, str]](
            success=True,
            data={"job_id": job_id, "status": "retrying"},
            message="Job queued for retry"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job retry failed: {str(e)}")

@router.get("/system/health", response_model=APIResponse[Dict[str, Any]])
@monitor_api_call
async def get_system_health_detailed(
    current_user: Dict[str, Any] = Depends(get_supabase_user)
):
    """Get detailed system health information for admin monitoring."""
    try:
        # Get comprehensive health status
        health_status = metrics_collector.get_health_status()
        
        # Add detailed service checks
        service_health = {
            "database": await _check_database_health(),
            "cache": await _check_cache_health(),
            "background_jobs": _check_job_processor_health(),
            "monitoring": _check_monitoring_health(),
            "file_system": _check_filesystem_health()
        }
        
        # Calculate overall health score
        health_score = _calculate_health_score(health_status, service_health)
        
        result = {
            "overall_health": health_status,
            "service_health": service_health,
            "health_score": health_score,
            "recommendations": _get_health_recommendations(health_status, service_health),
            "alerts": _get_active_alerts(health_status, service_health)
        }
        
        return APIResponse[Dict[str, Any]](
            success=True,
            data=result,
            message="System health analysis complete"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

# Helper functions
def _calculate_error_trend(api_metrics: Dict[str, Any]) -> Dict[str, float]:
    """Calculate error rate trend."""
    current_error_rate = api_metrics.get("error_rate_percent", 0)
    return {
        "current_rate": current_error_rate,
        "status": "high" if current_error_rate > 5 else "normal" if current_error_rate > 1 else "low"
    }

def _get_performance_alerts(system_metrics: Dict[str, Any], api_metrics: Dict[str, Any]) -> List[Dict[str, str]]:
    """Get active performance alerts."""
    alerts = []
    
    if system_metrics.get("max_cpu_percent", 0) > 90:
        alerts.append({"type": "cpu", "level": "critical", "message": "High CPU usage detected"})
    
    if system_metrics.get("max_memory_percent", 0) > 90:
        alerts.append({"type": "memory", "level": "critical", "message": "High memory usage detected"})
    
    if api_metrics.get("error_rate_percent", 0) > 10:
        alerts.append({"type": "api", "level": "warning", "message": "High API error rate"})
    
    return alerts

def _calculate_resource_utilization(system_metrics: Dict[str, Any]) -> Dict[str, str]:
    """Calculate resource utilization status."""
    cpu_status = "high" if system_metrics.get("avg_cpu_percent", 0) > 70 else "normal"
    memory_status = "high" if system_metrics.get("avg_memory_percent", 0) > 80 else "normal"
    
    return {
        "cpu_status": cpu_status,
        "memory_status": memory_status,
        "overall": "high" if cpu_status == "high" or memory_status == "high" else "normal"
    }

async def _check_database_health() -> Dict[str, Any]:
    """Check database connectivity and performance."""
    try:
        stats = await db_optimizer.get_connection_health()
        return {"status": "healthy", "details": stats}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

async def _check_cache_health() -> Dict[str, Any]:
    """Check cache system health."""
    try:
        stats = cache.health_check()
        return {"status": "healthy", "details": stats}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

def _check_job_processor_health() -> Dict[str, Any]:
    """Check background job processor health."""
    try:
        if not job_processor or not job_processor.is_running:
            return {"status": "unhealthy", "error": "Job processor not running"}
        
        stats = job_processor.health_check()
        return {"status": "healthy", "details": stats}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

def _check_monitoring_health() -> Dict[str, Any]:
    """Check monitoring system health."""
    try:
        if not metrics_collector.is_collecting:
            return {"status": "unhealthy", "error": "Metrics collection not active"}
        
        return {"status": "healthy", "details": {"collecting": True}}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

def _check_filesystem_health() -> Dict[str, Any]:
    """Check filesystem health."""
    try:
        import os, shutil
        
        # Check temp directory
        temp_usage = shutil.disk_usage("/tmp")
        temp_percent = (temp_usage.used / temp_usage.total) * 100
        
        if temp_percent > 95:
            return {"status": "critical", "details": {"temp_usage_percent": temp_percent}}
        elif temp_percent > 80:
            return {"status": "warning", "details": {"temp_usage_percent": temp_percent}}
        else:
            return {"status": "healthy", "details": {"temp_usage_percent": temp_percent}}
            
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

def _calculate_health_score(health_status: Dict[str, Any], service_health: Dict[str, Any]) -> int:
    """Calculate overall system health score (0-100)."""
    base_score = 100
    
    # Deduct points for system issues
    if health_status.get("status") == "critical":
        base_score -= 40
    elif health_status.get("status") == "warning":
        base_score -= 20
    
    # Deduct points for unhealthy services
    unhealthy_services = sum(1 for service in service_health.values() if service.get("status") != "healthy")
    base_score -= (unhealthy_services * 15)
    
    return max(0, base_score)

def _get_health_recommendations(health_status: Dict[str, Any], service_health: Dict[str, Any]) -> List[str]:
    """Get health improvement recommendations."""
    recommendations = []
    
    if health_status.get("status") == "critical":
        recommendations.append("Immediate attention required for critical system issues")
    
    for service_name, service_data in service_health.items():
        if service_data.get("status") != "healthy":
            recommendations.append(f"Check {service_name} service: {service_data.get('error', 'Status check failed')}")
    
    return recommendations

def _get_active_alerts(health_status: Dict[str, Any], service_health: Dict[str, Any]) -> List[Dict[str, str]]:
    """Get active system alerts."""
    alerts = []
    
    for issue in health_status.get("issues", []):
        alerts.append({"type": "system", "message": issue, "level": "warning"})
    
    for service_name, service_data in service_health.items():
        if service_data.get("status") == "unhealthy":
            alerts.append({
                "type": "service",
                "message": f"{service_name} service is unhealthy",
                "level": "critical"
            })
    
    return alerts