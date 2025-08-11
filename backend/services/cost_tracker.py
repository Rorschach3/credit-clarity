"""
Cost tracking service for OCR methods
Monitors usage and cost of different extraction methods
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class OCRMethod(str, Enum):
    """OCR extraction methods"""
    PDFPLUMBER = "pdfplumber"
    PYMUPDF = "pymupdf" 
    TESSERACT = "tesseract_ocr"
    DOCUMENT_AI = "document_ai"


@dataclass
class CostEntry:
    """Individual cost tracking entry"""
    user_id: str
    method: OCRMethod
    file_size_mb: float
    processing_time_ms: float
    cost_usd: float
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)
    pages_processed: Optional[int] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'user_id': self.user_id,
            'method': self.method.value,
            'file_size_mb': self.file_size_mb,
            'processing_time_ms': self.processing_time_ms,
            'cost_usd': self.cost_usd,
            'success': self.success,
            'timestamp': self.timestamp.isoformat(),
            'pages_processed': self.pages_processed,
            'error_message': self.error_message
        }


class CostTracker:
    """Tracks and analyzes OCR method costs and usage"""
    
    def __init__(self):
        self.cost_entries = []  # In-memory storage (would use database in production)
        
        # Cost structure (per page or per MB)
        self.cost_rates = {
            OCRMethod.PDFPLUMBER: 0.0,      # Free
            OCRMethod.PYMUPDF: 0.0,         # Free
            OCRMethod.TESSERACT: 0.0,       # Free (but requires compute resources)
            OCRMethod.DOCUMENT_AI: 0.0015   # Google Document AI: ~$1.50 per 1000 pages
        }
        
        # Track method success rates
        self.method_stats = {}
    
    def calculate_cost(self, method: OCRMethod, pages: int = 1, file_size_mb: float = 1.0) -> float:
        """Calculate cost for OCR method"""
        base_rate = self.cost_rates.get(method, 0.0)
        
        if method == OCRMethod.DOCUMENT_AI:
            # Document AI charges per page
            return base_rate * pages
        else:
            # Free methods have no direct cost
            return 0.0
    
    def record_usage(
        self,
        user_id: str,
        method: OCRMethod,
        file_size_mb: float,
        processing_time_ms: float,
        success: bool,
        pages_processed: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """Record usage of an OCR method"""
        
        # Calculate cost
        cost_usd = self.calculate_cost(method, pages_processed or 1, file_size_mb)
        
        # Create entry
        entry = CostEntry(
            user_id=user_id,
            method=method,
            file_size_mb=file_size_mb,
            processing_time_ms=processing_time_ms,
            cost_usd=cost_usd,
            success=success,
            pages_processed=pages_processed,
            error_message=error_message
        )
        
        self.cost_entries.append(entry)
        
        # Update method stats
        self._update_method_stats(method, success, processing_time_ms, cost_usd)
        
        # Log usage
        logger.info(
            f"OCR Usage: {method.value} | "
            f"User: {user_id} | "
            f"Size: {file_size_mb:.1f}MB | "
            f"Time: {processing_time_ms:.0f}ms | "
            f"Cost: ${cost_usd:.4f} | "
            f"Success: {success}"
        )
        
        # Alert on expensive usage
        if cost_usd > 0.01:  # Alert if cost > $0.01
            logger.warning(f"Expensive OCR usage: ${cost_usd:.4f} for {method.value}")
    
    def _update_method_stats(self, method: OCRMethod, success: bool, time_ms: float, cost: float):
        """Update running statistics for each method"""
        if method.value not in self.method_stats:
            self.method_stats[method.value] = {
                'total_uses': 0,
                'successful_uses': 0,
                'total_time_ms': 0,
                'total_cost': 0,
                'avg_time_ms': 0,
                'success_rate': 0,
                'avg_cost': 0
            }
        
        stats = self.method_stats[method.value]
        stats['total_uses'] += 1
        if success:
            stats['successful_uses'] += 1
        stats['total_time_ms'] += time_ms
        stats['total_cost'] += cost
        
        # Update averages
        stats['avg_time_ms'] = stats['total_time_ms'] / stats['total_uses']
        stats['success_rate'] = (stats['successful_uses'] / stats['total_uses']) * 100
        stats['avg_cost'] = stats['total_cost'] / stats['total_uses']
    
    def get_usage_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get usage summary for specified period"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter entries by date
        recent_entries = [
            entry for entry in self.cost_entries 
            if entry.timestamp >= cutoff_date
        ]
        
        if not recent_entries:
            return {
                'period_days': days,
                'total_files': 0,
                'total_cost': 0,
                'methods': {},
                'cost_breakdown': {},
                'recommendations': []
            }
        
        # Calculate summary metrics
        total_files = len(recent_entries)
        total_cost = sum(entry.cost_usd for entry in recent_entries)
        successful_files = len([e for e in recent_entries if e.success])
        
        # Method breakdown
        method_breakdown = {}
        cost_breakdown = {}
        
        for method in OCRMethod:
            method_entries = [e for e in recent_entries if e.method == method]
            
            if method_entries:
                total_uses = len(method_entries)
                successful_uses = len([e for e in method_entries if e.success])
                method_cost = sum(e.cost_usd for e in method_entries)
                avg_time = sum(e.processing_time_ms for e in method_entries) / total_uses
                
                method_breakdown[method.value] = {
                    'uses': total_uses,
                    'success_rate': (successful_uses / total_uses) * 100,
                    'avg_processing_time_ms': avg_time,
                    'total_cost_usd': method_cost,
                    'avg_cost_per_use': method_cost / total_uses if total_uses > 0 else 0
                }
                
                cost_breakdown[method.value] = method_cost
        
        # Generate recommendations
        recommendations = self._generate_recommendations(method_breakdown, total_cost)
        
        return {
            'period_days': days,
            'total_files': total_files,
            'successful_files': successful_files,
            'overall_success_rate': (successful_files / total_files) * 100,
            'total_cost_usd': total_cost,
            'avg_cost_per_file': total_cost / total_files if total_files > 0 else 0,
            'methods': method_breakdown,
            'cost_breakdown': cost_breakdown,
            'recommendations': recommendations
        }
    
    def _generate_recommendations(self, method_breakdown: Dict[str, Any], total_cost: float) -> List[str]:
        """Generate cost optimization recommendations"""
        recommendations = []
        
        # Check if expensive methods are being overused
        docai_usage = method_breakdown.get('document_ai', {})
        if docai_usage.get('uses', 0) > 0:
            docai_cost = docai_usage.get('total_cost_usd', 0)
            if docai_cost > total_cost * 0.5:  # More than 50% of total cost
                recommendations.append(
                    "High Document AI usage detected. Consider improving free method success rates."
                )
        
        # Check success rates of free methods
        free_methods = ['pdfplumber', 'pymupdf', 'tesseract_ocr']
        poor_performers = []
        
        for method in free_methods:
            method_data = method_breakdown.get(method, {})
            success_rate = method_data.get('success_rate', 100)  # Assume 100% if no data
            
            if success_rate < 70:  # Less than 70% success rate
                poor_performers.append(method)
        
        if poor_performers:
            recommendations.append(
                f"Low success rates for: {', '.join(poor_performers)}. "
                f"Consider tuning extraction parameters."
            )
        
        # Cost efficiency
        if total_cost > 1.0:  # More than $1 total
            recommendations.append(
                "Consider implementing caching to reduce repeated processing costs."
            )
        
        # Volume recommendations
        total_files = sum(m.get('uses', 0) for m in method_breakdown.values())
        if total_files > 100:
            recommendations.append(
                "High volume processing detected. Consider bulk processing optimizations."
            )
        
        return recommendations
    
    def get_method_performance(self) -> Dict[str, Any]:
        """Get performance comparison of all methods"""
        return {
            'methods': self.method_stats,
            'cost_rates': {method.value: rate for method, rate in self.cost_rates.items()},
            'recommendations': {
                'fastest': self._get_fastest_method(),
                'cheapest': self._get_cheapest_method(),
                'most_reliable': self._get_most_reliable_method(),
                'best_overall': self._get_best_overall_method()
            }
        }
    
    def _get_fastest_method(self) -> Optional[str]:
        """Get the fastest method based on average processing time"""
        if not self.method_stats:
            return None
        
        fastest = min(
            self.method_stats.items(),
            key=lambda x: x[1]['avg_time_ms'] if x[1]['success_rate'] > 50 else float('inf')
        )
        return fastest[0] if fastest[1]['success_rate'] > 50 else None
    
    def _get_cheapest_method(self) -> Optional[str]:
        """Get the cheapest method that works"""
        if not self.method_stats:
            return None
        
        cheapest = min(
            self.method_stats.items(),
            key=lambda x: x[1]['avg_cost'] if x[1]['success_rate'] > 50 else float('inf')
        )
        return cheapest[0] if cheapest[1]['success_rate'] > 50 else None
    
    def _get_most_reliable_method(self) -> Optional[str]:
        """Get the most reliable method"""
        if not self.method_stats:
            return None
        
        most_reliable = max(
            self.method_stats.items(),
            key=lambda x: x[1]['success_rate']
        )
        return most_reliable[0] if most_reliable[1]['success_rate'] > 0 else None
    
    def _get_best_overall_method(self) -> Optional[str]:
        """Get best overall method considering cost, speed, and reliability"""
        if not self.method_stats:
            return None
        
        # Score based on weighted criteria
        def calculate_score(stats):
            success_weight = 0.4
            cost_weight = 0.3  
            speed_weight = 0.3
            
            # Normalize metrics (higher is better)
            success_score = stats['success_rate'] / 100
            
            # Cost score (lower cost is better, so invert)
            max_cost = max(s['avg_cost'] for s in self.method_stats.values())
            cost_score = 1 - (stats['avg_cost'] / max_cost) if max_cost > 0 else 1
            
            # Speed score (faster is better, so invert) 
            max_time = max(s['avg_time_ms'] for s in self.method_stats.values())
            speed_score = 1 - (stats['avg_time_ms'] / max_time) if max_time > 0 else 1
            
            return (success_score * success_weight + 
                   cost_score * cost_weight + 
                   speed_score * speed_weight)
        
        best = max(
            self.method_stats.items(),
            key=lambda x: calculate_score(x[1])
        )
        
        return best[0]
    
    def export_data(self, days: int = 30) -> List[Dict[str, Any]]:
        """Export cost tracking data for analysis"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        return [
            entry.to_dict() 
            for entry in self.cost_entries 
            if entry.timestamp >= cutoff_date
        ]


# Global cost tracker instance
cost_tracker = CostTracker()