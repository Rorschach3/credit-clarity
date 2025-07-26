import logging
import tempfile
import os
from typing import List, Tuple, Dict, Any
from pathlib import Path
import io

try:
    import pikepdf
    PIKEPDF_AVAILABLE = True
except ImportError:
    PIKEPDF_AVAILABLE = False

try:
    from PyPDF2 import PdfReader, PdfWriter
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

logger = logging.getLogger(__name__)

class PDFChunkingService:
    """Service for splitting PDFs into smaller chunks for processing"""
    
    def __init__(self, max_pages_per_chunk: int = 30):
        self.max_pages_per_chunk = max_pages_per_chunk
        self.preferred_library = self._determine_best_library()
        
    def _determine_best_library(self) -> str:
        """Determine the best available PDF library"""
        if PIKEPDF_AVAILABLE:
            logger.info("Using pikepdf for PDF chunking (recommended)")
            return "pikepdf"
        elif PYPDF2_AVAILABLE:
            logger.info("Using PyPDF2 for PDF chunking")
            return "pypdf2"
        else:
            raise ImportError("No suitable PDF library available (pikepdf or PyPDF2 required)")
    
    async def split_pdf(self, pdf_content: bytes, filename: str = "document.pdf") -> List[Dict[str, Any]]:
        """
        Split PDF into chunks of ≤max_pages_per_chunk pages
        
        Args:
            pdf_content: PDF file bytes
            filename: Original filename for logging
            
        Returns:
            List of chunk dictionaries with chunk_data, page_range, and metadata
        """
        try:
            logger.info(f"Starting PDF chunking for {filename}")
            
            # Get total page count first
            total_pages = self._get_page_count(pdf_content)
            logger.info(f"PDF has {total_pages} pages, splitting into chunks of ≤{self.max_pages_per_chunk} pages")
            
            if total_pages <= self.max_pages_per_chunk:
                # No need to split
                return [{
                    "chunk_id": 0,
                    "chunk_data": pdf_content,
                    "page_range": {"start": 1, "end": total_pages},
                    "total_pages": total_pages,
                    "is_single_chunk": True,
                    "original_filename": filename
                }]
            
            # Split into chunks
            if self.preferred_library == "pikepdf":
                chunks = await self._split_with_pikepdf(pdf_content, filename, total_pages)
            else:
                chunks = await self._split_with_pypdf2(pdf_content, filename, total_pages)
                
            logger.info(f"Successfully split {filename} into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error splitting PDF {filename}: {str(e)}")
            # Return original PDF as single chunk on error
            return [{
                "chunk_id": 0,
                "chunk_data": pdf_content,
                "page_range": {"start": 1, "end": self._get_page_count(pdf_content)},
                "total_pages": self._get_page_count(pdf_content),
                "is_single_chunk": True,
                "original_filename": filename,
                "error": str(e)
            }]
    
    def _get_page_count(self, pdf_content: bytes) -> int:
        """Get total number of pages in PDF"""
        try:
            if self.preferred_library == "pikepdf" and PIKEPDF_AVAILABLE:
                with pikepdf.open(io.BytesIO(pdf_content)) as pdf:
                    return len(pdf.pages)
            else:
                reader = PdfReader(io.BytesIO(pdf_content))
                return len(reader.pages)
        except Exception as e:
            logger.error(f"Error getting page count: {str(e)}")
            return 1  # Default to 1 page on error
    
    async def _split_with_pikepdf(self, pdf_content: bytes, filename: str, total_pages: int) -> List[Dict[str, Any]]:
        """Split PDF using pikepdf (preferred method)"""
        chunks = []
        
        with pikepdf.open(io.BytesIO(pdf_content)) as source_pdf:
            chunk_id = 0
            
            for start_page in range(0, total_pages, self.max_pages_per_chunk):
                end_page = min(start_page + self.max_pages_per_chunk - 1, total_pages - 1)
                
                # Create new PDF for this chunk
                chunk_pdf = pikepdf.new()
                
                # Copy pages to chunk
                for page_num in range(start_page, end_page + 1):
                    chunk_pdf.pages.append(source_pdf.pages[page_num])
                
                # Convert to bytes
                chunk_buffer = io.BytesIO()
                chunk_pdf.save(chunk_buffer)
                chunk_data = chunk_buffer.getvalue()
                chunk_buffer.close()
                
                chunks.append({
                    "chunk_id": chunk_id,
                    "chunk_data": chunk_data,
                    "page_range": {"start": start_page + 1, "end": end_page + 1},
                    "total_pages": end_page - start_page + 1,
                    "is_single_chunk": False,
                    "original_filename": filename,
                    "library_used": "pikepdf"
                })
                
                chunk_id += 1
                logger.debug(f"Created chunk {chunk_id} with pages {start_page + 1}-{end_page + 1}")
        
        return chunks
    
    async def _split_with_pypdf2(self, pdf_content: bytes, filename: str, total_pages: int) -> List[Dict[str, Any]]:
        """Split PDF using PyPDF2 (fallback method)"""
        chunks = []
        
        reader = PdfReader(io.BytesIO(pdf_content))
        chunk_id = 0
        
        for start_page in range(0, total_pages, self.max_pages_per_chunk):
            end_page = min(start_page + self.max_pages_per_chunk - 1, total_pages - 1)
            
            # Create new PDF writer for this chunk
            writer = PdfWriter()
            
            # Add pages to chunk
            for page_num in range(start_page, end_page + 1):
                writer.add_page(reader.pages[page_num])
            
            # Convert to bytes
            chunk_buffer = io.BytesIO()
            writer.write(chunk_buffer)
            chunk_data = chunk_buffer.getvalue()
            chunk_buffer.close()
            
            chunks.append({
                "chunk_id": chunk_id,
                "chunk_data": chunk_data,
                "page_range": {"start": start_page + 1, "end": end_page + 1},
                "total_pages": end_page - start_page + 1,
                "is_single_chunk": False,
                "original_filename": filename,
                "library_used": "pypdf2"
            })
            
            chunk_id += 1
            logger.debug(f"Created chunk {chunk_id} with pages {start_page + 1}-{end_page + 1}")
        
        return chunks
    
    async def combine_chunk_results(self, chunk_results: List[Dict[str, Any]], 
                                  original_filename: str) -> Dict[str, Any]:
        """
        Combine results from multiple chunks into a single result
        
        Args:
            chunk_results: List of Document AI results from each chunk
            original_filename: Original PDF filename
            
        Returns:
            Combined Document AI result
        """
        try:
            if not chunk_results:
                raise ValueError("No chunk results to combine")
            
            if len(chunk_results) == 1:
                # Single chunk, return as-is but update metadata
                result = chunk_results[0].copy()
                result['is_combined_result'] = False
                result['total_chunks'] = 1
                return result
            
            logger.info(f"Combining results from {len(chunk_results)} chunks for {original_filename}")
            
            # Initialize combined result
            combined_result = {
                'job_id': chunk_results[0].get('job_id'),
                'document_type': chunk_results[0].get('document_type'),
                'raw_text': '',
                'tables': [],
                'text_blocks': [],
                'confidence_score': 0.0,
                'total_pages': 0,
                'processing_time': 0.0,
                'metadata': {
                    'original_filename': original_filename,
                    'is_combined_result': True,
                    'total_chunks': len(chunk_results),
                    'chunk_info': []
                }
            }
            
            # Combine data from all chunks
            total_confidence = 0.0
            page_offset = 0
            
            for i, chunk_result in enumerate(chunk_results):
                # Combine raw text
                combined_result['raw_text'] += chunk_result.get('raw_text', '') + '\n\n'
                
                # Combine tables with page number adjustments
                chunk_tables = chunk_result.get('tables', [])
                for table in chunk_tables:
                    adjusted_table = table.copy()
                    if 'page_number' in adjusted_table:
                        adjusted_table['page_number'] += page_offset
                    adjusted_table['source_chunk'] = i
                    combined_result['tables'].append(adjusted_table)
                
                # Combine text blocks with page number adjustments
                chunk_text_blocks = chunk_result.get('text_blocks', [])
                for block in chunk_text_blocks:
                    adjusted_block = block.copy()
                    if 'page_number' in adjusted_block:
                        adjusted_block['page_number'] += page_offset
                    adjusted_block['source_chunk'] = i
                    combined_result['text_blocks'].append(adjusted_block)
                
                # Accumulate metrics
                combined_result['total_pages'] += chunk_result.get('total_pages', 0)
                combined_result['processing_time'] += chunk_result.get('processing_time', 0.0)
                total_confidence += chunk_result.get('confidence_score', 0.0)
                
                # Track chunk info
                combined_result['metadata']['chunk_info'].append({
                    'chunk_id': i,
                    'pages': chunk_result.get('total_pages', 0),
                    'tables_found': len(chunk_tables),
                    'text_blocks_found': len(chunk_text_blocks),
                    'confidence': chunk_result.get('confidence_score', 0.0)
                })
                
                page_offset += chunk_result.get('total_pages', 0)
            
            # Calculate average confidence
            combined_result['confidence_score'] = total_confidence / len(chunk_results) if chunk_results else 0.0
            
            # Clean up raw text
            combined_result['raw_text'] = combined_result['raw_text'].strip()
            
            logger.info(f"Combined results: {len(combined_result['tables'])} tables, "
                       f"{len(combined_result['text_blocks'])} text blocks, "
                       f"{combined_result['total_pages']} total pages")
            
            return combined_result
            
        except Exception as e:
            logger.error(f"Error combining chunk results: {str(e)}")
            raise
    
    def get_chunking_info(self, pdf_content: bytes) -> Dict[str, Any]:
        """Get information about how a PDF would be chunked"""
        try:
            total_pages = self._get_page_count(pdf_content)
            chunks_needed = (total_pages + self.max_pages_per_chunk - 1) // self.max_pages_per_chunk
            
            chunk_info = []
            for i in range(chunks_needed):
                start_page = i * self.max_pages_per_chunk + 1
                end_page = min((i + 1) * self.max_pages_per_chunk, total_pages)
                chunk_info.append({
                    "chunk_id": i,
                    "page_range": {"start": start_page, "end": end_page},
                    "pages_in_chunk": end_page - start_page + 1
                })
            
            return {
                "total_pages": total_pages,
                "max_pages_per_chunk": self.max_pages_per_chunk,
                "chunks_needed": chunks_needed,
                "chunk_info": chunk_info,
                "library_used": self.preferred_library
            }
            
        except Exception as e:
            logger.error(f"Error getting chunking info: {str(e)}")
            return {"error": str(e)}