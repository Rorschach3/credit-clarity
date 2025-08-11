"""
A/B Testing Framework for Pipeline Comparison
Tracks performance metrics and manages user routing
"""
import logging
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class TestVariant(str, Enum):
    """A/B test variants"""
    CONTROL = "control"  # V1 pipeline
    TREATMENT = "treatment"  # V2 pipeline
    AUTO = "auto"  # Automatic selection


@dataclass
class ABTestMetrics:
    """Metrics for A/B test tracking"""
    variant: TestVariant
    user_id: str
    file_size_mb: float
    processing_time_ms: float
    tradelines_extracted: int
    success: bool
    cost_usd: float
    method_used: str
    timestamp: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'variant': self.variant.value,
            'user_id': self.user_id,
            'file_size_mb': self.file_size_mb,
            'processing_time_ms': self.processing_time_ms,
            'tradelines_extracted': self.tradelines_extracted,
            'success': self.success,
            'cost_usd': self.cost_usd,
            'method_used': self.method_used,
            'timestamp': self.timestamp.isoformat(),
            'error_message': self.error_message
        }


@dataclass  
class ABTestConfig:
    """Configuration for A/B tests"""
    test_name: str
    treatment_percentage: float = 50.0  # Percentage of users to route to treatment
    enabled: bool = True
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_whitelist: List[str] = field(default_factory=list)  # Force these users to treatment
    user_blacklist: List[str] = field(default_factory=list)  # Force these users to control
    file_size_threshold_mb: Optional[float] = None  # Route large files to specific variant
    
    def is_active(self) -> bool:
        """Check if test is currently active"""
        if not self.enabled:
            return False
        
        now = datetime.now()
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        
        return True


class ABTestManager:
    """Manages A/B testing for pipeline comparison"""
    
    def __init__(self):
        self.metrics_storage = []  # In-memory storage (would use database in production)
        self.configs = {}
        
        # Default configuration for pipeline testing
        self.configs['pipeline_v2'] = ABTestConfig(
            test_name='pipeline_v2',
            treatment_percentage=30.0,  # Start with 30% to V2
            enabled=True,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30)  # 30-day test
        )
    
    def assign_variant(self, user_id: str, file_size_mb: float, config_name: str = 'pipeline_v2') -> TestVariant:
        """
        Assign user to test variant based on configuration
        Uses consistent hashing to ensure same user always gets same variant
        """
        config = self.configs.get(config_name)
        if not config or not config.is_active():
            return TestVariant.CONTROL
        
        # Check whitelist/blacklist first
        if user_id in config.user_whitelist:
            logger.info(f"User {user_id} in whitelist, assigning to TREATMENT")
            return TestVariant.TREATMENT
        
        if user_id in config.user_blacklist:
            logger.info(f"User {user_id} in blacklist, assigning to CONTROL")
            return TestVariant.CONTROL
        
        # File size based routing
        if config.file_size_threshold_mb:
            if file_size_mb > config.file_size_threshold_mb:
                logger.info(f"Large file ({file_size_mb}MB), routing to CONTROL for stability")
                return TestVariant.CONTROL
        
        # Consistent hash-based assignment
        hash_input = f"{user_id}_{config.test_name}".encode('utf-8')
        hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
        percentage = (hash_value % 100) + 1  # 1-100
        
        if percentage <= config.treatment_percentage:
            logger.info(f"User {user_id} assigned to TREATMENT (hash={percentage})")
            return TestVariant.TREATMENT
        else:
            logger.info(f"User {user_id} assigned to CONTROL (hash={percentage})")
            return TestVariant.CONTROL
    
    def record_metrics(self, metrics: ABTestMetrics):
        """Record A/B test metrics"""
        try:
            self.metrics_storage.append(metrics)
            
            # Log for monitoring
            logger.info(
                f"AB Test: {metrics.variant.value} | "
                f"User: {metrics.user_id} | "
                f"Success: {metrics.success} | "
                f"Time: {metrics.processing_time_ms}ms | "
                f"Tradelines: {metrics.tradelines_extracted} | "
                f"Cost: ${metrics.cost_usd:.4f}"
            )
            
            # In production, you'd save to a database here
            # await self._save_to_database(metrics)
            
        except Exception as e:
            logger.error(f"Failed to record AB test metrics: {e}")
    
    def get_test_results(self, config_name: str = 'pipeline_v2', days: int = 7) -> Dict[str, Any]:
        """Get A/B test results for analysis"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter metrics by date and test
        relevant_metrics = [
            m for m in self.metrics_storage 
            if m.timestamp >= cutoff_date
        ]
        
        if not relevant_metrics:
            return {
                'test_name': config_name,
                'period_days': days,
                'total_samples': 0,
                'variants': {},
                'recommendation': 'insufficient_data'
            }
        
        # Group by variant
        variants = {}
        for variant in TestVariant:
            if variant == TestVariant.AUTO:
                continue
                
            variant_metrics = [m for m in relevant_metrics if m.variant == variant]
            
            if not variant_metrics:
                variants[variant.value] = {
                    'sample_size': 0,
                    'success_rate': 0,
                    'avg_processing_time_ms': 0,
                    'avg_tradelines_extracted': 0,
                    'total_cost_usd': 0,
                    'avg_cost_per_file': 0
                }
                continue
            
            # Calculate metrics
            total_files = len(variant_metrics)
            successful_files = len([m for m in variant_metrics if m.success])
            total_processing_time = sum(m.processing_time_ms for m in variant_metrics)
            total_tradelines = sum(m.tradelines_extracted for m in variant_metrics)
            total_cost = sum(m.cost_usd for m in variant_metrics)
            
            variants[variant.value] = {
                'sample_size': total_files,
                'success_rate': (successful_files / total_files) * 100 if total_files > 0 else 0,
                'avg_processing_time_ms': total_processing_time / total_files if total_files > 0 else 0,
                'avg_tradelines_extracted': total_tradelines / total_files if total_files > 0 else 0,
                'total_cost_usd': total_cost,
                'avg_cost_per_file': total_cost / total_files if total_files > 0 else 0,
                'method_breakdown': self._get_method_breakdown(variant_metrics)
            }
        
        # Statistical analysis and recommendation
        recommendation = self._analyze_results(variants)
        
        return {
            'test_name': config_name,
            'period_days': days,
            'total_samples': len(relevant_metrics),
            'variants': variants,
            'recommendation': recommendation,
            'config': self.configs.get(config_name, {}).to_dict() if hasattr(self.configs.get(config_name, {}), 'to_dict') else {}
        }
    
    def _get_method_breakdown(self, metrics: List[ABTestMetrics]) -> Dict[str, int]:
        """Get breakdown of methods used"""
        method_counts = {}
        for metric in metrics:
            method = metric.method_used
            method_counts[method] = method_counts.get(method, 0) + 1
        return method_counts
    
    def _analyze_results(self, variants: Dict[str, Any]) -> str:
        """Analyze test results and provide recommendation"""
        try:
            control = variants.get('control', {})
            treatment = variants.get('treatment', {})
            
            control_sample = control.get('sample_size', 0)
            treatment_sample = treatment.get('sample_size', 0)
            
            # Need sufficient sample size
            min_sample_size = 50
            if control_sample < min_sample_size or treatment_sample < min_sample_size:
                return 'insufficient_sample_size'
            
            # Compare key metrics
            control_success = control.get('success_rate', 0)
            treatment_success = treatment.get('success_rate', 0)
            
            control_time = control.get('avg_processing_time_ms', 0)
            treatment_time = treatment.get('avg_processing_time_ms', 0)
            
            control_cost = control.get('avg_cost_per_file', 0)
            treatment_cost = treatment.get('avg_cost_per_file', 0)
            
            # Decision logic
            success_improvement = treatment_success - control_success
            time_improvement = (control_time - treatment_time) / control_time * 100 if control_time > 0 else 0
            cost_difference = treatment_cost - control_cost
            
            # Treatment is clearly better
            if success_improvement >= 5 and time_improvement >= 10 and cost_difference <= 0.01:
                return 'treatment_winner_launch'
            
            # Treatment is worse
            elif success_improvement <= -5 or cost_difference >= 0.05:
                return 'control_winner_stop_test'
            
            # Mixed results
            elif abs(success_improvement) < 2 and abs(time_improvement) < 5:
                return 'no_significant_difference'
            
            else:
                return 'continue_testing'
                
        except Exception as e:
            logger.error(f"Error analyzing AB test results: {e}")
            return 'analysis_error'
    
    def update_config(self, config_name: str, **updates):
        """Update test configuration"""
        if config_name in self.configs:
            config = self.configs[config_name]
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                    logger.info(f"Updated {config_name}.{key} = {value}")
        else:
            logger.warning(f"Config {config_name} not found")
    
    def get_active_tests(self) -> List[str]:
        """Get list of active test names"""
        return [
            name for name, config in self.configs.items() 
            if config.is_active()
        ]


# Global instance
ab_test_manager = ABTestManager()


def track_pipeline_performance(
    variant: TestVariant,
    user_id: str,
    file_size_mb: float,
    processing_time_ms: float,
    tradelines_extracted: int,
    success: bool,
    cost_usd: float,
    method_used: str,
    error_message: Optional[str] = None
):
    """Convenience function to track pipeline performance"""
    metrics = ABTestMetrics(
        variant=variant,
        user_id=user_id,
        file_size_mb=file_size_mb,
        processing_time_ms=processing_time_ms,
        tradelines_extracted=tradelines_extracted,
        success=success,
        cost_usd=cost_usd,
        method_used=method_used,
        error_message=error_message
    )
    
    ab_test_manager.record_metrics(metrics)