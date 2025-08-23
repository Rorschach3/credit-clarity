"""
Safe PDF Processor - Non-freezing alternative to OptimizedCreditReportProcessor
"""
import asyncio
import os
import logging
import time
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class SafePDFProcessor:
    """
    Simplified, safe PDF processor that won't freeze.
    Uses conservative timeouts and simple processing.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    async def process_pdf_safe(self, pdf_path: str) -> Dict[str, Any]:
        """
        Safe PDF processing with strict timeouts and no hanging.
        """
        start_time = time.time()
        
        try:
            # Check file exists and is readable
            if not os.path.exists(pdf_path):
                return {
                    'success': False,
                    'error': 'File not found',
                    'processing_time': time.time() - start_time
                }
            
            file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
            logger.info(f"📄 Processing {os.path.basename(pdf_path)} ({file_size_mb:.2f}MB)")
            
            # Try methods in order of reliability, with strict timeouts
            extraction_methods = [
                ('pdfplumber', self._extract_with_pdfplumber_safe),
                ('pymupdf', self._extract_with_pymupdf_safe),
            ]
            
            for method_name, method_func in extraction_methods:
                try:
                    logger.info(f"🔄 Trying {method_name}")
                    
                    # Each method gets max 60 seconds
                    result = await asyncio.wait_for(
                        method_func(pdf_path),
                        timeout=60.0
                    )
                    
                    if result.get('success'):
                        result['processing_time'] = time.time() - start_time
                        result['method_used'] = method_name
                        logger.info(f"✅ {method_name} succeeded")
                        return result
                        
                except asyncio.TimeoutError:
                    logger.warning(f"⏰ {method_name} timed out")
                    continue
                except Exception as e:
                    logger.warning(f"❌ {method_name} failed: {e}")
                    continue
            
            # If all methods failed
            return {
                'success': False,
                'error': 'All extraction methods failed',
                'processing_time': time.time() - start_time,
                'tradelines': []
            }
            
        except Exception as e:
            logger.error(f"❌ Safe processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time,
                'tradelines': []
            }
    
    async def _extract_with_pdfplumber_safe(self, pdf_path: str) -> Dict[str, Any]:
        """Safe pdfplumber extraction with limits."""
        
        def extract_sync():
            try:
                import pdfplumber
                
                text_content = ""
                
                with pdfplumber.open(pdf_path) as pdf:
                    # Limit to first 10 pages to prevent hanging
                    max_pages = min(len(pdf.pages), 10)
                    
                    for i in range(max_pages):
                        page = pdf.pages[i]
                        page_text = page.extract_text() or ""
                        text_content += f"\n--- Page {i + 1} ---\n{page_text}"
                        
                        # Break if we have enough text
                        if len(text_content) > 50000:  # 50KB limit
                            break
                
                if len(text_content.strip()) > 100:
                    return {
                        'success': True,
                        'text': text_content,
                        'method': 'pdfplumber_safe'
                    }
                else:
                    return {'success': False, 'error': 'No text extracted'}
                    
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        # Run in thread with timeout
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, extract_sync)
    
    async def _extract_with_pymupdf_safe(self, pdf_path: str) -> Dict[str, Any]:
        """Safe PyMuPDF extraction with limits."""
        
        def extract_sync():
            try:
                import fitz
                
                text_content = ""
                
                doc = fitz.open(pdf_path)
                # Limit to first 10 pages
                max_pages = min(len(doc), 10)
                
                for i in range(max_pages):
                    page = doc[i]
                    page_text = page.get_text()
                    text_content += f"\n--- Page {i + 1} ---\n{page_text}"
                    
                    # Break if we have enough text
                    if len(text_content) > 50000:  # 50KB limit
                        break
                
                doc.close()
                
                if len(text_content.strip()) > 100:
                    return {
                        'success': True,
                        'text': text_content,
                        'method': 'pymupdf_safe'
                    }
                else:
                    return {'success': False, 'error': 'No text extracted'}
                    
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        # Run in thread with timeout
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, extract_sync)
    
    async def parse_tradelines_simple(self, text: str) -> List[Dict]:
        """Simple tradeline parsing without complex AI."""
        try:
            from services.optimized_processor import detect_credit_bureau
            
            tradelines = []
            lines = text.split('\n')
            
            # Look for lines that might contain tradeline information
            for line in lines:
                line = line.strip()
                if len(line) < 20:  # Skip short lines
                    continue
                
                # Simple patterns for credit information
                if any(keyword in line.lower() for keyword in ['account', 'credit', 'balance', 'limit']):
                    # Extract basic info with regex
                    import re
                    
                    # Look for account numbers
                    account_matches = re.findall(r'\b\d{4,16}\b', line)
                    # Look for dollar amounts
                    amount_matches = re.findall(r'\$[\d,]+', line)
                    
                    if account_matches and len(line) > 30:
                        tradeline = {
                            "creditor_name": line[:40].strip(),
                            "account_number": account_matches[0] if account_matches else "",
                            "account_balance": amount_matches[0] if amount_matches else "",
                            "credit_limit": amount_matches[1] if len(amount_matches) > 1 else "",
                            "monthly_payment": "",
                            "date_opened": "",
                            "account_type": "Credit Card",
                            "account_status": "Open",
                            "credit_bureau": detect_credit_bureau(text),
                            "is_negative": False,
                            "dispute_count": 0
                        }
                        tradelines.append(tradeline)
                        
                        # Limit to 20 tradelines to prevent issues
                        if len(tradelines) >= 20:
                            break
            
            logger.info(f"📊 Simple parsing found {len(tradelines)} tradelines")
            return tradelines
            
        except Exception as e:
            logger.error(f"❌ Simple parsing failed: {e}")
            return []

# Create global instance
safe_processor = SafePDFProcessor()

async def process_pdf_safely(pdf_path: str) -> Dict[str, Any]:
    """
    Main entry point for safe PDF processing.
    Use this instead of OptimizedCreditReportProcessor when experiencing freezing.
    """
    result = await safe_processor.process_pdf_safe(pdf_path)
    
    if result.get('success') and result.get('text'):
        # Parse tradelines from text
        tradelines = await safe_processor.parse_tradelines_simple(result['text'])
        result['tradelines'] = tradelines
        result['stats'] = {
            'text_length': len(result.get('text', '')),
            'tradelines_extracted': len(tradelines)
        }
    
    return result

if __name__ == "__main__":
    import sys
    
    async def test_safe_processor():
        if len(sys.argv) < 2:
            print("Usage: python safe_pdf_processor.py <pdf_path>")
            return
        
        pdf_path = sys.argv[1]
        result = await process_pdf_safely(pdf_path)
        
        print(f"Result: {result.get('success')}")
        print(f"Method: {result.get('method_used')}")
        print(f"Processing time: {result.get('processing_time', 0):.2f}s")
        print(f"Tradelines found: {len(result.get('tradelines', []))}")
        
        if result.get('error'):
            print(f"Error: {result['error']}")
    
    asyncio.run(test_safe_processor())