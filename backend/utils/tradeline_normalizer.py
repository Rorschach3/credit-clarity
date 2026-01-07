"""
Legacy wrapper providing the unified EnhancedTradelineNormalizer for compatibility.
"""

from .enhanced_tradeline_normalizer import EnhancedTradelineNormalizer

TradelineNormalizer = EnhancedTradelineNormalizer
tradeline_normalizer = EnhancedTradelineNormalizer()
