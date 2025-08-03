import os
import tempfile
import logging
from typing import List, Optional, Tuple
from PyPDF2 import PdfReader, PdfWriter

logger = logging.getLogger(__name__)

CHUNK_SIZE = 30  # Max pages allowed by Document AI


class PDFChunker:
    """Service for chunking large PDF documents for Document AI processing"""
    
    def __init__(self, chunk_size: int = CHUNK_SIZE):
        self.chunk_size = chunk_size
        
    def chunk_pdf(self, file_content: bytes, chunk_dir: str, 
                  file_name: str = "document") -> List[str]:
        """
        Split a PDF into smaller chunks for Document AI processing
        
        Args:
            file_content: PDF file content as bytes
            chunk_dir: Directory to store chunks
            file_name: Base name for chunk files
            
        Returns:
            List of paths to chunk files
        """
        try:
            # Create temporary file from bytes
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                reader = PdfReader(temp_file_path)
                total_pages = len(reader.pages)
                
                logger.info(f"PDF has {total_pages} pages, chunking into {self.chunk_size}-page segments")
                
                # If PDF is within limit, return original
                if total_pages <= self.chunk_size:
                    logger.info("PDF is within page limit, no chunking needed")
                    return [temp_file_path]
                
                chunk_paths = []
                os.makedirs(chunk_dir, exist_ok=True)
                
                for i in range(0, total_pages, self.chunk_size):
                    writer = PdfWriter()
                    end_page = min(i + self.chunk_size, total_pages)
                    
                    # Add pages to chunk
                    for j in range(i, end_page):
                        writer.add_page(reader.pages[j])
                    
                    # Save chunk
                    chunk_num = i // self.chunk_size + 1
                    chunk_path = os.path.join(chunk_dir, f"{file_name}_chunk_{chunk_num}.pdf")
                    
                    with open(chunk_path, "wb") as chunk_file:
                        writer.write(chunk_file)
                    
                    chunk_paths.append(chunk_path)
                    logger.info(f"Created chunk {chunk_num}: {chunk_path} [pages {i+1}-{end_page}]")
                
                return chunk_paths
                
            finally:
                # Clean up original temp file
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Failed to chunk PDF: {str(e)}")
            raise
    
    def get_pdf_page_count(self, file_content: bytes) -> int:
        """Get the total number of pages in a PDF"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                reader = PdfReader(temp_file_path)
                return len(reader.pages)
            finally:
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
        except Exception as e:
            logger.error(f"Failed to get PDF page count: {str(e)}")
            return 0
    
    def needs_chunking(self, file_content: bytes) -> bool:
        """Check if a PDF needs to be chunked"""
        page_count = self.get_pdf_page_count(file_content)
        return page_count > self.chunk_size
    
    @staticmethod
    def cleanup_chunks(chunk_paths: List[str]) -> None:
        """Clean up temporary chunk files"""
        for chunk_path in chunk_paths:
            try:
                if os.path.exists(chunk_path):
                    os.unlink(chunk_path)
                    logger.debug(f"Cleaned up chunk: {chunk_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup chunk {chunk_path}: {str(e)}")