"""Integration adapter to use new config system in existing code."""
from iterminal.config import get_settings


class ConfigAdapter:
    """Adapter to convert new Settings to legacy config format."""
    
    @staticmethod
    def get_api_key() -> str:
        """Get API key from new config system."""
        settings = get_settings()
        return settings.ai.openrouter_api_key or ""
    
    @staticmethod
    def get_ai_provider() -> str:
        """Get AI provider from new config system."""
        settings = get_settings()
        return settings.ai.provider.value
    
    @staticmethod
    def get_ollama_base_url() -> str:
        """Get Ollama base URL from new config system."""
        settings = get_settings()
        return settings.ai.ollama_base_url
    
    @staticmethod
    def get_ollama_model() -> str:
        """Get Ollama model from new config system."""
        settings = get_settings()
        return settings.ai.ollama_model
    
    @staticmethod
    def is_cache_enabled() -> bool:
        """Check if caching is enabled."""
        settings = get_settings()
        return settings.performance.cache_enabled
    
    @staticmethod
    def get_cache_duration() -> int:
        """Get cache duration in seconds."""
        settings = get_settings()
        return settings.performance.cache_duration
    
    @staticmethod
    def get_thread_count() -> int:
        """Get number of threads."""
        settings = get_settings()
        return settings.performance.thread_count
    
    @staticmethod
    def get_process_count() -> int:
        """Get number of processes."""
        settings = get_settings()
        return settings.performance.process_count
    
    @staticmethod
    def is_hyperthread_enabled() -> bool:
        """Check if hyperthreading is enabled."""
        settings = get_settings()
        return settings.performance.hyperthread_enabled
    
    @staticmethod
    def get_parallel_requests() -> int:
        """Get number of parallel requests."""
        settings = get_settings()
        return settings.performance.parallel_requests
    
    @staticmethod
    def get_request_timeout() -> int:
        """Get request timeout in seconds."""
        settings = get_settings()
        return settings.performance.request_timeout
    
    @staticmethod
    def is_safe_mode_enabled() -> bool:
        """Check if safe mode is enabled."""
        settings = get_settings()
        return settings.security.safe_mode
    
    @staticmethod
    def requires_confirmation() -> bool:
        """Check if command confirmation is required."""
        settings = get_settings()
        return settings.security.require_confirmation


# Export adapter functions for backward compatibility
def get_api_key() -> str:
    """Legacy function - use ConfigAdapter instead."""
    return ConfigAdapter.get_api_key()


def get_ai_provider() -> str:
    """Legacy function - use ConfigAdapter instead."""
    return ConfigAdapter.get_ai_provider()


OLLAMA_BASE_URL = "http://localhost:11434"  # Legacy - will be overridden
OLLAMA_MODEL = "llama2"  # Legacy - will be overridden


def _update_legacy_constants():
    """Update legacy constants from new config."""
    global OLLAMA_BASE_URL, OLLAMA_MODEL
    OLLAMA_BASE_URL = ConfigAdapter.get_ollama_base_url()
    OLLAMA_MODEL = ConfigAdapter.get_ollama_model()


# Initialize legacy constants on import
_update_legacy_constants()
