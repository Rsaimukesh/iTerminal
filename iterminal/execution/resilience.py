"""Error handling, resilience patterns, and recovery strategies."""
import time
import logging
from typing import Callable, Any, Optional, TypeVar, Union
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass


logger = logging.getLogger(__name__)
T = TypeVar("T")


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class ErrorCategory(Enum):
    """Categories of errors for handling."""
    NETWORK = "network"
    TIMEOUT = "timeout"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    RESOURCE = "resource"
    UNKNOWN = "unknown"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    expected_exception: type = Exception
    name: str = "default"


class CircuitBreaker:
    """Circuit breaker pattern implementation for fault tolerance."""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.success_count = 0
        
    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection."""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                logger.info(f"Circuit breaker '{self.config.name}' entering HALF_OPEN state")
            else:
                raise Exception(f"Circuit breaker '{self.config.name}' is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.last_failure_time is None:
            return False
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.config.recovery_timeout
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.success_count += 1
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
            logger.info(f"Circuit breaker '{self.config.name}' recovered to CLOSED")
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(
                f"Circuit breaker '{self.config.name}' is now OPEN "
                f"(failures: {self.failure_count})"
            )


class RetryConfig:
    """Configuration for retry logic."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        backoff_factor: float = 2.0,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True,
    ):
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.jitter = jitter


class Retry:
    """Retry logic with exponential backoff."""
    
    @staticmethod
    def execute(
        func: Callable[..., T],
        config: RetryConfig,
        *args,
        **kwargs
    ) -> T:
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(config.max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < config.max_attempts - 1:
                    delay = Retry._calculate_delay(attempt, config)
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {str(e)}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"All {config.max_attempts} attempts failed. "
                        f"Last error: {str(e)}"
                    )
        
        raise last_exception
    
    @staticmethod
    def _calculate_delay(attempt: int, config: RetryConfig) -> float:
        """Calculate delay with exponential backoff and optional jitter."""
        delay = config.initial_delay * (config.backoff_factor ** attempt)
        delay = min(delay, config.max_delay)
        
        if config.jitter:
            import random
            jitter_amount = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        return max(0, delay)


class ErrorHandler:
    """Centralized error handling and recovery."""
    
    def __init__(self):
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.error_counts: dict[str, int] = {}
    
    def categorize_error(self, exception: Exception) -> ErrorCategory:
        """Categorize error for appropriate handling."""
        error_str = str(exception).lower()
        error_type = type(exception).__name__.lower()
        
        if "timeout" in error_str or "timeout" in error_type:
            return ErrorCategory.TIMEOUT
        elif "connection" in error_str or "network" in error_str:
            return ErrorCategory.NETWORK
        elif "auth" in error_str or "permission" in error_str:
            return ErrorCategory.AUTHENTICATION
        elif "validation" in error_str or "invalid" in error_str:
            return ErrorCategory.VALIDATION
        elif "resource" in error_str or "memory" in error_str:
            return ErrorCategory.RESOURCE
        else:
            return ErrorCategory.UNKNOWN
    
    def get_recovery_action(self, category: ErrorCategory) -> str:
        """Get recommended recovery action for error category."""
        actions = {
            ErrorCategory.NETWORK: "Check network connection and retry",
            ErrorCategory.TIMEOUT: "Request timed out. Try again or increase timeout",
            ErrorCategory.AUTHENTICATION: "Authentication failed. Check credentials",
            ErrorCategory.VALIDATION: "Invalid input provided",
            ErrorCategory.RESOURCE: "Insufficient resources available",
            ErrorCategory.UNKNOWN: "Unknown error occurred",
        }
        return actions.get(category, "An error occurred")
    
    def get_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create circuit breaker for a component."""
        if name not in self.circuit_breakers:
            if config is None:
                config = CircuitBreakerConfig(name=name)
            self.circuit_breakers[name] = CircuitBreaker(config)
        return self.circuit_breakers[name]
    
    def track_error(self, component: str, exception: Exception) -> None:
        """Track error occurrences for monitoring."""
        if component not in self.error_counts:
            self.error_counts[component] = 0
        self.error_counts[component] += 1
        
        category = self.categorize_error(exception)
        logger.error(
            f"Error in {component}: {str(exception)} "
            f"(Category: {category.value}, Total: {self.error_counts[component]})"
        )
    
    def get_error_stats(self) -> dict[str, int]:
        """Get error statistics."""
        return dict(self.error_counts)
    
    def reset_error_stats(self) -> None:
        """Reset error statistics."""
        self.error_counts.clear()


# Global error handler instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get or create global error handler."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler
