"""
Virus Scanner Service for Credit Clarity
Handles file scanning for malware and malicious content
"""
import hashlib
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class ScanResult:
    """Result of a virus scan."""
    clean: bool
    threats_found: list
    scan_time_ms: float
    scanner: str
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "clean": self.clean,
            "threats_found": self.threats_found,
            "scan_time_ms": self.scan_time_ms,
            "scanner": self.scanner,
            "details": self.details or {}
        }


class VirusScanner:
    """
    File virus scanning service.
    
    Supports multiple scanning backends:
    - ClamAV (local installation)
    - Cloud-based scanning (placeholder)
    - Heuristic analysis (basic pattern matching)
    """
    
    def __init__(self):
        """Initialize virus scanner."""
        self.scanner_name = "credit_clarity_scanner"
        self.heuristic_threshold = 0.7  # Confidence threshold for heuristic detection
        
        # Known malicious patterns (simplified for demo - in production use proper signatures)
        self._suspicious_patterns = [
            # Executable signatures in wrong places
            (r'\x4D\x5A', 'PE executable signature'),
            (r'\x7F\x45\x4C\x46', 'ELF executable signature'),
            (r'#!/bin/(bash|sh|python)', 'Shell script header'),
            # JavaScript/VBScript patterns that could be malicious
            (r'<script[^>]*>[\s\S]*?eval\s*\(', 'Potential script injection'),
            (r'(document\.cookie|localStorage\.setItem)', 'Data exfiltration attempt'),
            # PowerShell/CMD patterns
            (r'powershell.*-enc|--EncodedCommand', 'Encoded PowerShell command'),
            (r'cmd\.exe\s+/c\s+', 'CMD command execution'),
            # Common malware indicators
            (r'(wget|curl).*\|\s*(bash|sh)', 'Pipe to shell'),
            (r'\$ENV\{[A-Z_]+\}', 'Environment variable access'),
            # Archive bombs (zip bombs)
            (r'^PK\x03\x04', 'ZIP archive'),
            # PDF suspicious patterns
            (r'/OpenAction\s+<<', 'PDF open action'),
            (r'/JS\s*/JavaScript', 'PDF JavaScript'),
            (r'/AA\s*<<', 'PDF automatic action'),
        ]
        
        # File type allowlist/denylist
        self._allowed_types = {
            'application/pdf': '.pdf',
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'text/plain': '.txt',
            'text/csv': '.csv',
            'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
        }
        
        self._blocked_types = {
            'application/x-executable': '.exe',
            'application/x-sh': '.sh',
            'application/javascript': '.js',
            'text/html': '.html',
            'application/x-msdownload': '.dll',
        }
    
    async def scan_file(
        self,
        file_content: bytes,
        filename: str = "unknown"
    ) -> ScanResult:
        """
        Scan a file for malware and malicious content.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            
        Returns:
            ScanResult with scan outcome
        """
        import time
        start_time = time.time()
        
        threats = []
        details = {}
        
        # 1. Check file size (potential zip bomb)
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > 100:  # Files over 100MB are suspicious
            threats.append({
                "type": "SIZE_SUSPICIOUS",
                "description": f"File size {file_size_mb:.2f}MB exceeds maximum allowed",
                "severity": "high"
            })
            details["file_size_mb"] = file_size_mb
        
        # 2. Check file type
        file_type = self._detect_file_type(file_content, filename)
        details["detected_type"] = file_type
        
        if file_type in self._blocked_types:
            threats.append({
                "type": "FILE_TYPE_BLOCKED",
                "description": f"File type {file_type} is not allowed",
                "severity": "critical",
                "extension": self._blocked_types[file_type]
            })
        
        # 3. Heuristic pattern scanning
        if file_content:
            try:
                content_text = file_content.decode('utf-8', errors='ignore')
                content_hex = file_content.hex()
                
                pattern_threats = self._scan_patterns(content_text, content_hex)
                threats.extend(pattern_threats)
            except Exception as e:
                logger.warning(f"Could not decode file content for scanning: {e}")
                details["decode_warning"] = str(e)
        
        # 4. Calculate file hash for signature matching
        file_hash = hashlib.sha256(file_content).hexdigest()
        details["sha256_hash"] = file_hash
        
        # Check against known bad hashes (placeholder - in production use threat intel feed)
        known_bad_hashes = self._get_known_bad_hashes()
        if file_hash in known_bad_hashes:
            threats.append({
                "type": "KNOWN_MALWARE",
                "description": "File matches known malware signature",
                "severity": "critical",
                "hash": file_hash
            })
        
        # 5. Attempt ClamAV integration if available
        clamav_result = await self._scan_with_clamav(file_content, filename)
        if clamav_result:
            threats.extend(clamav_result)
        
        # Calculate scan time
        scan_time_ms = (time.time() - start_time) * 1000
        
        # Determine if file is clean
        clean = len([t for t in threats if t.get("severity") in ["critical", "high"]]) == 0
        
        return ScanResult(
            clean=clean,
            threats_found=threats,
            scan_time_ms=scan_time_ms,
            scanner=self.scanner_name,
            details=details
        )
    
    async def scan_file_async(self, file_path: str) -> ScanResult:
        """
        Scan a file from disk asynchronously.
        
        Args:
            file_path: Path to file on disk
            
        Returns:
            ScanResult with scan outcome
        """
        import aiofiles
        import time
        
        start_time = time.time()
        
        threats = []
        details = {}
        
        try:
            # Read file content
            async with aiofiles.open(file_path, 'rb') as f:
                file_content = await f.read()
            
            # Run scan
            filename = file_path.split('/')[-1]
            scan_result = await self.scan_file(file_content, filename)
            
            return scan_result
            
        except Exception as e:
            logger.error(f"Failed to scan file {file_path}: {e}")
            
            return ScanResult(
                clean=False,
                threats_found=[{
                    "type": "SCAN_FAILED",
                    "description": str(e),
                    "severity": "high"
                }],
                scan_time_ms=(time.time() - start_time) * 1000,
                scanner=self.scanner_name,
                details={"error": str(e)}
            )
    
    def _detect_file_type(
        self,
        file_content: bytes,
        filename: str
    ) -> str:
        """
        Detect file type from content and filename.
        
        Args:
            file_content: File bytes
            filename: Original filename
            
        Returns:
            Detected MIME type
        """
        # Check magic bytes first
        if len(file_content) >= 4:
            magic = file_content[:4]
            
            # PDF
            if file_content.startswith(b'%PDF'):
                return 'application/pdf'
            
            # JPEG
            if magic[:2] == b'\xFF\xD8':
                return 'image/jpeg'
            
            # PNG
            if magic == b'\x89PNG':
                return 'image/png'
            
            # GIF
            if magic[:3] == b'GIF':
                return 'image/gif'
            
            # ZIP (also used for docx, xlsx, etc.)
            if magic == b'PK\x03\x04':
                return 'application/zip'
        
        # Fall back to filename extension
        if filename:
            ext = filename.lower().split('.')[-1] if '.' in filename else ''
            
            extension_map = {
                'pdf': 'application/pdf',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'webp': 'image/webp',
                'txt': 'text/plain',
                'csv': 'text/csv',
                'doc': 'application/msword',
                'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            }
            
            if ext in extension_map:
                return extension_map[ext]
        
        return 'application/octet-stream'
    
    def _scan_patterns(
        self,
        content_text: str,
        content_hex: str
    ) -> list:
        """
        Scan content for suspicious patterns.
        
        Args:
            content_text: Decoded text content
            content_hex: Hex-encoded content
            
        Returns:
            List of detected threats
        """
        threats = []
        
        for pattern, description in self._suspicious_patterns:
            try:
                if re.search(pattern, content_text, re.IGNORECASE):
                    threats.append({
                        "type": "PATTERN_DETECTED",
                        "description": description,
                        "severity": "medium",
                        "pattern": pattern
                    })
            except re.error:
                # Skip invalid regex patterns
                continue
        
        return threats
    
    async def _scan_with_clamav(
        self,
        file_content: bytes,
        filename: str
    ) -> Optional[list]:
        """
        Scan file with ClamAV if available.
        
        Args:
            file_content: File content
            filename: Original filename
            
        Returns:
            List of threats or None if ClamAV not available
        """
        # Placeholder for ClamAV integration
        # In production, you would use clamd or clamscan via subprocess
        # or connect to clamav daemon
        
        try:
            # Check if clamav is available
            import shutil
            clamav_path = shutil.which('clamscan') or shutil.which('clamdscan')
            
            if not clamav_path:
                logger.debug("ClamAV not found, skipping ClamAV scan")
                return None
            
            # TODO: Implement actual ClamAV scanning
            # This would typically involve:
            # 1. Writing file to temp location
            # 2. Running clamscan/clamdscan
            # 3. Parsing output
            # 4. Cleaning up temp file
            
            logger.debug("ClamAV available but not yet implemented")
            return None
            
        except Exception as e:
            logger.warning(f"ClamAV scan failed: {e}")
            return None
    
    def _get_known_bad_hashes(self) -> set:
        """
        Get set of known bad file hashes.
        
        Returns:
            Set of SHA-256 hashes of known malware
        """
        # Placeholder - in production use threat intelligence feed
        # Example: AlienVault OTX, VirusTotal, etc.
        return set()
    
    async def quick_scan(
        self,
        file_content: bytes,
        filename: str = "unknown"
    ) -> Tuple[bool, str]:
        """
        Quick scan for common issues.
        
        Args:
            file_content: File content
            filename: Original filename
            
        Returns:
            Tuple of (is_safe, message)
        """
        # Basic size check
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > 50:
            return False, f"File too large ({file_size_mb:.2f}MB)"
        
        # Check magic bytes for valid PDF
        if filename.lower().endswith('.pdf'):
            if not file_content.startswith(b'%PDF'):
                return False, "Invalid PDF file"
        
        # Basic content scan
        scan_result = await self.scan_file(file_content, filename)
        
        if not scan_result.clean:
            threat_descriptions = [
                t.get("description", t.get("type", "Unknown threat"))
                for t in scan_result.threats_found
            ]
            return False, f"Security issue detected: {'; '.join(threat_descriptions)}"
        
        return True, "File passed security scan"
    
    def get_scanner_info(self) -> Dict[str, Any]:
        """
        Get information about the scanner configuration.
        
        Returns:
            Scanner information dictionary
        """
        return {
            "scanner_name": self.scanner_name,
            "heuristic_threshold": self.heuristic_threshold,
            "allowed_file_types": list(self._allowed_types.keys()),
            "blocked_file_types": list(self._blocked_types.keys()),
            "patterns_monitored": len(self._suspicious_patterns),
            "clamav_available": False  # TODO: Check actual availability
        }


# Global scanner instance
virus_scanner = VirusScanner()
