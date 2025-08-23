"""
Enhanced configuration management
Environment-specific settings with validation and security
"""
import os
from typing import List, Optional, Dict, Any
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with environment-specific configuration."""
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_prefix: str = Field(default="/api", env="API_PREFIX")
    
    # Database
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    supabase_url: Optional[str] = Field(default=None, env="SUPABASE_URL")
    supabase_anon_key: Optional[str] = Field(default=None, env="SUPABASE_ANON_KEY")
    
    # Security
    jwt_secret: Optional[str] = Field(default=None, env="JWT_SECRET")
    encryption_key: Optional[str] = Field(default=None, env="ENCRYPTION_KEY")
    admin_emails: Optional[str] = Field(default="", env="ADMIN_EMAILS")
    admin_email_domains: Optional[str] = Field(default="@creditclarity.com", env="ADMIN_EMAIL_DOMAINS")
    
    # CORS
    cors_origins: Optional[str] = Field(
        default="http://localhost:8080,http://localhost:3000",
        env="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_methods: Optional[str] = Field(
        default="GET,POST,PUT,DELETE,OPTIONS,PATCH",
        env="CORS_METHODS"
    )
    cors_headers: Optional[str] = Field(
        default="Accept,Content-Type,Authorization",
        env="CORS_HEADERS"
    )
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")
    
    # External Services
    google_cloud_project_id: Optional[str] = Field(default=None, env="GOOGLE_CLOUD_PROJECT_ID")
    document_ai_processor_id: Optional[str] = Field(default=None, env="DOCUMENT_AI_PROCESSOR_ID")
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    
    # Performance
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    max_workers: int = Field(default=3, env="MAX_WORKERS")
    
    # File Processing
    max_file_size_mb: int = Field(default=50, env="MAX_FILE_SIZE_MB")
    temp_dir: str = Field(default="/tmp", env="TEMP_DIR")
    
    # Background Jobs
    background_job_timeout: int = Field(default=3600, env="BACKGROUND_JOB_TIMEOUT")
    
    # Monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_interval: int = Field(default=60, env="METRICS_INTERVAL")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="structured", env="LOG_FORMAT")
    
    # Database Pool
    database_pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "allow",  # Allow extra fields from .env
    }
    
    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        # Keep as string for storage, parse in property method
        return v if isinstance(v, str) else str(v)
    
    @validator('admin_emails', pre=True)
    def parse_admin_emails(cls, v):
        # Keep as string for storage, parse in property method
        return v if isinstance(v, str) else str(v)
    
    @validator('admin_email_domains', pre=True)
    def parse_admin_email_domains(cls, v):
        # Keep as string for storage, parse in property method
        return v if isinstance(v, str) else str(v)
    
    @validator('cors_methods', pre=True)
    def parse_cors_methods(cls, v):
        # Keep as string for storage, parse in property method
        return v if isinstance(v, str) else str(v)
    
    @validator('cors_headers', pre=True)
    def parse_cors_headers(cls, v):
        # Keep as string for storage, parse in property method
        return v if isinstance(v, str) else str(v)
    
    @validator('environment')
    def validate_environment(cls, v):
        valid_envs = ['development', 'testing', 'staging', 'production']
        if v not in valid_envs:
            raise ValueError(f'Environment must be one of {valid_envs}')
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of {valid_levels}')
        return v.upper()
    
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"
    
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.environment == "testing"
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins based on environment."""
        origins = self.get_cors_origins_list()
        if self.is_production():
            # In production, only allow specific origins
            production_origins = [
                origin for origin in origins 
                if not origin.startswith('http://localhost')
            ]
            return production_origins or ["https://app.creditclarity.com"]
        return origins
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return {
            "database_url": self.database_url,
            "supabase_url": self.supabase_url,
            "supabase_key": self.supabase_anon_key
        }
    
    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration."""
        return {
            "redis_url": self.redis_url,
            "ttl": self.cache_ttl,
            "enabled": self.redis_url is not None
        }
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get processing configuration."""
        return {
            "max_workers": self.max_workers,
            "max_file_size_mb": self.max_file_size_mb,
            "temp_dir": self.temp_dir,
            "google_cloud_project_id": self.google_cloud_project_id,
            "document_ai_processor_id": self.document_ai_processor_id,
            "gemini_api_key": self.gemini_api_key
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        return {
            "jwt_secret": self.jwt_secret,
            "encryption_key": self.encryption_key,
            "admin_emails": self.get_admin_emails_list(),
            "admin_email_domains": self.get_admin_email_domains_list(),
            "rate_limit": {
                "requests": self.rate_limit_requests,
                "window": self.rate_limit_window
            }
        }
    
    def get_cors_config(self) -> Dict[str, Any]:
        """Get CORS configuration."""
        return {
            "origins": self.get_cors_origins(),
            "allow_credentials": self.cors_allow_credentials,
            "methods": self.get_cors_methods_list(),
            "headers": self.get_cors_headers_list()
        }
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration."""
        return {
            "enable_metrics": self.enable_metrics,
            "metrics_port": self.metrics_port,
            "metrics_interval": self.metrics_interval,
            "log_level": self.log_level,
            "log_format": self.log_format
        }
    
    # Helper methods to parse string fields into lists
    def get_admin_emails_list(self) -> List[str]:
        """Parse admin emails from string to list."""
        if not self.admin_emails or self.admin_emails.strip() == "":
            return []
        try:
            import json
            return json.loads(self.admin_emails)
        except (json.JSONDecodeError, ImportError):
            return [email.strip() for email in self.admin_emails.split(',') if email.strip()]
    
    def get_admin_email_domains_list(self) -> List[str]:
        """Parse admin email domains from string to list."""
        if not self.admin_email_domains or self.admin_email_domains.strip() == "":
            return ["@creditclarity.com"]
        try:
            import json
            return json.loads(self.admin_email_domains)
        except (json.JSONDecodeError, ImportError):
            return [domain.strip() for domain in self.admin_email_domains.split(',') if domain.strip()]
    
    def get_cors_origins_list(self) -> List[str]:
        """Parse CORS origins from string to list."""
        if not self.cors_origins or self.cors_origins.strip() == "":
            return ["http://localhost:8080", "http://localhost:3000"]
        try:
            import json
            return json.loads(self.cors_origins)
        except (json.JSONDecodeError, ImportError):
            return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]
    
    def get_cors_methods_list(self) -> List[str]:
        """Parse CORS methods from string to list."""
        if not self.cors_methods or self.cors_methods.strip() == "":
            return ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
        try:
            import json
            return [method.upper() for method in json.loads(self.cors_methods)]
        except (json.JSONDecodeError, ImportError):
            return [method.strip().upper() for method in self.cors_methods.split(',') if method.strip()]
    
    def get_cors_headers_list(self) -> List[str]:
        """Parse CORS headers from string to list."""
        if not self.cors_headers or self.cors_headers.strip() == "":
            return ["Accept", "Content-Type", "Authorization"]
        try:
            import json
            return json.loads(self.cors_headers)
        except (json.JSONDecodeError, ImportError):
            return [header.strip() for header in self.cors_headers.split(',') if header.strip()]

# Environment-specific configuration classes
class DevelopmentSettings(Settings):
    """Development environment settings."""
    environment: str = "development"
    debug: bool = True
    log_level: str = "DEBUG"

class ProductionSettings(Settings):
    """Production environment settings."""
    environment: str = "production"
    debug: bool = False
    log_level: str = "INFO"

class TestingSettings(Settings):
    """Testing environment settings."""
    environment: str = "testing"
    debug: bool = True
    log_level: str = "DEBUG"
    database_url: str = "sqlite:///test.db"
    cache_ttl: int = 60  # Shorter TTL for tests

@lru_cache()
def get_settings() -> Settings:
    """Get application settings (cached) with error handling."""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    try:
        if env == "production":
            return ProductionSettings()
        elif env == "testing":
            return TestingSettings()
        else:
            return DevelopmentSettings()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error loading settings: {e}")
        
        # Return basic fallback settings
        return Settings(
            environment="development",
            debug=True,
            supabase_url=os.getenv("SUPABASE_URL", ""),
            supabase_anon_key=os.getenv("SUPABASE_ANON_KEY", ""),
            admin_emails="",
            admin_email_domains="@creditclarity.com",
            cors_origins="http://localhost:8080,http://localhost:3000",
            cors_methods="GET,POST,PUT,DELETE,OPTIONS,PATCH",
            cors_headers="Accept,Content-Type,Authorization"
        )

def validate_required_settings():
    """Validate that required settings are present."""
    settings = get_settings()
    errors = []
    
    # Check critical settings based on environment
    if settings.is_production():
        required_prod_settings = [
            "jwt_secret",
            "database_url", 
            "supabase_url",
            "supabase_anon_key"
        ]
        
        for setting in required_prod_settings:
            if not getattr(settings, setting):
                errors.append(f"Missing required production setting: {setting}")
    
    # Check Google Cloud settings if processing is enabled
    if settings.google_cloud_project_id:
        if not settings.document_ai_processor_id:
            errors.append("DOCUMENT_AI_PROCESSOR_ID required when using Google Cloud")
    
    if errors:
        raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    return True

# Configuration utilities
def get_config_summary() -> Dict[str, Any]:
    """Get configuration summary for debugging."""
    settings = get_settings()
    
    return {
        "environment": settings.environment,
        "debug": settings.debug,
        "api": {
            "host": settings.api_host,
            "port": settings.api_port,
            "prefix": settings.api_prefix
        },
        "features": {
            "database": bool(settings.database_url or settings.supabase_url),
            "cache": bool(settings.redis_url),
            "processing": bool(settings.google_cloud_project_id),
            "metrics": settings.enable_metrics
        },
        "cors_origins": len(settings.cors_origins),
        "admin_emails": len(settings.admin_emails)
    }

def load_config_from_file(config_path: str) -> Dict[str, Any]:
    """Load configuration from external file."""
    import json
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in configuration file: {e}")

# Export commonly used settings
settings = get_settings()