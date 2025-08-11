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
    admin_emails: List[str] = Field(default_factory=list, env="ADMIN_EMAILS")
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        env="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    
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
    
    # Monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_interval: int = Field(default=60, env="METRICS_INTERVAL")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields from .env
    
    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @validator('admin_emails', pre=True)
    def parse_admin_emails(cls, v):
        if isinstance(v, str):
            return [email.strip() for email in v.split(',')]
        return v
    
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
        if self.is_production():
            # In production, only allow specific origins
            production_origins = [
                origin for origin in self.cors_origins 
                if not origin.startswith('http://localhost')
            ]
            return production_origins or ["https://app.creditclarity.com"]
        return self.cors_origins
    
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
            "admin_emails": self.admin_emails,
            "rate_limit": {
                "requests": self.rate_limit_requests,
                "window": self.rate_limit_window
            }
        }

# Environment-specific configuration classes
class DevelopmentSettings(Settings):
    """Development environment settings."""
    environment: str = "development"
    debug: bool = True
    log_level: str = "DEBUG"
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]

class ProductionSettings(Settings):
    """Production environment settings."""
    environment: str = "production"
    debug: bool = False
    log_level: str = "INFO"
    cors_origins: List[str] = [
        "https://app.creditclarity.com",
        "https://creditclarity.com"
    ]

class TestingSettings(Settings):
    """Testing environment settings."""
    environment: str = "testing"
    debug: bool = True
    log_level: str = "DEBUG"
    database_url: str = "sqlite:///test.db"
    cache_ttl: int = 60  # Shorter TTL for tests

@lru_cache()
def get_settings() -> Settings:
    """Get application settings (cached)."""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()

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