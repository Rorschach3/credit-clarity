"""
Optimized Credit Report Processor with enhanced performance
Implements concurrent processing, memory management, and caching
"""
import asyncio
import os
import logging
import tempfile
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import lru_cache
import weakref
import psutil
import time

from core.config import get_settings
from services.pdf_chunker import PDFChunker

logger = logging.getLogger(__name__)
settings = get_settings()

# Import bureau detection function
def detect_credit_bureau(text_content: str) -> str:
    """
    Detect credit bureau from PDF text content.
    Searches for: Equifax, Experian, TransUnion
    Returns the first bureau found, or "Unknown" if none detected.
    """
    if not text_content:
        return "Unknown"
    
    # Convert to lowercase for case-insensitive matching
    text_lower = text_content.lower()
    
    # Credit bureau names to search for (in order of priority)
    bureaus = [
        ("equifax", "Equifax"),
        ("experian", "Experian"), 
        ("transunion", "TransUnion"),
        ("trans union", "TransUnion")  # Handle space variation
    ]
    
    # Search for each bureau name
    for search_term, bureau_name in bureaus:
        if search_term in text_lower:
            logger.info(f"🔍 Credit bureau detected: {bureau_name}")
            return bureau_name
    
    logger.info("🔍 No credit bureau detected, using 'Unknown'")
    return "Unknown"


class MemoryManager:
    """Manages memory usage and resource cleanup."""
    
    def __init__(self, max_memory_percent: float = 80.0):
        self.max_memory_percent = max_memory_percent
        self._temp_files = weakref.WeakSet()
    
    def check_memory_usage(self) -> bool:
        """Check if memory usage is within acceptable limits."""
        memory = psutil.virtual_memory()
        return memory.percent < self.max_memory_percent
    
    def register_temp_file(self, filepath: str):
        """Register a temporary file for cleanup."""
        self._temp_files.add(filepath)
    
    def cleanup_temp_files(self):
        """Clean up registered temporary files."""
        for filepath in list(self._temp_files):
            try:
                if os.path.exists(filepath):
                    os.unlink(filepath)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {filepath}: {e}")


class ProcessingCache:
    """Simple in-memory cache for processing results."""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired."""
        if key not in self.access_times:
            return True
        return datetime.now() - self.access_times[key] > timedelta(seconds=self.ttl_seconds)
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache if exists and not expired."""
        if key in self.cache and not self._is_expired(key):
            self.access_times[key] = datetime.now()  # Update access time
            return self.cache[key]
        
        # Remove expired item
        if key in self.cache:
            self.cache.pop(key, None)
            self.access_times.pop(key, None)
        
        return None
    
    def set(self, key: str, value: Any):
        """Set item in cache with cleanup if needed."""
        # Clean up expired entries
        self._cleanup_expired()
        
        # Remove oldest entries if at capacity
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            self.cache.pop(oldest_key, None)
            self.access_times.pop(oldest_key, None)
        
        self.cache[key] = value
        self.access_times[key] = datetime.now()
    
    def _cleanup_expired(self):
        """Remove expired entries."""
        expired_keys = [k for k in self.cache.keys() if self._is_expired(k)]
        for key in expired_keys:
            self.cache.pop(key, None)
            self.access_times.pop(key, None)


class OptimizedCreditReportProcessor:
    """
    High-performance credit report processor with:
    - Concurrent PDF extraction methods
    - Memory management and resource cleanup
    - Result caching
    - Background processing support
    - Performance monitoring
    """
    
    def __init__(self, deterministic_mode: bool = True):
        self.logger = logging.getLogger(__name__)
        self.memory_manager = MemoryManager()
        self.cache = ProcessingCache()
        self.chunker = PDFChunker(chunk_size=20)  # 20 pages per chunk for better performance
        self.deterministic_mode = deterministic_mode  # NEW: Control for consistent results
        
        # Performance tracking
        self.processing_stats = {
            'total_processed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'average_processing_time': 0.0,
            'memory_warnings': 0
        }
        
        # Thread pools for different types of operations
        self.io_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="pdf-io")
        self.cpu_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="pdf-cpu")
        
        # Only use ProcessPoolExecutor for CPU-intensive tasks if available
        try:
            self.process_executor = ProcessPoolExecutor(max_workers=2)
        except Exception as e:
            logger.warning(f"ProcessPoolExecutor not available: {e}")
            self.process_executor = None
        
        # Log deterministic mode setting
        mode_status = "ENABLED" if self.deterministic_mode else "DISABLED"
        logger.info(f"🎯 OptimizedCreditReportProcessor initialized with deterministic mode: {mode_status}")
    
    def _generate_cache_key(self, pdf_path: str) -> str:
        """Generate cache key from PDF file."""
        try:
            # Use file hash for cache key
            with open(pdf_path, 'rb') as f:
                file_hash = hashlib.md5(f.read(1024)).hexdigest()  # Hash first 1KB for speed
                file_size = os.path.getsize(pdf_path)
                return f"pdf_{file_hash}_{file_size}"
        except Exception:
            # Fallback to filepath + mtime
            stat = os.stat(pdf_path)
            return f"pdf_{abs(hash(pdf_path))}_{int(stat.st_mtime)}_{stat.st_size}"
    
    def _should_chunk_pdf(self, pdf_path: str) -> bool:
        """Determine if PDF should be chunked based on size and page count."""
        try:
            file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
            
            # Always chunk files larger than 3MB or estimate >30 pages
            if file_size_mb > 3:
                return True
                
            # Try to get page count quickly
            try:
                import PyPDF2
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    page_count = len(reader.pages)
                    if page_count > 30:
                        logger.info(f"PDF has {page_count} pages, will use chunking")
                        return True
            except Exception:
                # If we can't determine page count, chunk large files anyway
                return file_size_mb > 2
                
            return False
        except Exception as e:
            logger.warning(f"Could not determine if PDF needs chunking: {e}")
            return False

    async def process_credit_report_optimized(self, pdf_path: str) -> Dict[str, Any]:
        """
        Optimized processing pipeline with caching and performance monitoring.
        """
        start_time = time.time()
        self.processing_stats['total_processed'] += 1
        
        # Check memory before processing
        if not self.memory_manager.check_memory_usage():
            self.processing_stats['memory_warnings'] += 1
            logger.warning("Memory usage high, forcing garbage collection")
            import gc
            gc.collect()
        
        # Check cache first
        cache_key = self._generate_cache_key(pdf_path)
        cached_result = self.cache.get(cache_key)
        
        if cached_result:
            self.processing_stats['cache_hits'] += 1
            logger.info(f"📋 Cache hit for {os.path.basename(pdf_path)}")
            
            # Update processing time in cached result
            cached_result['processing_time'] = time.time() - start_time
            cached_result['cache_hit'] = True
            return cached_result
        
        self.processing_stats['cache_misses'] += 1
        logger.info(f"🔄 Cache miss for {os.path.basename(pdf_path)}, processing...")
        
        try:
            # Check if we need to chunk this PDF
            if self._should_chunk_pdf(pdf_path):
                logger.info("📄 Processing large PDF with chunking")
                return await self._process_with_chunking(pdf_path, start_time)
            
            # Phase 1: Concurrent extraction methods
            extraction_result = await self._concurrent_extraction(pdf_path)
            
            if extraction_result['success']:
                # Phase 2: Concurrent parsing
                tradelines = await self._concurrent_parsing(
                    extraction_result['text'], 
                    extraction_result['tables']
                )
                
                processing_time = time.time() - start_time
                
                result = {
                    'success': True,
                    'tradelines': tradelines,
                    'method_used': extraction_result['method'],
                    'processing_time': processing_time,
                    'cost_estimate': 0.0,  # Free methods
                    'cache_hit': False,
                    'stats': {
                        'text_length': len(extraction_result['text']),
                        'tables_found': len(extraction_result['tables']),
                        'tradelines_extracted': len(tradelines)
                    }
                }
                
                # Cache the result
                self.cache.set(cache_key, result.copy())
                
                # Update average processing time
                self._update_avg_processing_time(processing_time)
                
                return result
            
            else:
                # Fallback to expensive methods if needed
                return await self._expensive_fallback(pdf_path, start_time)
                
        except Exception as e:
            logger.error(f"❌ Optimized processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    async def _process_with_chunking(self, pdf_path: str, start_time: float) -> Dict[str, Any]:
        """Process large PDF files using chunking strategy."""
        try:
            # Read the original file content
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            # Create a temporary directory for chunks
            chunk_dir = tempfile.mkdtemp(prefix="pdf_chunks_")
            logger.info(f"📁 Created chunk directory: {chunk_dir}")
            
            try:
                # Chunk the PDF
                chunk_paths = self.chunker.chunk_pdf(
                    pdf_content, 
                    chunk_dir, 
                    f"chunk_{os.path.basename(pdf_path).replace('.pdf', '')}"
                )
                
                logger.info(f"📄 Split PDF into {len(chunk_paths)} chunks")
                
                # Process each chunk concurrently
                chunk_tasks = []
                for i, chunk_path in enumerate(chunk_paths):
                    task = asyncio.create_task(
                        self._process_single_chunk(chunk_path, i),
                        name=f"chunk_{i}"
                    )
                    chunk_tasks.append(task)
                
                # Wait for all chunks to complete with longer timeout
                chunk_results = await asyncio.gather(*chunk_tasks, return_exceptions=True)
                
                # Combine results from all chunks
                all_tradelines = []
                total_cost = 0.0
                methods_used = []
                
                for i, result in enumerate(chunk_results):
                    if isinstance(result, Exception):
                        logger.warning(f"⚠️ Chunk {i} failed: {result}")
                        continue
                    
                    if isinstance(result, dict) and result.get('success'):
                        chunk_tradelines = result.get('tradelines', [])
                        all_tradelines.extend(chunk_tradelines)
                        total_cost += result.get('cost_estimate', 0.0)
                        methods_used.append(result.get('method_used', 'unknown'))
                        logger.info(f"✅ Chunk {i}: extracted {len(chunk_tradelines)} tradelines")
                    else:
                        logger.warning(f"⚠️ Chunk {i} returned no results")
                
                # Deduplicate tradelines across chunks
                unique_tradelines = self._deduplicate_tradelines(all_tradelines)
                
                processing_time = time.time() - start_time
                
                result = {
                    'success': True,
                    'tradelines': unique_tradelines,
                    'method_used': f"chunked_{','.join(set(methods_used))}",
                    'processing_time': processing_time,
                    'cost_estimate': total_cost,
                    'cache_hit': False,
                    'stats': {
                        'chunks_processed': len(chunk_paths),
                        'successful_chunks': sum(1 for r in chunk_results if isinstance(r, dict) and r.get('success')),
                        'total_tradelines_before_dedup': len(all_tradelines),
                        'tradelines_after_dedup': len(unique_tradelines)
                    }
                }
                
                logger.info(f"🎉 Chunked processing complete: {len(unique_tradelines)} tradelines from {len(chunk_paths)} chunks")
                
                # Cache the result
                cache_key = self._generate_cache_key(pdf_path)
                self.cache.set(cache_key, result.copy())
                
                return result
                
            finally:
                # Cleanup chunk directory
                try:
                    import shutil
                    shutil.rmtree(chunk_dir, ignore_errors=True)
                    logger.debug(f"🗑️ Cleaned up chunk directory: {chunk_dir}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to cleanup chunk directory: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Chunked processing failed: {e}")
            return {
                'success': False,
                'error': f"Chunked processing failed: {str(e)}",
                'processing_time': time.time() - start_time
            }
    
    async def _process_single_chunk(self, chunk_path: str, chunk_index: int) -> Dict[str, Any]:
        """Process a single PDF chunk."""
        try:
            logger.debug(f"🔄 Processing chunk {chunk_index}: {os.path.basename(chunk_path)}")
            
            # Process this chunk using the regular extraction pipeline
            extraction_result = await self._concurrent_extraction(chunk_path)
            
            if extraction_result['success']:
                # Parse the extracted content
                tradelines = await self._concurrent_parsing(
                    extraction_result['text'], 
                    extraction_result['tables']
                )
                
                return {
                    'success': True,
                    'tradelines': tradelines,
                    'method_used': extraction_result['method'],
                    'cost_estimate': 0.0,  # Free methods for chunks
                    'chunk_index': chunk_index
                }
            else:
                return {
                    'success': False,
                    'error': extraction_result.get('error', 'Extraction failed'),
                    'chunk_index': chunk_index
                }
                
        except Exception as e:
            logger.error(f"❌ Chunk {chunk_index} processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'chunk_index': chunk_index
            }
    
    async def _concurrent_extraction(self, pdf_path: str) -> Dict[str, Any]:
        """
        Run multiple PDF extraction methods concurrently with smart timeouts.
        """
        file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
        
        # Adjust timeout based on file size - more generous for large files
        base_timeout = 60  # 60 seconds base timeout
        timeout_per_mb = 10  # 10 seconds per MB
        max_timeout = 600  # Maximum 10 minutes for very large files
        
        timeout = min(max_timeout, base_timeout + (file_size_mb * timeout_per_mb))
        
        logger.info(f"Processing {file_size_mb:.2f}MB file with {timeout}s timeout")
        
        # Create tasks for different extraction methods
        tasks = []
        
        # Always try pdfplumber (fast and reliable)
        tasks.append(asyncio.create_task(
            self._extract_with_pdfplumber_async(pdf_path),
            name="pdfplumber"
        ))
        
        # Try PyMuPDF for complex layouts
        tasks.append(asyncio.create_task(
            self._extract_with_pymupdf_async(pdf_path),
            name="pymupdf"  
        ))
        
        # Only try OCR for smaller files
        if file_size_mb < 10:
            tasks.append(asyncio.create_task(
                self._extract_with_ocr_async(pdf_path),
                name="ocr"
            ))
        
        try:
            # Use asyncio.wait with timeout and return when first succeeds
            done, pending = await asyncio.wait(
                tasks,
                timeout=timeout,
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel pending tasks to save resources
            for task in pending:
                task.cancel()
            
            # Get the first successful result
            for task in done:
                try:
                    result = await task
                    if result.get('success'):
                        logger.info(f"✅ {task.get_name()} extraction succeeded")
                        return result
                except Exception as e:
                    logger.warning(f"Task {task.get_name()} failed: {e}")
            
            # If no successful results, wait for all and return best effort
            remaining_results = []
            for task in pending:
                try:
                    result = await asyncio.wait_for(task, timeout=10)
                    remaining_results.append(result)
                except Exception:
                    pass
            
            # Return the result with the most text
            all_results = [await task for task in done if not task.cancelled()] + remaining_results
            valid_results = [r for r in all_results if r.get('success')]
            
            if valid_results:
                best_result = max(valid_results, key=lambda r: len(r.get('text', '')))
                return best_result
            
            return {'success': False, 'text': '', 'tables': [], 'method': 'all_failed'}
            
        except asyncio.TimeoutError:
            # Cancel all tasks on timeout
            for task in tasks:
                task.cancel()
            
            logger.warning(f"All extraction methods timed out after {timeout}s")
            return {'success': False, 'text': '', 'tables': [], 'method': 'timeout'}
    
    async def _extract_with_pdfplumber_async(self, pdf_path: str) -> Dict[str, Any]:
        """Async wrapper for pdfplumber with optimizations."""
        loop = asyncio.get_running_loop()
        
        def _sync_extract():
            try:
                import pdfplumber
                
                text_content = ""
                tables = []
                
                # Process in chunks to manage memory
                with pdfplumber.open(pdf_path) as pdf:
                    total_pages = len(pdf.pages)
                    
                    # For large PDFs, process in smaller chunks
                    chunk_size = 10 if total_pages > 50 else total_pages
                    
                    for i in range(0, total_pages, chunk_size):
                        chunk_end = min(i + chunk_size, total_pages)
                        
                        for page_num in range(i, chunk_end):
                            page = pdf.pages[page_num]
                            page_text = page.extract_text() or ""
                            text_content += f"\n--- Page {page_num + 1} ---\n{page_text}"
                            
                            # Extract tables but limit processing time
                            try:
                                page_tables = page.extract_tables()
                                if page_tables:
                                    for table in page_tables[:3]:  # Limit to 3 tables per page
                                        if table and len(table) > 0:
                                            tables.append({
                                                'headers': table[0] if table else [],
                                                'rows': table[1:] if len(table) > 1 else [],
                                                'page': page_num + 1
                                            })
                            except Exception as e:
                                logger.debug(f"Table extraction failed for page {page_num + 1}: {e}")
                        
                        # Allow other tasks to run
                        if chunk_end < total_pages:
                            time.sleep(0.01)  # Small yield
                
                if self._validate_extraction_quality(text_content):
                    return {
                        'success': True,
                        'text': text_content,
                        'tables': tables,
                        'method': 'pdfplumber_optimized'
                    }
                
            except ImportError:
                logger.debug("pdfplumber not available")
            except Exception as e:
                logger.debug(f"pdfplumber failed: {e}")
            
            return {'success': False}
        
        return await loop.run_in_executor(self.io_executor, _sync_extract)
    
    async def _extract_with_pymupdf_async(self, pdf_path: str) -> Dict[str, Any]:
        """Async wrapper for PyMuPDF with optimizations."""
        loop = asyncio.get_running_loop()
        
        def _sync_extract():
            try:
                import fitz  # PyMuPDF
                
                text_content = ""
                tables = []
                
                doc = fitz.open(pdf_path)
                
                # Process pages in parallel chunks
                total_pages = len(doc)
                for page_num in range(min(total_pages, 50)):  # Limit to first 50 pages for speed
                    page = doc[page_num]
                    page_text = page.get_text()
                    text_content += f"\n--- Page {page_num + 1} ---\n{page_text}"
                    
                    # Extract tables if available (but limit processing)
                    try:
                        page_tables = page.find_tables()
                        for table_idx, table in enumerate(page_tables[:2]):  # Max 2 tables per page
                            table_data = table.extract()
                            if table_data and len(table_data) > 0:
                                tables.append({
                                    'headers': table_data[0] if table_data else [],
                                    'rows': table_data[1:] if len(table_data) > 1 else [],
                                    'page': page_num + 1
                                })
                    except Exception:
                        pass  # Table extraction is optional
                
                doc.close()
                
                if self._validate_extraction_quality(text_content):
                    return {
                        'success': True,
                        'text': text_content,
                        'tables': tables,
                        'method': 'pymupdf_optimized'
                    }
                
            except ImportError:
                logger.debug("PyMuPDF not available")
            except Exception as e:
                logger.debug(f"PyMuPDF failed: {e}")
            
            return {'success': False}
        
        return await loop.run_in_executor(self.io_executor, _sync_extract)
    
    async def _extract_with_ocr_async(self, pdf_path: str) -> Dict[str, Any]:
        """Async wrapper for OCR extraction with resource limits."""
        loop = asyncio.get_running_loop()
        
        def _sync_extract():
            try:
                import shutil
                
                # Check if tesseract is available
                if not shutil.which('tesseract'):
                    return {'success': False}
                
                import fitz
                import pytesseract
                from PIL import Image
                import io
                
                text_content = ""
                
                doc = fitz.open(pdf_path)
                # Limit OCR to first 3 pages for performance
                for page_num in range(min(len(doc), 3)):
                    page = doc[page_num]
                    
                    # Convert to image with lower resolution for speed
                    pix = page.get_pixmap(matrix=fitz.Matrix(1.2, 1.2))  # Reduced scale
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    
                    # OCR with timeout
                    try:
                        page_text = pytesseract.image_to_string(
                            img, 
                            config='--psm 6 --oem 3',  # Optimized config
                            timeout=15  # 15 second timeout per page
                        )
                        text_content += f"\n--- Page {page_num + 1} (OCR) ---\n{page_text}"
                    except Exception:
                        continue
                
                doc.close()
                
                if self._validate_extraction_quality(text_content):
                    return {
                        'success': True,
                        'text': text_content,
                        'tables': [],
                        'method': 'ocr_optimized'
                    }
                
            except Exception as e:
                logger.debug(f"OCR failed: {e}")
            
            return {'success': False}
        
        return await loop.run_in_executor(self.cpu_executor, _sync_extract)
    
    async def _concurrent_parsing(self, text: str, tables: List[Dict]) -> List[Dict]:
        """Parse text and tables concurrently."""
        tasks = []
        
        # Detect credit bureau from text
        credit_bureau = detect_credit_bureau(text)
        logger.info(f"🏛️ Credit bureau detected for tradelines: {credit_bureau}")
        
        # Parse tables in parallel
        if tables:
            table_task = asyncio.create_task(
                self._parse_tables_async(tables)
            )
            tasks.append(table_task)
        
        # Parse text with Gemini
        if text.strip():
            text_task = asyncio.create_task(
                self._parse_text_with_gemini_async(text)
            )
            tasks.append(text_task)
        
        # Wait for all parsing tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        all_tradelines = []
        for result in results:
            if isinstance(result, list):
                all_tradelines.extend(result)
        
        # Assign credit bureau to all tradelines
        for tradeline in all_tradelines:
            if isinstance(tradeline, dict):
                tradeline["credit_bureau"] = credit_bureau
        
        # Deduplicate tradelines
        return self._deduplicate_tradelines(all_tradelines)
    
    async def _parse_tables_async(self, tables: List[Dict]) -> List[Dict]:
        """Parse tables asynchronously."""
        loop = asyncio.get_running_loop()
        
        def _sync_parse():
            tradelines = []
            for table in tables:
                table_tradelines = self._extract_tradelines_from_table(table)
                tradelines.extend(table_tradelines)
            return tradelines
        
        return await loop.run_in_executor(self.cpu_executor, _sync_parse)
    
    async def _parse_text_with_gemini_async(self, text: str) -> List[Dict]:
        """Parse text with Gemini asynchronously."""
        try:
            # Import locally to avoid import issues
            from main import GeminiProcessor
            
            processor = GeminiProcessor()
            
            # Run Gemini processing in thread pool to avoid blocking
            loop = asyncio.get_running_loop()
            tradelines = await loop.run_in_executor(
                self.cpu_executor,
                processor.extract_tradelines,
                text
            )
            
            return tradelines if isinstance(tradelines, list) else []
            
        except Exception as e:
            logger.warning(f"Gemini parsing failed: {e}")
            return []
    
    def _validate_extraction_quality(self, text: str) -> bool:
        """Validate if extracted text is good enough for processing."""
        if not text or len(text.strip()) < 100:
            return False
        
        # Check for credit report indicators
        text_lower = text.lower()
        credit_indicators = [
            'credit', 'account', 'balance', 'payment', 'tradeline',
            'experian', 'equifax', 'transunion', 'creditor', 'limit'
        ]
        
        found_indicators = sum(1 for indicator in credit_indicators if indicator in text_lower)
        return found_indicators >= 3
    
    def _extract_tradelines_from_table(self, table: Dict) -> List[Dict]:
        """Extract tradelines from table data with robust null handling."""
        try:
            headers = table.get("headers", [])
            rows = table.get("rows", [])
            
            if not headers or not rows:
                return []
            
            tradelines = []
            
            # Map common header variations to standard fields
            header_mapping = {
                "creditor": "creditor_name",
                "creditor_name": "creditor_name", 
                "lender": "creditor_name",
                "company": "creditor_name",
                "account": "account_number",
                "account_number": "account_number",
                "acct": "account_number",
                "balance": "account_balance",
                "current_balance": "account_balance",
                "amount_owed": "account_balance",
                "limit": "credit_limit",
                "credit_limit": "credit_limit",
                "high_credit": "credit_limit",
                "payment": "monthly_payment",
                "monthly_payment": "monthly_payment",
                "min_payment": "monthly_payment",
                "date_opened": "date_opened",
                "opened": "date_opened",
                "status": "account_status",
                "account_status": "account_status",
                "type": "account_type",
                "account_type": "account_type"
            }
            
            # Normalize headers with null checks
            normalized_headers = []
            for header in headers:
                if not header:  # Skip None or empty headers
                    normalized_headers.append("")
                    continue
                    
                header_lower = str(header).lower().strip()
                mapped_header = None
                for key, value in header_mapping.items():
                    if key in header_lower:
                        mapped_header = value
                        break
                normalized_headers.append(mapped_header or header_lower)
            
            # Process each row as a potential tradeline
            for row_idx, row in enumerate(rows):
                if not row or len(row) != len(normalized_headers):
                    continue
                
                tradeline = {
                    "creditor_name": "",
                    "account_number": "",
                    "account_balance": "",
                    "credit_limit": "",
                    "monthly_payment": "",
                    "date_opened": "",
                    "account_type": "Credit Card",
                    "account_status": "Open",
                    "credit_bureau": "",  # Will be assigned later in _concurrent_parsing
                    "is_negative": False,
                    "dispute_count": 0
                }
                
                # Map row data to tradeline fields with null safety
                for i, cell_value in enumerate(row):
                    if i < len(normalized_headers):
                        header = normalized_headers[i]
                        if header in tradeline and cell_value is not None:
                            cell_str = str(cell_value).strip()
                            if cell_str:  # Only add non-empty values
                                tradeline[header] = cell_str
                
                # Only add if we have essential fields
                if tradeline["creditor_name"] and tradeline["account_number"]:
                    tradelines.append(tradeline)
            
            logger.debug(f"Extracted {len(tradelines)} tradelines from table with {len(rows)} rows")
            return tradelines
            
        except Exception as e:
            logger.error(f"Failed to extract tradelines from table: {str(e)}")
            return []
    
    def _deduplicate_tradelines(self, tradelines: List[Dict]) -> List[Dict]:
        """Enhanced deduplication using creditor + clean account number + date + credit bureau."""
        import re
        
        if not tradelines:
            return []
        
        # Filter out tradelines without valid account numbers
        valid_tradelines = []
        invalid_count = 0
        
        for tradeline in tradelines:
            account_number_raw = tradeline.get('account_number', '') or ''
            account_number = str(account_number_raw).strip() if account_number_raw is not None else ''
            if account_number and account_number not in ['', 'N/A', 'Unknown', 'No account']:
                valid_tradelines.append(tradeline)
            else:
                invalid_count += 1
        
        if invalid_count > 0:
            logger.info(f"🚫 Filtered out {invalid_count} tradelines without valid account numbers")
        
        # Enhanced deduplication with proper key generation
        unique_tradelines = []
        seen_identifiers = set()
        
        for tradeline in valid_tradelines:
            # Extract and normalize components
            creditor_name_raw = tradeline.get('creditor_name', '') or ''
            creditor_name = str(creditor_name_raw).strip().upper() if creditor_name_raw is not None else ''
            
            raw_account_number_val = tradeline.get('account_number', '') or ''
            raw_account_number = str(raw_account_number_val).strip() if raw_account_number_val is not None else ''
            
            date_opened_raw = tradeline.get('date_opened', '') or ''
            date_opened = str(date_opened_raw).strip() if date_opened_raw is not None else ''
            
            credit_bureau_raw = tradeline.get('credit_bureau', '') or ''
            credit_bureau = str(credit_bureau_raw).strip().upper() if credit_bureau_raw is not None else ''
            
            # Clean account number by removing special characters and normalizing
            clean_account_number = re.sub(r'[*.\-\s]', '', raw_account_number).upper()
            
            # Create robust unique identifier that matches database constraint
            unique_identifier = f"{creditor_name}|{clean_account_number}|{date_opened}|{credit_bureau}"
            
            if unique_identifier not in seen_identifiers:
                seen_identifiers.add(unique_identifier)
                unique_tradelines.append(tradeline)
                logger.debug(f"✅ Added unique tradeline: {creditor_name} {raw_account_number}")
            else:
                logger.debug(f"🔄 Duplicate found, skipping: {creditor_name} {raw_account_number}")
        
        total_removed = len(valid_tradelines) - len(unique_tradelines)
        logger.info(f"🧹 Enhanced deduplication: removed {total_removed} duplicates from {len(valid_tradelines)} valid tradelines")
        
        return unique_tradelines
    
    def _update_avg_processing_time(self, processing_time: float):
        """Update average processing time with exponential moving average."""
        alpha = 0.1  # Smoothing factor
        if self.processing_stats['average_processing_time'] == 0:
            self.processing_stats['average_processing_time'] = processing_time
        else:
            self.processing_stats['average_processing_time'] = (
                alpha * processing_time + 
                (1 - alpha) * self.processing_stats['average_processing_time']
            )
    
    async def _expensive_fallback(self, pdf_path: str, start_time: float) -> Dict[str, Any]:
        """Fallback to Document AI when free methods fail."""
        # Implementation would go here
        return {
            'success': False,
            'error': 'Document AI fallback not implemented in optimized processor',
            'processing_time': time.time() - start_time
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        return self.processing_stats.copy()
    
    def cleanup(self):
        """Clean up resources."""
        self.memory_manager.cleanup_temp_files()
        
        # Shutdown executors
        if hasattr(self, 'io_executor'):
            self.io_executor.shutdown(wait=False)
        if hasattr(self, 'cpu_executor'):
            self.cpu_executor.shutdown(wait=False)
        if hasattr(self, 'process_executor') and self.process_executor:
            self.process_executor.shutdown(wait=False)
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except Exception:
            pass