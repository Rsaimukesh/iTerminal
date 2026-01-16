"""Abstract interface for AI providers to enable pluggable AI backends."""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    def generate_response(self, prompt: str, system: str = None, **kwargs) -> Optional[str]:
        """
        Generate a response from the AI model.
        
        Args:
            prompt: The user's prompt
            system: Optional system message for context
            **kwargs: Additional provider-specific parameters
            
        Returns:
            The AI-generated response or None if failed
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the AI provider is available and ready to use."""
        pass
    
    @abstractmethod
    def get_models(self) -> List[str]:
        """Get list of available models from this provider."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the name of this AI provider."""
        pass


class CachedAIProvider(AIProvider):
    """Base class for AI providers with caching support."""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def get_cached_response(self, cache_key: str) -> Optional[str]:
        """Get cached response if available."""
        if cache_key in self._cache:
            import time
            cache_entry = self._cache[cache_key]
            if time.time() - cache_entry['timestamp'] < 7200:  # 2 hours
                return cache_entry['response']
            else:
                del self._cache[cache_key]
        return None
    
    def cache_response(self, cache_key: str, response: str):
        """Cache a response."""
        import time
        self._cache[cache_key] = {
            'response': response,
            'timestamp': time.time()
        }
