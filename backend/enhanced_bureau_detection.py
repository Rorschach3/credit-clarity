import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import Counter

@dataclass
class BureauIndicator:
    """Represents a bureau detection indicator with confidence score"""
    bureau: str
    confidence: float
    evidence: str
    position: int = -1

class EnhancedBureauDetector:
    """Advanced credit bureau detection with multiple detection strategies"""
    
    def __init__(self):
        # Primary bureau identifiers (high confidence)
        self.primary_patterns = {
            'Experian': [
                r'\bExperian\b',
                r'\bEXPERIAN\b',
                r'experian\.com',
                r'Experian Information Solutions',
                r'Experian Consumer Services',
                r'P\.O\. Box 4000.*Allen.*TX.*75013',
                r'Allen,?\s*TX\s*75013'
            ],
            'Equifax': [
                r'\bEquifax\b',
                r'\bEQUIFAX\b',
                r'equifax\.com',
                r'Equifax Information Services',
                r'Equifax Credit Information Services',
                r'P\.O\. Box 740256.*Atlanta.*GA.*30374',
                r'Atlanta,?\s*GA\s*30374'
            ],
            'TransUnion': [
                r'\bTransUnion\b',
                r'\bTRANSUNION\b',
                r'\bTrans Union\b',
                r'transunion\.com',
                r'TransUnion LLC',
                r'P\.O\. Box 2000.*Chester.*PA.*19016',
                r'Chester,?\s*PA\s*19016'
            ]
        }
        
        # Secondary indicators (medium confidence)
        self.secondary_patterns = {
            'Experian': [
                r'Consumer Disclosure.*Experian',
                r'Credit Profile.*Experian',
                r'Personal Credit Report.*Experian',
                r'FICO.*Score.*Experian',
                r'Experian.*Credit.*Report'
            ],
            'Equifax': [
                r'Consumer Disclosure.*Equifax',
                r'Credit File Disclosure.*Equifax', 
                r'Personal Credit Report.*Equifax',
                r'FICO.*Score.*Equifax',
                r'Equifax.*Credit.*Report'
            ],
            'TransUnion': [
                r'Consumer Disclosure.*TransUnion',
                r'Credit Report.*TransUnion',
                r'Personal Credit Report.*TransUnion',
                r'VantageScore.*TransUnion',
                r'TransUnion.*Credit.*Report'
            ]
        }
        
        # Format-specific patterns (lower confidence but still useful)
        self.format_patterns = {
            'Experian': [
                r'Account\s+Name\s+Account\s+Number\s+Date\s+Opened',  # Common Experian table header
                r'Potentially\s+Negative\s+Items',
                r'Accounts\s+in\s+Good\s+Standing'
            ],
            'Equifax': [
                r'Account\s+history\s+as\s+of',
                r'Credit\s+Accounts\s+Summary',
                r'The\s+following\s+accounts\s+are\s+listed\s+on\s+your\s+credit\s+file'
            ],
            'TransUnion': [
                r'Account\s+Information\s+Summary',
                r'Satisfactory\s+Accounts',
                r'Potentially\s+Negative\s+Accounts'
            ]
        }
        
        # Logo/header detection patterns
        self.header_patterns = {
            'Experian': [r'^\s*EXPERIAN\s*$', r'EXPERIAN\s+CONSUMER\s+SERVICES'],
            'Equifax': [r'^\s*EQUIFAX\s*$', r'EQUIFAX\s+CREDIT\s+SERVICES'],
            'TransUnion': [r'^\s*TRANSUNION\s*$', r'^\s*TRANS\s+UNION\s*$']
        }
    
    def extract_indicators(self, text: str) -> List[BureauIndicator]:
        """Extract all bureau indicators from text with positions and confidence scores"""
        indicators = []
        text_upper = text.upper()
        
        # Check primary patterns (high confidence)
        for bureau, patterns in self.primary_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    indicators.append(BureauIndicator(
                        bureau=bureau,
                        confidence=0.9,
                        evidence=match.group(0),
                        position=match.start()
                    ))
        
        # Check secondary patterns (medium confidence)
        for bureau, patterns in self.secondary_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    indicators.append(BureauIndicator(
                        bureau=bureau,
                        confidence=0.7,
                        evidence=match.group(0),
                        position=match.start()
                    ))
        
        # Check format patterns (lower confidence)
        for bureau, patterns in self.format_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    indicators.append(BureauIndicator(
                        bureau=bureau,
                        confidence=0.5,
                        evidence=match.group(0),
                        position=match.start()
                    ))
        
        # Check header patterns (very high confidence if found early in document)
        first_1000_chars = text[:1000]
        for bureau, patterns in self.header_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, first_1000_chars, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    indicators.append(BureauIndicator(
                        bureau=bureau,
                        confidence=0.95,
                        evidence=match.group(0),
                        position=match.start()
                    ))
        
        return sorted(indicators, key=lambda x: (x.position, -x.confidence))
    
    def calculate_bureau_scores(self, indicators: List[BureauIndicator], text_length: int = 10000) -> Dict[str, float]:
        """Calculate weighted scores for each bureau based on all indicators"""
        scores = {'Experian': 0.0, 'Equifax': 0.0, 'TransUnion': 0.0}
        
        for indicator in indicators:
            # Apply position weighting (earlier in document = higher weight)
            position_weight = 1.0
            if indicator.position >= 0:
                # Higher weight for indicators found in first 20% of document
                doc_position_ratio = indicator.position / max(text_length, 1)
                if doc_position_ratio <= 0.2:
                    position_weight = 1.3
                elif doc_position_ratio <= 0.5:
                    position_weight = 1.1
                else:
                    position_weight = 0.9
            
            weighted_score = indicator.confidence * position_weight
            scores[indicator.bureau] += weighted_score
        
        return scores
    
    def detect_credit_bureau(self, text: str, confidence_threshold: float = 0.6) -> Tuple[str, float, List[str]]:
        """
        Detect credit bureau from text with confidence score and evidence
        
        Returns:
            (bureau_name: str, confidence: float, evidence_list: List[str])
        """
        if not text or len(text.strip()) < 50:
            return "Unknown", 0.0, ["Document too short"]
        
        # Extract all indicators
        indicators = self.extract_indicators(text)
        
        if not indicators:
            return "Unknown", 0.0, ["No bureau indicators found"]
        
        # Calculate scores for each bureau
        scores = self.calculate_bureau_scores(indicators, len(text))
        
        # Find the bureau with highest score
        best_bureau = max(scores.keys(), key=lambda k: scores[k])
        best_score = scores[best_bureau]
        
        # Normalize score (convert to 0-1 scale)
        max_possible_score = len(indicators) * 0.95 * 1.3  # Max possible weighted score
        normalized_score = min(best_score / max(max_possible_score, 1.0), 1.0) if max_possible_score > 0 else 0.0
        
        # Collect evidence
        evidence = [ind.evidence for ind in indicators if ind.bureau == best_bureau]
        
        # Apply confidence threshold
        if normalized_score < confidence_threshold:
            return "Unknown", normalized_score, evidence
        
        return best_bureau, normalized_score, evidence
    
    def detect_multiple_bureaus(self, text: str) -> Dict[str, Dict]:
        """
        Detect if document contains multiple bureau reports
        
        Returns:
            {
                'Experian': {'confidence': 0.8, 'evidence': [...], 'start_pos': 0},
                'Equifax': {'confidence': 0.6, 'evidence': [...], 'start_pos': 5000},
                ...
            }
        """
        indicators = self.extract_indicators(text)
        bureau_data = {}
        
        # Group indicators by bureau
        for bureau in ['Experian', 'Equifax', 'TransUnion']:
            bureau_indicators = [ind for ind in indicators if ind.bureau == bureau]
            
            if bureau_indicators:
                scores = {bureau: 0.0}
                for ind in bureau_indicators:
                    scores[bureau] += ind.confidence
                
                # Normalize score
                max_score = len(bureau_indicators) * 0.95
                normalized = min(scores[bureau] / max(max_score, 1.0), 1.0)
                
                if normalized > 0.3:  # Lower threshold for multi-bureau detection
                    # Get positions that are >= 0
                    valid_positions = [ind.position for ind in bureau_indicators if ind.position >= 0]
                    start_pos = min(valid_positions) if valid_positions else 0
                    
                    bureau_data[bureau] = {
                        'confidence': normalized,
                        'evidence': [ind.evidence for ind in bureau_indicators],
                        'start_pos': start_pos,
                        'indicator_count': len(bureau_indicators)
                    }
        
        return bureau_data

# Usage in your main processing code
def enhanced_detect_credit_bureau(text_content: str) -> str:
    """
    Enhanced bureau detection to replace your existing detect_credit_bureau function
    """
    detector = EnhancedBureauDetector()
    bureau, confidence, evidence = detector.detect_credit_bureau(text_content)
    
    print(f"Bureau Detection Results:")
    print(f"  - Detected: {bureau}")
    print(f"  - Confidence: {confidence:.2f}")
    print(f"  - Evidence: {evidence[:3]}")  # Show first 3 pieces of evidence
    
    return bureau

# For processing documents that might contain multiple bureau reports
def split_multi_bureau_document(text_content: str) -> Dict[str, str]:
    """
    Split a document that contains multiple bureau reports
    """
    detector = EnhancedBureauDetector()
    bureau_data = detector.detect_multiple_bureaus(text_content)
    
    if len(bureau_data) <= 1:
        # Single bureau document
        bureau, _, _ = detector.detect_credit_bureau(text_content)
        return {bureau: text_content}
    
    # Multi-bureau document - attempt to split
    splits = {}
    sorted_bureaus = sorted(bureau_data.items(), key=lambda x: x[1]['start_pos'])
    
    for i, (bureau, data) in enumerate(sorted_bureaus):
        start_pos = data['start_pos']
        
        # Find end position (start of next bureau or end of document)
        if i + 1 < len(sorted_bureaus):
            end_pos = sorted_bureaus[i + 1][1]['start_pos']
        else:
            end_pos = len(text_content)
        
        # Extract the section for this bureau
        bureau_section = text_content[start_pos:end_pos]
        splits[bureau] = bureau_section
    
    return splits