"""
Unified Negative Tradeline Classifier
Implements multi-factor scoring for accurate identification of negative accounts.
"""
import re
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

@dataclass
class ClassificationResult:
    """Result of negative tradeline classification."""
    is_negative: bool
    confidence: float
    score: float
    factors: Dict[str, float]
    indicators: List[str]
    classification_method: str

class NegativeTradelineClassifier:
    """
    Classifier for identifying negative/derogatory tradelines using multi-factor analysis.
    """
    
    def __init__(self):
        # Weights for different factors
        self.weights = {
            'status': 0.40,
            'payment_history': 0.30,
            'balance': 0.15,
            'creditor': 0.10,
            'remarks': 0.05
        }
        
        # Negative indicators
        self.status_keywords = {
            'charge off': 1.0, 'charged off': 1.0, 'paid charge off': 1.0,
            'collection': 1.0, 'collections': 1.0, 'in collection': 1.0,
            'bankruptcy': 1.0, 'chapter 7': 1.0, 'chapter 13': 1.0,
            'foreclosure': 1.0, 'repossession': 1.0, 'repo': 1.0,
            'default': 0.9, 'defaulted': 0.9,
            'delinquent': 0.8, 'seriously delinquent': 0.9,
            'settled': 0.8, 'settlement': 0.8, 'settled for less': 1.0,
            'government claim': 0.9, 'claim filed': 0.8,
            'written off': 1.0, 'write off': 1.0
        }
        
        self.payment_history_keywords = {
            '120': 1.0, '90': 0.9, '60': 0.7, '30': 0.4,
            'late': 0.5, 'past due': 0.6
        }
        
        self.collection_agencies = [
            'midland', 'portfolio recovery', 'lvnv', 'cavalry', 'jefferson capital',
            'enhanced recovery', 'convergent', 'diversified', 'resurgent', 'sherman'
        ]
    
    def classify(self, tradeline: Dict[str, Any]) -> ClassificationResult:
        """
        Classify a tradeline as negative or positive.
        """
        factors = {
            'status': self._analyze_status(tradeline.get('account_status', '')),
            'payment_history': self._analyze_payment_history(tradeline.get('payment_history', '')),
            'balance': self._analyze_balance(tradeline),
            'creditor': self._analyze_creditor(tradeline.get('creditor_name', '')),
            'remarks': self._analyze_remarks(tradeline.get('comments', '') or tradeline.get('remarks', ''))
        }
        
        # Calculate weighted score
        score = sum(factors[key] * self.weights[key] for key in factors)
        
        # Determine classification
        # Threshold 0.50 means likely negative
        is_negative = score >= 0.50
        
        # Determine confidence
        # Higher score = higher confidence for negative
        # Lower score = higher confidence for positive
        if is_negative:
            confidence = min(1.0, score + 0.2) # Boost confidence if threshold met
        else:
            confidence = min(1.0, (1.0 - score) + 0.1)
            
        # Collect indicators
        indicators = []
        if factors['status'] > 0: indicators.append(f"Status score: {factors['status']:.2f}")
        if factors['payment_history'] > 0: indicators.append(f"Payment history score: {factors['payment_history']:.2f}")
        if factors['balance'] > 0: indicators.append(f"Balance score: {factors['balance']:.2f}")
        if factors['creditor'] > 0: indicators.append(f"Creditor score: {factors['creditor']:.2f}")
        
        return ClassificationResult(
            is_negative=is_negative,
            confidence=confidence,
            score=score,
            factors=factors,
            indicators=indicators,
            classification_method='rule_based_weighted'
        )
    
    def _analyze_status(self, status: str) -> float:
        """Analyze account status for negative indicators."""
        if not status:
            return 0.0
        
        status_lower = status.lower()
        max_score = 0.0
        
        # Check direct keywords
        for keyword, score in self.status_keywords.items():
            if keyword in status_lower:
                max_score = max(max_score, score)
        
        # Check contextual rules
        if 'closed' in status_lower and 'paid' in status_lower and max_score == 0:
            # "Closed - Paid in Full" is positive
            return 0.0
            
        return max_score
    
    def _analyze_payment_history(self, history: str) -> float:
        """Analyze payment history for lates."""
        if not history:
            return 0.0
            
        history_lower = history.lower()
        score = 0.0
        
        # Check specific late markers
        if '120' in history_lower or '90' in history_lower:
            score = 1.0
        elif '60' in history_lower:
            score = 0.7
        elif '30' in history_lower:
            score = 0.4
        elif 'late' in history_lower or 'past due' in history_lower:
            score = 0.5
            
        return score
    
    def _analyze_balance(self, tradeline: Dict[str, Any]) -> float:
        """Analyze balance vs limit and closed status."""
        try:
            balance_str = str(tradeline.get('account_balance', '0')).replace('$', '').replace(',', '')
            limit_str = str(tradeline.get('credit_limit', '0')).replace('$', '').replace(',', '')
            status = str(tradeline.get('account_status', '')).lower()
            
            balance = float(balance_str) if balance_str.replace('.', '', 1).isdigit() else 0.0
            limit = float(limit_str) if limit_str.replace('.', '', 1).isdigit() else 0.0
            
            # Closed with balance
            if 'closed' in status and balance > 0:
                return 0.8
                
            # Over limit
            if limit > 0 and balance > limit * 1.05:
                return 0.5
                
            return 0.0
        except:
            return 0.0
            
    def _analyze_creditor(self, creditor: str) -> float:
        """Analyze creditor name for collection agencies."""
        if not creditor:
            return 0.0
            
        creditor_lower = creditor.lower()
        
        for agency in self.collection_agencies:
            if agency in creditor_lower:
                return 1.0
        
        if 'collection' in creditor_lower or 'recovery' in creditor_lower:
            return 0.8
            
        return 0.0
    
    def _analyze_remarks(self, remarks: str) -> float:
        """Analyze remarks for negative keywords."""
        if not remarks:
            return 0.0
            
        remarks_lower = remarks.lower()
        max_score = 0.0
        
        for keyword, score in self.status_keywords.items():
            if keyword in remarks_lower:
                max_score = max(max_score, score)
                
        return max_score
