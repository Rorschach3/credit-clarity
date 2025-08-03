import os
import tempfile
import pytest
from unittest.mock import Mock, patch
from backend.services.pdf_chunker import PDFChunker


class TestPDFChunker:
    """Test cases for PDF chunking functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.chunker = PDFChunker(chunk_size=30)
    
    def test_chunk_size_initialization(self):
        """Test chunk size initialization"""
        assert self.chunker.chunk_size == 30
        
        custom_chunker = PDFChunker(chunk_size=20)
        assert custom_chunker.chunk_size == 20
    
    @patch('backend.services.pdf_chunker.PdfReader')
    def test_needs_chunking_large_pdf(self, mock_pdf_reader):
        """Test needs_chunking returns True for large PDFs"""
        # Mock a PDF with 50 pages
        mock_reader = Mock()
        mock_reader.pages = [Mock()] * 50
        mock_pdf_reader.return_value = mock_reader
        
        result = self.chunker.needs_chunking(b'fake_pdf_content')
        assert result is True
    
    @patch('backend.services.pdf_chunker.PdfReader')
    def test_needs_chunking_small_pdf(self, mock_pdf_reader):
        """Test needs_chunking returns False for small PDFs"""
        # Mock a PDF with 20 pages
        mock_reader = Mock()
        mock_reader.pages = [Mock()] * 20
        mock_pdf_reader.return_value = mock_reader
        
        result = self.chunker.needs_chunking(b'fake_pdf_content')
        assert result is False
    
    @patch('backend.services.pdf_chunker.PdfReader')
    def test_get_pdf_page_count(self, mock_pdf_reader):
        """Test PDF page count detection"""
        # Mock a PDF with 35 pages
        mock_reader = Mock()
        mock_reader.pages = [Mock()] * 35
        mock_pdf_reader.return_value = mock_reader
        
        page_count = self.chunker.get_pdf_page_count(b'fake_pdf_content')
        assert page_count == 35
    
    @patch('backend.services.pdf_chunker.PdfReader')
    @patch('backend.services.pdf_chunker.PdfWriter')
    def test_chunk_pdf_small_document(self, mock_pdf_writer, mock_pdf_reader):
        """Test chunking a small PDF that doesn't need chunking"""
        # Mock a PDF with 20 pages
        mock_reader = Mock()
        mock_reader.pages = [Mock()] * 20
        mock_pdf_reader.return_value = mock_reader
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Since it's small, should return the original temp file path
            chunk_paths = self.chunker.chunk_pdf(b'fake_pdf_content', temp_dir, 'test')
            assert len(chunk_paths) == 1
            # The path should be the temporary file, not a chunk
    
    @patch('backend.services.pdf_chunker.PdfReader')
    @patch('backend.services.pdf_chunker.PdfWriter')
    def test_chunk_pdf_large_document(self, mock_pdf_writer, mock_pdf_reader):
        """Test chunking a large PDF that needs chunking"""
        # Mock a PDF with 65 pages (will create 3 chunks: 30, 30, 5)
        mock_reader = Mock()
        mock_reader.pages = [Mock() for _ in range(65)]
        mock_pdf_reader.return_value = mock_reader
        
        # Mock writer
        mock_writer_instance = Mock()
        mock_pdf_writer.return_value = mock_writer_instance
        
        with tempfile.TemporaryDirectory() as temp_dir:
            chunk_paths = self.chunker.chunk_pdf(b'fake_pdf_content', temp_dir, 'test')
            
            # Should create 3 chunks: 30 + 30 + 5 pages
            assert len(chunk_paths) == 3
            
            # Verify chunk file names
            expected_names = ['test_chunk_1.pdf', 'test_chunk_2.pdf', 'test_chunk_3.pdf']
            for i, chunk_path in enumerate(chunk_paths):
                assert os.path.basename(chunk_path) == expected_names[i]
                assert temp_dir in chunk_path
            
            # Verify writer was called for each chunk
            assert mock_writer_instance.add_page.call_count == 65  # All pages added
            assert mock_writer_instance.write.call_count == 3  # 3 chunks written
    
    def test_cleanup_chunks(self):
        """Test cleanup functionality"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test files
            test_files = []
            for i in range(3):
                test_file = os.path.join(temp_dir, f'test_chunk_{i+1}.pdf')
                with open(test_file, 'w') as f:
                    f.write('test content')
                test_files.append(test_file)
            
            # Verify files exist
            for test_file in test_files:
                assert os.path.exists(test_file)
            
            # Cleanup
            PDFChunker.cleanup_chunks(test_files)
            
            # Verify files are deleted
            for test_file in test_files:
                assert not os.path.exists(test_file)
    
    def test_cleanup_chunks_nonexistent_files(self):
        """Test cleanup with non-existent files doesn't raise errors"""
        fake_files = ['/fake/path/chunk1.pdf', '/fake/path/chunk2.pdf']
        
        # Should not raise any exceptions
        PDFChunker.cleanup_chunks(fake_files)
    
    @patch('backend.services.pdf_chunker.PdfReader')
    def test_error_handling_invalid_pdf(self, mock_pdf_reader):
        """Test error handling for invalid PDF content"""
        mock_pdf_reader.side_effect = Exception("Invalid PDF")
        
        page_count = self.chunker.get_pdf_page_count(b'invalid_pdf_content')
        assert page_count == 0
    
    @patch('backend.services.pdf_chunker.PdfReader')
    def test_edge_case_exact_chunk_size(self, mock_pdf_reader):
        """Test PDF with exactly the chunk size pages"""
        # Mock a PDF with exactly 30 pages
        mock_reader = Mock()
        mock_reader.pages = [Mock()] * 30
        mock_pdf_reader.return_value = mock_reader
        
        result = self.chunker.needs_chunking(b'fake_pdf_content')
        assert result is False  # Exactly at limit, no chunking needed
    
    @patch('backend.services.pdf_chunker.PdfReader')
    def test_edge_case_one_page_over_limit(self, mock_pdf_reader):
        """Test PDF with one page over the limit"""
        # Mock a PDF with 31 pages
        mock_reader = Mock()
        mock_reader.pages = [Mock()] * 31
        mock_pdf_reader.return_value = mock_reader
        
        result = self.chunker.needs_chunking(b'fake_pdf_content')
        assert result is True  # One page over limit, needs chunking