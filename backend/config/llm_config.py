"""
LLM Configuration for Credit Clarity backend.
Manages OpenAI and Google Gemini API settings.
"""
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class LLMConfig:
    """Configuration for LLM services"""

    # API Keys
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None

    # OpenAI Configuration
    openai_model: str = "gpt-4-turbo-preview"
    model_name: str = "gpt-4-turbo-preview"  # Alias for openai_model for backward compatibility
    openai_temperature: float = 0.1
    openai_max_tokens: int = 4096
    openai_timeout: int = 60

    # Google Gemini Configuration
    gemini_model: str = "gemini-2.0-flash-exp"
    gemini_temperature: float = 0.1
    gemini_max_tokens: int = 8192

    # Request Configuration
    max_retries: int = 3
    retry_delay: int = 2
    request_timeout: int = 120

    # Token Management
    max_context_tokens: int = 100000
    max_completion_tokens: int = 4096
    truncation_threshold: float = 0.9

    # Confidence Thresholds
    min_confidence_score: float = 0.3
    validation_threshold: float = 0.7

    # Processing Settings
    enable_caching: bool = True
    enable_validation: bool = True
    enable_retry_logic: bool = True

    def __post_init__(self):
        """Initialize configuration from environment variables"""
        self.openai_api_key = self.openai_api_key or os.getenv("OPENAI_API_KEY")
        self.google_api_key = self.google_api_key or os.getenv("GOOGLE_API_KEY")

        # Override defaults from environment if present
        self.openai_model = os.getenv("OPENAI_MODEL", self.openai_model)
        self.gemini_model = os.getenv("GEMINI_MODEL", self.gemini_model)

    def get_openai_params(self) -> Dict[str, Any]:
        """Get OpenAI API parameters"""
        return {
            "model": self.openai_model,
            "temperature": self.openai_temperature,
            "max_tokens": self.openai_max_tokens,
            "timeout": self.openai_timeout
        }

    def get_gemini_params(self) -> Dict[str, Any]:
        """Get Google Gemini API parameters"""
        return {
            "model": self.gemini_model,
            "temperature": self.gemini_temperature,
            "max_output_tokens": self.gemini_max_tokens
        }

    def is_openai_configured(self) -> bool:
        """Check if OpenAI is properly configured"""
        return bool(self.openai_api_key)

    def is_gemini_configured(self) -> bool:
        """Check if Gemini is properly configured"""
        return bool(self.google_api_key)

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Create configuration from environment variables"""
        return cls()

    @classmethod
    def default(cls) -> "LLMConfig":
        """Create default configuration"""
        return cls()


# Global configuration instance
_default_config: Optional[LLMConfig] = None

def get_llm_config() -> LLMConfig:
    """Get or create the default LLM configuration"""
    global _default_config
    if _default_config is None:
        _default_config = LLMConfig.from_env()
    return _default_config

def set_llm_config(config: LLMConfig):
    """Set the default LLM configuration"""
    global _default_config
    _default_config = config
