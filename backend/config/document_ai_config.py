import os
from typing import Dict, Any, Optional

class DocumentAIConfig:
    """Configuration for Document AI services"""
    
    @staticmethod
    def get_google_ai_config() -> Dict[str, Any]:
        """Get Google Document AI configuration from environment variables"""
        return {
            'use_google_ai': os.getenv('USE_GOOGLE_DOCUMENT_AI', 'false').lower() == 'true',
            'project_id': os.getenv('GOOGLE_CLOUD_PROJECT_ID'),
            'processor_id': os.getenv('GOOGLE_DOCUMENT_AI_PROCESSOR_ID'),
            'location': os.getenv('GOOGLE_DOCUMENT_AI_LOCATION', 'us'),
            'credentials_path': os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        }
    
    @staticmethod
    def is_google_ai_enabled() -> bool:
        """Check if Google Document AI is properly configured and enabled"""
        config = DocumentAIConfig.get_google_ai_config()
        
        return (
            config['use_google_ai'] and
            config['project_id'] and
            config['processor_id'] and
            (config['credentials_path'] or os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
        )
    
    @staticmethod
    def validate_config() -> Optional[str]:
        """Validate Document AI configuration and return error message if invalid"""
        config = DocumentAIConfig.get_google_ai_config()
        
        if not config['use_google_ai']:
            return None  # Google AI is disabled, no validation needed
        
        if not config['project_id']:
            return "GOOGLE_CLOUD_PROJECT_ID environment variable is required"
        
        if not config['processor_id']:
            return "GOOGLE_DOCUMENT_AI_PROCESSOR_ID environment variable is required"
        
        if not (config['credentials_path'] or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')):
            return "GOOGLE_APPLICATION_CREDENTIALS environment variable is required"
        
        return None  # Configuration is valid