# Document AI Chunking Implementation

This implementation adds PDF chunking support to handle documents that exceed Google Document AI's 30-page limit.

## Features

- **Automatic PDF Chunking**: Splits large PDFs into 30-page chunks
- **Seamless Integration**: Works with existing Document AI pipeline
- **Fallback Processing**: Falls back to PyPDF2 if Google Document AI fails
- **Result Merging**: Combines results from multiple chunks into a single response
- **Configurable**: Easy to enable/disable Google Document AI

## Architecture

### New Components

1. **PDFChunker** (`backend/services/pdf_chunker.py`)
   - Splits PDFs into smaller chunks
   - Handles page counting and validation
   - Manages temporary file cleanup

2. **GoogleDocumentAIService** (`backend/services/google_document_ai_service.py`)
   - Google Cloud Document AI integration
   - Handles chunked document processing
   - Merges results from multiple chunks

3. **DocumentAIConfig** (`backend/config/document_ai_config.py`)
   - Configuration management
   - Environment variable validation

### Updated Components

- **DocumentAIService**: Now supports Google Document AI with fallback
- **DocumentProcessorService**: Updated to accept Google AI configuration

## Configuration

Set these environment variables to enable Google Document AI:

```bash
# Enable Google Document AI
USE_GOOGLE_DOCUMENT_AI=true

# Google Cloud configuration
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_DOCUMENT_AI_PROCESSOR_ID=your-processor-id
GOOGLE_DOCUMENT_AI_LOCATION=us
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

## Usage

### Basic Usage

```python
from backend.services.document_processor_service import DocumentProcessorService
from backend.config.document_ai_config import DocumentAIConfig

# Get configuration
google_ai_config = DocumentAIConfig.get_google_ai_config()

# Initialize processor
processor = DocumentProcessorService(
    storage_service=storage_service,
    job_service=job_service,
    google_ai_config=google_ai_config
)

# Process document (handles chunking automatically)
success = await processor.document_ai_workflow(job_id)
```

### Direct Chunking

```python
from backend.services.pdf_chunker import PDFChunker

chunker = PDFChunker(chunk_size=30)

# Check if PDF needs chunking
if chunker.needs_chunking(pdf_content):
    print(f"PDF has {chunker.get_pdf_page_count(pdf_content)} pages")
    
    # Chunk the PDF
    chunk_paths = chunker.chunk_pdf(pdf_content, temp_dir, "document")
    print(f"Created {len(chunk_paths)} chunks")
    
    # Process each chunk...
    
    # Cleanup
    PDFChunker.cleanup_chunks(chunk_paths)
```

## Processing Flow

1. **Document Upload**: User uploads a PDF document
2. **Type Detection**: System detects it's a PDF
3. **Page Count Check**: System checks if PDF > 30 pages
4. **Chunking (if needed)**: PDF is split into 30-page chunks
5. **Document AI Processing**: Each chunk is processed with Google Document AI
6. **Result Merging**: Results are combined into a single response
7. **Cleanup**: Temporary chunk files are removed

## Features

### Chunking Logic

- PDFs ≤ 30 pages: Processed directly
- PDFs > 30 pages: Split into chunks of 30 pages each
- Last chunk may have fewer than 30 pages

### Result Merging

- Text content is concatenated
- Page numbers are adjusted across chunks
- Tables are merged with unique IDs
- Confidence scores are averaged

### Error Handling

- Google Document AI failures fall back to PyPDF2
- Invalid PDFs are handled gracefully
- Temporary files are always cleaned up

## Testing

Run the test suite:

```bash
cd backend
python -m pytest tests/test_pdf_chunker.py -v
```

## Example

See `backend/example_usage.py` for a complete example of how to use the new chunking functionality.

## Dependencies

The following packages are already included in `requirements.txt`:

- `google-cloud-documentai==3.5.0`
- `PyPDF2==3.0.1`
- `google-auth`
- `google-api-core`

## Monitoring

The system provides detailed logging for:

- Chunk creation and processing
- Google Document AI API calls
- Fallback scenarios
- Processing statistics

## Troubleshooting

### Common Issues

1. **"Document AI client not properly initialized"**
   - Check that all required environment variables are set
   - Verify Google Cloud credentials are valid

2. **"Failed to chunk PDF"**
   - Ensure PDF is not corrupted
   - Check file permissions and disk space

3. **Processing falls back to PyPDF2**
   - This is normal if Google Document AI is not configured
   - Check logs for specific Google API errors

### Performance Considerations

- Large PDFs (100+ pages) will take longer to process
- Each chunk requires a separate API call to Google Document AI
- Consider implementing parallel processing for very large documents
- Monitor API quotas and rate limits

## Future Enhancements

- Parallel chunk processing
- Custom chunk size configuration per document type
- Resume processing from failed chunks
- Advanced result merging strategies
- Caching of processed chunks