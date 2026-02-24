"""Dependency injection container and context factory."""
import logging
from typing import Dict, Any, Optional, Type, TypeVar
from iterminal.config import Settings, get_settings
from iterminal.execution import ExecutorPool, get_error_handler
from iterminal.completion import AutoCompleter


logger = logging.getLogger(__name__)
T = TypeVar("T")


class ApplicationContext:
    """Dependency injection container for the application."""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}
        self._singletons: Dict[str, Any] = {}
        
        # Register core services
        self._register_core_services()
    
    def _register_core_services(self) -> None:
        """Register built-in services."""
        # Error handler
        self.register_singleton("error_handler", get_error_handler())
        
        # Executor pool
        executor_pool = ExecutorPool.get_instance(
            thread_count=self.settings.performance.thread_count,
            process_count=self.settings.performance.process_count
        )
        executor_pool.initialize()
        self.register_singleton("executor_pool", executor_pool)
        
        # Autocompleter
        completer_config = {
            "enabled": self.settings.completion.enabled,
            "fuzzy_matching": self.settings.completion.fuzzy_matching,
            "history_based": self.settings.completion.history_based,
            "max_suggestions": self.settings.completion.max_suggestions,
            "ignore_case": self.settings.completion.ignore_case,
        }
        self.register_singleton("autocompleter", AutoCompleter(completer_config))
        
        logger.info("Core services registered")
    
    def register(self, name: str, service: Any) -> None:
        """Register a service."""
        self._services[name] = service
        logger.debug(f"Service registered: {name}")
    
    def register_singleton(self, name: str, service: Any) -> None:
        """Register a singleton service."""
        self._singletons[name] = service
        logger.debug(f"Singleton registered: {name}")
    
    def register_factory(self, name: str, factory: callable) -> None:
        """Register a factory function."""
        self._factories[name] = factory
        logger.debug(f"Factory registered: {name}")
    
    def get(self, name: str) -> Any:
        """Get a service by name."""
        # Check singletons first
        if name in self._singletons:
            return self._singletons[name]
        
        # Check factories
        if name in self._factories:
            service = self._factories[name](self)
            self._singletons[name] = service  # Cache factory result
            return service
        
        # Check services
        if name in self._services:
            return self._services[name]
        
        raise KeyError(f"Service '{name}' not registered")
    
    def get_or_none(self, name: str) -> Optional[Any]:
        """Get a service or None if not found."""
        try:
            return self.get(name)
        except KeyError:
            return None
    
    def get_settings(self) -> Settings:
        """Get application settings."""
        return self.settings
    
    def get_error_handler(self):
        """Get error handler."""
        return self.get("error_handler")
    
    def get_executor_pool(self) -> ExecutorPool:
        """Get executor pool."""
        return self.get("executor_pool")
    
    def get_autocompleter(self) -> AutoCompleter:
        """Get autocompleter."""
        return self.get("autocompleter")
    
    def shutdown(self) -> None:
        """Shutdown all services."""
        logger.info("Shutting down application context")
        
        # Shutdown executor pool
        try:
            executor_pool = self.get_or_none("executor_pool")
            if executor_pool:
                executor_pool.shutdown(wait=True)
        except Exception as e:
            logger.error(f"Error shutting down executor pool: {e}")
        
        # Clear singletons
        self._singletons.clear()
        self._services.clear()
        self._factories.clear()


# Global context instance
_context: Optional[ApplicationContext] = None


def get_application_context(settings: Optional[Settings] = None) -> ApplicationContext:
    """Get or create global application context."""
    global _context
    if _context is None:
        _context = ApplicationContext(settings)
    return _context


def create_application_context(settings: Optional[Settings] = None) -> ApplicationContext:
    """Create a new application context (useful for testing)."""
    return ApplicationContext(settings)


def shutdown_application_context() -> None:
    """Shutdown global application context."""
    global _context
    if _context is not None:
        _context.shutdown()
        _context = None
