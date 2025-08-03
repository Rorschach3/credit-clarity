"""
Example usage of the new Document AI chunking functionality
"""
import asyncio
import os
from backend.services.document_processor_service import DocumentProcessorService
from backend.services.storage_service import StorageService
from backend.services.job_service import JobService
from backend.config.document_ai_config import DocumentAIConfig


async def example_usage():
    """Example of how to use the new chunked Document AI processing"""
    
    # Check configuration
    config_error = DocumentAIConfig.validate_config()
    if config_error:
        print(f"Configuration error: {config_error}")
        print("Set the following environment variables to use Google Document AI:")
        print("- USE_GOOGLE_DOCUMENT_AI=true")
        print("- GOOGLE_CLOUD_PROJECT_ID=your-project-id")
        print("- GOOGLE_DOCUMENT_AI_PROCESSOR_ID=your-processor-id")
        print("- GOOGLE_DOCUMENT_AI_LOCATION=us (optional, defaults to 'us')")
        print("- GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json")
        print()
        print("Falling back to PyPDF2 processing...")
    
    # Initialize services (you would typically inject these)
    storage_service = StorageService()  # Your storage implementation
    job_service = JobService()  # Your job service implementation
    
    # Get Google AI configuration
    google_ai_config = DocumentAIConfig.get_google_ai_config()
    
    # Initialize document processor with Google AI support
    processor = DocumentProcessorService(
        storage_service=storage_service,
        job_service=job_service,
        google_ai_config=google_ai_config
    )
    
    print("Document AI Processor initialized with configuration:")
    print(f"- Google AI enabled: {google_ai_config['use_google_ai']}")
    print(f"- Project ID: {google_ai_config['project_id'] or 'Not set'}")
    print(f"- Processor ID: {google_ai_config['processor_id'] or 'Not set'}")
    print(f"- Location: {google_ai_config['location']}")
    
    # Example: Process a job
    job_id = "example-job-123"
    
    try:
        print(f"\nProcessing job: {job_id}")
        success = await processor.document_ai_workflow(job_id)
        
        if success:
            print("✅ Document processing completed successfully!")
            
            # Get processing status
            status = await processor.get_processing_status(job_id)
            print(f"Processing status: {status}")
            
        else:
            print("❌ Document processing failed")
            
    except Exception as e:
        print(f"❌ Error during processing: {str(e)}")


def main():
    """Main function to demonstrate usage"""
    print("Credit Clarity - Document AI Chunking Example")
    print("=" * 50)
    
    # Check if we're in the right environment
    if not os.path.exists("backend/services/document_ai_service.py"):
        print("Please run this script from the project root directory")
        return
    
    # Run the example
    asyncio.run(example_usage())


if __name__ == "__main__":
    main()