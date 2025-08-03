import os
import tempfile
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from google.cloud import documentai_v1beta3 as documentai
from google.api_core.exceptions import GoogleAPIError

from ..models.tradeline_models import DocumentType, ExtractedTable, ExtractedText, DocumentAIResult
from .pdf_chunker import PDFChunker

logger = logging.getLogger(__name__)


class GoogleDocumentAIService:
    """Service for processing documents with Google Cloud Document AI"""
    
    def __init__(self, project_id: str, location: str = "us", processor_id: str = None):
        self.project_id = project_id
        self.location = location
        self.processor_id = processor_id
        self.client = None
        self.processor_name = None
        self.chunker = PDFChunker()
        
        if project_id and processor_id:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Document AI client and processor name"""
        try:
            self.client = documentai.DocumentProcessorServiceClient()
            self.processor_name = f"projects/{self.project_id}/locations/{self.location}/processors/{self.processor_id}"
            logger.info(f"Initialized Google Document AI client for processor: {self.processor_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Document AI client: {str(e)}")
            raise
    
    async def process_document(self, file_content: bytes, file_name: str) -> DocumentAIResult:
        """Process document with Google Document AI, handling chunking for large PDFs"""
        try:
            logger.info(f"Starting Google Document AI processing for {file_name}")
            start_time = datetime.now()
            
            if not self.client or not self.processor_name:
                raise ValueError("Document AI client not properly initialized")
            
            # Determine document type
            doc_type = self._detect_document_type(file_name, file_content)
            
            if doc_type == DocumentType.PDF:
                result = await self._process_pdf_with_chunking(file_content, file_name)
            elif doc_type == DocumentType.IMAGE:
                result = await self._process_single_document(file_content, file_name, doc_type)
            else:
                raise ValueError(f"Unsupported document type for Document AI: {doc_type}")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            result.processing_time = processing_time
            
            logger.info(f"Google Document AI processing completed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Google Document AI processing failed: {str(e)}")
            raise
    
    async def _process_pdf_with_chunking(self, file_content: bytes, file_name: str) -> DocumentAIResult:
        """Process PDF with chunking if necessary"""
        try:
            # Check if chunking is needed
            if not self.chunker.needs_chunking(file_content):
                logger.info("PDF is within page limit, processing directly")
                return await self._process_single_document(file_content, file_name, DocumentType.PDF)
            
            logger.info("PDF exceeds page limit, processing with chunking")
            
            # Create temporary directory for chunks
            with tempfile.TemporaryDirectory() as temp_dir:
                # Chunk the PDF
                chunk_paths = self.chunker.chunk_pdf(file_content, temp_dir, 
                                                   file_name.rsplit('.', 1)[0])
                
                # Process each chunk
                processed_docs = []
                for chunk_path in chunk_paths:
                    with open(chunk_path, 'rb') as chunk_file:
                        chunk_content = chunk_file.read()
                    
                    doc_result = await self._process_single_document(
                        chunk_content, 
                        os.path.basename(chunk_path), 
                        DocumentType.PDF
                    )
                    
                    if doc_result:
                        processed_docs.append(doc_result)
                
                if not processed_docs:
                    raise RuntimeError("All chunked documents failed to process")
                
                # Merge results
                merged_result = self._merge_document_results(processed_docs, file_name)
                return merged_result
                
        except Exception as e:
            logger.error(f"Failed to process PDF with chunking: {str(e)}")
            raise
    
    async def _process_single_document(self, file_content: bytes, file_name: str, 
                                     doc_type: DocumentType) -> DocumentAIResult:
        """Process a single document with Document AI"""
        try:
            # Determine MIME type
            mime_type = self._get_mime_type(doc_type)
            
            # Create Document AI request
            raw_document = documentai.RawDocument(
                content=file_content, 
                mime_type=mime_type
            )
            
            request = documentai.ProcessRequest(
                name=self.processor_name,
                raw_document=raw_document
            )
            
            # Process document
            logger.info(f"Processing {file_name} with Document AI")
            result = self.client.process_document(request=request)
            document = result.document
            
            # Extract data from Document AI response
            text_blocks = self._extract_text_blocks(document)
            tables = self._extract_tables(document)
            
            return DocumentAIResult(
                job_id="",  # Will be set by caller
                document_type=doc_type,
                total_pages=len(document.pages) if document.pages else 1,
                tables=tables,
                text_blocks=text_blocks,
                raw_text=document.text,
                metadata={
                    "file_name": file_name,
                    "file_size": len(file_content),
                    "processing_method": "google_document_ai",
                    "processor_id": self.processor_id
                },
                processing_time=0.0,
                confidence_score=self._calculate_average_confidence(text_blocks, tables)
            )
            
        except GoogleAPIError as e:
            logger.error(f"Google API error processing {file_name}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error processing {file_name}: {str(e)}")
            raise
    
    def _extract_text_blocks(self, document: documentai.Document) -> List[ExtractedText]:
        """Extract text blocks from Document AI response"""
        text_blocks = []
        
        for page_num, page in enumerate(document.pages, 1):
            if hasattr(page, 'paragraphs') and page.paragraphs:
                for para in page.paragraphs:
                    if hasattr(para, 'layout') and para.layout:
                        text_content = self._get_text_from_layout(document.text, para.layout)
                        if text_content.strip():
                            text_blocks.append(ExtractedText(
                                content=text_content,
                                page_number=page_num,
                                confidence=para.layout.confidence if hasattr(para.layout, 'confidence') else 0.9,
                                bounding_box=self._extract_bounding_box(para.layout)
                            ))
            else:
                # Fallback: use page-level text if no paragraphs
                page_text = self._get_page_text(document.text, page)
                if page_text.strip():
                    text_blocks.append(ExtractedText(
                        content=page_text,
                        page_number=page_num,
                        confidence=0.85,
                        bounding_box={"x": 0, "y": 0, "width": 612, "height": 792}
                    ))
        
        return text_blocks
    
    def _extract_tables(self, document: documentai.Document) -> List[ExtractedTable]:
        """Extract tables from Document AI response"""
        tables = []
        
        for page_num, page in enumerate(document.pages, 1):
            if hasattr(page, 'tables') and page.tables:
                for table_idx, table in enumerate(page.tables):
                    headers = []
                    rows = []
                    
                    # Extract headers from first row
                    if table.header_rows:
                        header_row = table.header_rows[0]
                        for cell in header_row.cells:
                            cell_text = self._get_text_from_layout(document.text, cell.layout)
                            headers.append(cell_text.strip())
                    
                    # Extract data rows
                    if table.body_rows:
                        for row in table.body_rows:
                            row_data = []
                            for cell in row.cells:
                                cell_text = self._get_text_from_layout(document.text, cell.layout)
                                row_data.append(cell_text.strip())
                            if row_data:  # Only add non-empty rows
                                rows.append(row_data)
                    
                    if headers or rows:  # Only add if we have data
                        tables.append(ExtractedTable(
                            table_id=f"table_{page_num}_{table_idx + 1}",
                            headers=headers,
                            rows=rows,
                            confidence=0.9,
                            page_number=page_num,
                            bounding_box=self._extract_bounding_box(table.layout) if hasattr(table, 'layout') else {}
                        ))
        
        return tables
    
    def _merge_document_results(self, documents: List[DocumentAIResult], 
                              original_filename: str) -> DocumentAIResult:
        """Merge results from multiple chunked documents"""
        if not documents:
            raise ValueError("No documents to merge")
        
        # Base document is the first one
        merged = documents[0]
        merged.metadata["file_name"] = original_filename
        merged.metadata["chunked"] = True
        merged.metadata["chunk_count"] = len(documents)
        
        total_pages = 0
        current_page_offset = 0
        
        for i, doc in enumerate(documents):
            if i == 0:
                total_pages += doc.total_pages
                current_page_offset = doc.total_pages
                continue
            
            # Append text
            merged.raw_text += "\n" + doc.raw_text
            
            # Append text blocks with adjusted page numbers
            for text_block in doc.text_blocks:
                adjusted_block = ExtractedText(
                    content=text_block.content,
                    page_number=text_block.page_number + current_page_offset,
                    confidence=text_block.confidence,
                    bounding_box=text_block.bounding_box
                )
                merged.text_blocks.append(adjusted_block)
            
            # Append tables with adjusted page numbers
            for table in doc.tables:
                adjusted_table = ExtractedTable(
                    table_id=f"chunk_{i+1}_{table.table_id}",
                    headers=table.headers,
                    rows=table.rows,
                    confidence=table.confidence,
                    page_number=table.page_number + current_page_offset,
                    bounding_box=table.bounding_box
                )
                merged.tables.append(adjusted_table)
            
            total_pages += doc.total_pages
            current_page_offset += doc.total_pages
        
        merged.total_pages = total_pages
        
        # Recalculate confidence
        merged.confidence_score = self._calculate_average_confidence(
            merged.text_blocks, merged.tables
        )
        
        logger.info(f"Merged {len(documents)} chunks into single result with {total_pages} pages")
        return merged
    
    def _get_text_from_layout(self, document_text: str, layout) -> str:
        """Extract text from layout segments"""
        if not hasattr(layout, 'text_anchor') or not layout.text_anchor:
            return ""
        
        text_segments = []
        for segment in layout.text_anchor.text_segments:
            start_index = int(segment.start_index) if hasattr(segment, 'start_index') else 0
            end_index = int(segment.end_index) if hasattr(segment, 'end_index') else len(document_text)
            text_segments.append(document_text[start_index:end_index])
        
        return "".join(text_segments)
    
    def _get_page_text(self, document_text: str, page) -> str:
        """Get text for a specific page"""
        # This is a simplified implementation
        # In practice, you'd need to track text segments by page
        return document_text
    
    def _extract_bounding_box(self, layout) -> Dict[str, float]:
        """Extract bounding box from layout"""
        if not hasattr(layout, 'bounding_poly') or not layout.bounding_poly:
            return {"x": 0, "y": 0, "width": 0, "height": 0}
        
        vertices = layout.bounding_poly.vertices
        if not vertices:
            return {"x": 0, "y": 0, "width": 0, "height": 0}
        
        x_coords = [v.x for v in vertices if hasattr(v, 'x')]
        y_coords = [v.y for v in vertices if hasattr(v, 'y')]
        
        if not x_coords or not y_coords:
            return {"x": 0, "y": 0, "width": 0, "height": 0}
        
        return {
            "x": min(x_coords),
            "y": min(y_coords),
            "width": max(x_coords) - min(x_coords),
            "height": max(y_coords) - min(y_coords)
        }
    
    def _calculate_average_confidence(self, text_blocks: List[ExtractedText], 
                                    tables: List[ExtractedTable]) -> float:
        """Calculate average confidence score"""
        confidences = []
        
        for block in text_blocks:
            confidences.append(block.confidence)
        
        for table in tables:
            confidences.append(table.confidence)
        
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    def _detect_document_type(self, file_name: str, content: bytes) -> DocumentType:
        """Detect document type from filename and content"""
        extension = file_name.lower().split('.')[-1]
        
        type_mapping = {
            'pdf': DocumentType.PDF,
            'png': DocumentType.IMAGE,
            'jpg': DocumentType.IMAGE,
            'jpeg': DocumentType.IMAGE,
            'tiff': DocumentType.IMAGE,
        }
        
        return type_mapping.get(extension, DocumentType.UNKNOWN)
    
    def _get_mime_type(self, doc_type: DocumentType) -> str:
        """Get MIME type for document type"""
        mime_mapping = {
            DocumentType.PDF: "application/pdf",
            DocumentType.IMAGE: "image/jpeg",  # Default, could be more specific
        }
        
        return mime_mapping.get(doc_type, "application/octet-stream")