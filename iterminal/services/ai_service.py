"""AI service for managing AI provider interactions."""
import hashlib
from typing import Optional, List
from ..interfaces.ai_provider import AIProvider, CachedAIProvider
from ..config import get_ai_provider, CACHE_ENABLED


class AIService:
    """Service for managing AI interactions with multiple providers."""
    
    def __init__(self):
        self._providers: List[AIProvider] = []
        self._current_provider: Optional[AIProvider] = None
    
    def register_provider(self, provider: AIProvider):
        """Register an AI provider."""
        self._providers.append(provider)
        if not self._current_provider and provider.is_available():
            self._current_provider = provider
    
    def set_provider(self, provider_name: str) -> bool:
        """Set the current AI provider by name."""
        for provider in self._providers:
            if provider.get_name().lower() == provider_name.lower():
                if provider.is_available():
                    self._current_provider = provider
                    return True
                return False
        return False
    
    def get_current_provider(self) -> Optional[AIProvider]:
        """Get the currently active AI provider."""
        return self._current_provider
    
    def generate_response(self, prompt: str, system: str = None, use_cache: bool = True) -> Optional[str]:
        """
        Generate a response using the current AI provider.
        
        Args:
            prompt: The user's prompt
            system: Optional system message
            use_cache: Whether to use caching
            
        Returns:
            The AI-generated response or None
        """
        if not self._current_provider:
            return None
        
        # Try cache first if enabled
        if use_cache and CACHE_ENABLED and isinstance(self._current_provider, CachedAIProvider):
            cache_key = self._get_cache_key(prompt, system)
            cached = self._current_provider.get_cached_response(cache_key)
            if cached:
                return cached
        
        # Generate new response
        response = self._current_provider.generate_response(prompt, system)
        
        # Cache if enabled
        if response and use_cache and CACHE_ENABLED and isinstance(self._current_provider, CachedAIProvider):
            cache_key = self._get_cache_key(prompt, system)
            self._current_provider.cache_response(cache_key, response)
        
        return response
    
    def _get_cache_key(self, prompt: str, system: str = None) -> str:
        """Generate cache key for a prompt."""
        content = f"{system or ''}:{prompt}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def list_providers(self) -> List[str]:
        """List all registered providers."""
        return [p.get_name() for p in self._providers]
    
    def get_available_providers(self) -> List[str]:
        """List all available (ready to use) providers."""
        return [p.get_name() for p in self._providers if p.is_available()]
