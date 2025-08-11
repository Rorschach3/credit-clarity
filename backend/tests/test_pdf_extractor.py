"""
Test PDF text extraction service using TDD approach
"""
import pytest
import asyncio
from pathlib import Path
import tempfile
import os

# Add the backend directory to the path
import sys
sys.path.append('/mnt/c/projects/credit-clarity/backend')

from services.tradeline_extraction.pdf_extractor import (
    TransUnionPDFExtractor,
    PDFExtractionResult
)


class TestTransUnionPDFExtractor:
    """Test PDF extraction functionality"""
    
    @pytest.fixture
    def extractor(self):
        """PDF extractor instance"""
        return TransUnionPDFExtractor()
    
    @pytest.fixture
    def sample_pdf_path(self):
        """Path to sample PDF file"""
        return Path("/mnt/c/projects/credit-clarity/TransUnion-06-10-2025.pdf")
    
    @pytest.fixture
    def temp_pdf_file(self):
        """Create temporary PDF file for testing"""
        content = b"""%PDF-1.4
1 0 obj
<< /Type /Pages /Kids [2 0 R] /Count 1 >>
endobj
2 0 obj
<< /Type /Page /Parent 1 0 R /MediaBox [0 0 612 792]
   /Contents 3 0 R /Resources << /Font << /F1 4 0 R >> >>
>>
endobj
3 0 obj
<< /Length 55 >>
stream
BT
/F1 12 Tf
100 700 Td
(Test Credit Report) Tj
ET
endstream
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000178 00000 n 
0000000284 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
355
%%EOF"""
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass
    
    def test_extractor_initialization(self, extractor):
        """Test PDF extractor initialization"""
        assert extractor.supported_extensions == {'.pdf'}
        assert extractor.max_file_size_mb == 50
        assert extractor.extraction_timeout_seconds == 30
    
    def test_validate_pdf_file_success(self, extractor, temp_pdf_file):
        """Test successful PDF file validation"""
        result = extractor.validate_pdf_file(temp_pdf_file)
        
        assert result['valid'] is True
        assert len(result['errors']) == 0
        assert 'file_info' in result
        assert 'size_bytes' in result['file_info']
        assert 'pdf_version' in result['file_info']
        assert result['file_info']['pdf_version'].startswith('%PDF-')
    
    def test_validate_pdf_file_not_found(self, extractor):
        """Test validation of non-existent file"""
        result = extractor.validate_pdf_file("nonexistent.pdf")
        
        assert result['valid'] is False
        assert any("File not found" in error for error in result['errors'])
    
    def test_validate_pdf_file_wrong_extension(self, extractor):
        """Test validation of non-PDF file"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"Not a PDF file")
            temp_path = f.name
        
        try:
            result = extractor.validate_pdf_file(temp_path)
            assert result['valid'] is False
            assert any("Unsupported file type" in error for error in result['errors'])
        finally:
            os.unlink(temp_path)
    
    def test_validate_pdf_file_invalid_format(self, extractor):
        """Test validation of file with PDF extension but invalid format"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b"This is not a valid PDF file")
            temp_path = f.name
        
        try:
            result = extractor.validate_pdf_file(temp_path)
            assert result['valid'] is False
            assert any("Invalid PDF file format" in error for error in result['errors'])
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_extract_text_from_pdf_success(self, extractor, temp_pdf_file):
        """Test successful text extraction"""
        result = await extractor.extract_text_from_pdf(temp_pdf_file)
        
        assert isinstance(result, PDFExtractionResult)
        assert result.success is True
        assert result.text is not None
        assert result.error is None
        assert result.file_size_bytes is not None
        assert result.extraction_time_ms is not None
        assert result.extraction_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_extract_text_from_pdf_validation_failure(self, extractor):
        """Test extraction with invalid file"""
        result = await extractor.extract_text_from_pdf("nonexistent.pdf")
        
        assert isinstance(result, PDFExtractionResult)
        assert result.success is False
        assert result.text is None
        assert result.error is not None
        assert "Validation failed" in result.error
    
    @pytest.mark.asyncio
    async def test_extract_sample_transunion_text(self, extractor):
        """Test extraction of sample TransUnion text"""
        # Test the sample PDF that should return our test data
        sample_path = "/mnt/c/projects/credit-clarity/TransUnion-06-10-2025.pdf"
        
        # Check if file exists first
        if not Path(sample_path).exists():
            pytest.skip("Sample PDF file not available for testing")
        
        result = await extractor.extract_text_from_pdf(sample_path)
        
        assert result.success is True
        assert result.text is not None
        
        # Verify the text contains expected tradeline information
        text_lower = result.text.lower()
        assert "transunion" in text_lower
        assert "lentegrity llc" in text_lower
        assert "capital one" in text_lower
        assert "account number" in text_lower
        assert "account type" in text_lower
        
        # Verify it's recognized as a TransUnion report
        assert extractor.is_transunion_report(result.text) is True
    
    def test_is_transunion_report_positive(self, extractor):
        """Test TransUnion report identification - positive cases"""
        transunion_text = """
        TransUnion Credit Report
        Account Information
        Tradeline Details
        """
        assert extractor.is_transunion_report(transunion_text) is True
        
        # Test case insensitive
        transunion_text_upper = "TRANSUNION CREDIT REPORT TRADELINE"
        assert extractor.is_transunion_report(transunion_text_upper) is True
    
    def test_is_transunion_report_negative(self, extractor):
        """Test TransUnion report identification - negative cases"""
        non_transunion_text = """
        Random document text
        No credit information
        Just some random content
        """
        assert extractor.is_transunion_report(non_transunion_text) is False
        
        empty_text = ""
        assert extractor.is_transunion_report(empty_text) is False


class TestPDFExtractionResult:
    """Test PDFExtractionResult dataclass"""
    
    def test_success_result(self):
        """Test successful extraction result"""
        result = PDFExtractionResult(
            success=True,
            text="Sample text content",
            page_count=5,
            file_size_bytes=1024,
            extraction_time_ms=150.5
        )
        
        assert result.success is True
        assert result.text == "Sample text content"
        assert result.error is None
        assert result.page_count == 5
        assert result.file_size_bytes == 1024
        assert result.extraction_time_ms == 150.5
    
    def test_failure_result(self):
        """Test failed extraction result"""
        result = PDFExtractionResult(
            success=False,
            error="File not found"
        )
        
        assert result.success is False
        assert result.text is None
        assert result.error == "File not found"
        assert result.page_count is None
        assert result.file_size_bytes is None
        assert result.extraction_time_ms is None


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])