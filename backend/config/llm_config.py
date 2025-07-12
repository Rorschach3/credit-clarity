import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class LLMConfig:
    """Configuration for LLM services"""
    
    # OpenAI Configuration
    openai_api_key: str
    model_name: str = "gpt-4"
    max_tokens: int = 8000
    temperature: float = 0.1
    top_p: float = 0.9
    
    # Request Configuration
    max_retries: int = 3
    timeout_seconds: int = 120
    
    # Processing Configuration
    default_confidence_threshold: float = 0.7
    max_tradelines_per_request: int = 50
    
    # System Prompt
    system_prompt: str = """You are an expert financial document processor specializing in credit reports and tradeline data. 
    Your role is to accurately extract, normalize, and validate financial information while maintaining the highest standards of data quality and consistency.
    
    Key principles:
    - Accuracy over speed
    - Preserve original meaning while standardizing format
    - Flag uncertainties rather than guessing
    - Maintain data privacy and security standards
    - Provide confidence scores for all extractions"""
    
    # Rate Limiting
    requests_per_minute: int = 10
    tokens_per_minute: int = 100000
    
    @classmethod
    def from_env(cls) -> 'LLMConfig':
        """Create configuration from environment variables"""
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            model_name=os.getenv("OPENAI_MODEL", "gpt-4"),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "8000")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
            top_p=float(os.getenv("LLM_TOP_P", "0.9")),
            max_retries=int(os.getenv("LLM_MAX_RETRIES", "3")),
            timeout_seconds=int(os.getenv("LLM_TIMEOUT", "120")),
            default_confidence_threshold=float(os.getenv("LLM_CONFIDENCE_THRESHOLD", "0.7")),
            max_tradelines_per_request=int(os.getenv("LLM_MAX_TRADELINES", "50")),
            requests_per_minute=int(os.getenv("LLM_RATE_LIMIT_RPM", "10")),
            tokens_per_minute=int(os.getenv("LLM_RATE_LIMIT_TPM", "100000"))
        )

def get_llm_config() -> LLMConfig:
    """Get LLM configuration instance"""
    return LLMConfig.from_env()

# Alternative models configuration
SUPPORTED_MODELS = {
    "gpt-4": {
        "max_tokens": 8192,
        "context_window": 8192,
        "cost_per_1k_tokens": {"input": 0.03, "output": 0.06}
    },
    "gpt-4-32k": {
        "max_tokens": 32768,
        "context_window": 32768,
        "cost_per_1k_tokens": {"input": 0.06, "output": 0.12}
    },
    "gpt-3.5-turbo": {
        "max_tokens": 4096,
        "context_window": 4096,
        "cost_per_1k_tokens": {"input": 0.001, "output": 0.002}
    },
    "claude-3-sonnet": {
        "max_tokens": 4096,
        "context_window": 200000,
        "cost_per_1k_tokens": {"input": 0.003, "output": 0.015}
    }
}

def get_model_config(model_name: str) -> dict:
    """Get configuration for specific model"""
    return SUPPORTED_MODELS.get(model_name, SUPPORTED_MODELS["gpt-4"])