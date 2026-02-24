"""Centralized configuration management for iTerminal."""
import os
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


class AIProviderType(Enum):
    """Supported AI providers."""
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"
    AUTO = "auto"  # Auto-select based on availability


class LogLevel(Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class PerformanceConfig:
    """Performance tuning settings."""
    hyperthread_enabled: bool = True
    parallel_requests: int = 4
    thread_count: int = 16
    process_count: int = 2
    cache_enabled: bool = True
    cache_duration: int = 7200  # 2 hours
    request_timeout: int = 60
    max_concurrent_tasks: int = 32
    
    @classmethod
    def from_env(cls) -> "PerformanceConfig":
        """Load from environment variables."""
        return cls(
            hyperthread_enabled=os.getenv("ITERMINAL_HYPERTHREAD", "1") == "1",
            parallel_requests=int(os.getenv("ITERMINAL_PARALLEL_REQUESTS", "4")),
            thread_count=int(os.getenv("ITERMINAL_THREAD_COUNT", "16")),
            process_count=int(os.getenv("ITERMINAL_PROCESS_COUNT", "2")),
            cache_enabled=os.getenv("ITERMINAL_CACHE_ENABLED", "1") == "1",
            cache_duration=int(os.getenv("ITERMINAL_CACHE_DURATION", "7200")),
            request_timeout=int(os.getenv("ITERMINAL_REQUEST_TIMEOUT", "60")),
            max_concurrent_tasks=int(os.getenv("ITERMINAL_MAX_CONCURRENT_TASKS", "32")),
        )


@dataclass
class AIConfig:
    """AI provider configuration."""
    provider: AIProviderType = AIProviderType.AUTO
    openrouter_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"
    fallback_providers: List[AIProviderType] = field(
        default_factory=lambda: [AIProviderType.OLLAMA, AIProviderType.OPENROUTER]
    )
    retry_attempts: int = 3
    retry_backoff_factor: float = 2.0
    
    @classmethod
    def from_env(cls) -> "AIConfig":
        """Load from environment variables."""
        provider_str = os.getenv("ITERMINAL_AI_PROVIDER", "auto").lower()
        try:
            provider = AIProviderType(provider_str)
        except ValueError:
            provider = AIProviderType.AUTO
        
        return cls(
            provider=provider,
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "llama2"),
            retry_attempts=int(os.getenv("ITERMINAL_RETRY_ATTEMPTS", "3")),
            retry_backoff_factor=float(os.getenv("ITERMINAL_RETRY_BACKOFF", "2.0")),
        )


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: LogLevel = LogLevel.INFO
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    console_output: bool = True
    structured_logging: bool = True
    
    @classmethod
    def from_env(cls) -> "LoggingConfig":
        """Load from environment variables."""
        level_str = os.getenv("ITERMINAL_LOG_LEVEL", "INFO").upper()
        try:
            level = LogLevel[level_str]
        except KeyError:
            level = LogLevel.INFO
        
        return cls(
            level=level,
            file_path=os.getenv("ITERMINAL_LOG_FILE"),
            console_output=os.getenv("ITERMINAL_CONSOLE_LOG", "1") == "1",
            structured_logging=os.getenv("ITERMINAL_STRUCTURED_LOG", "1") == "1",
        )


@dataclass
class CompletionConfig:
    """Autocomplete and tab completion configuration."""
    enabled: bool = True
    fuzzy_matching: bool = True
    history_based: bool = True
    ai_suggestions: bool = True
    max_suggestions: int = 10
    suggestion_delay_ms: int = 100
    cache_suggestions: bool = True
    ignore_case: bool = True
    
    @classmethod
    def from_env(cls) -> "CompletionConfig":
        """Load from environment variables."""
        return cls(
            enabled=os.getenv("ITERMINAL_COMPLETION", "1") == "1",
            fuzzy_matching=os.getenv("ITERMINAL_FUZZY_MATCH", "1") == "1",
            history_based=os.getenv("ITERMINAL_HISTORY_COMPLETE", "1") == "1",
            ai_suggestions=os.getenv("ITERMINAL_AI_SUGGESTIONS", "1") == "1",
            max_suggestions=int(os.getenv("ITERMINAL_MAX_SUGGESTIONS", "10")),
            suggestion_delay_ms=int(os.getenv("ITERMINAL_SUGGESTION_DELAY", "100")),
            cache_suggestions=os.getenv("ITERMINAL_CACHE_SUGGESTIONS", "1") == "1",
            ignore_case=os.getenv("ITERMINAL_IGNORE_CASE", "1") == "1",
        )


@dataclass
class UIConfig:
    """UI/Theme configuration."""
    theme: str = "default"
    colors_enabled: bool = True
    unicode_enabled: bool = True
    animation_enabled: bool = True
    progress_bar_enabled: bool = True
    
    @classmethod
    def from_env(cls) -> "UIConfig":
        """Load from environment variables."""
        return cls(
            theme=os.getenv("ITERMINAL_THEME", "default"),
            colors_enabled=os.getenv("ITERMINAL_COLORS", "1") == "1",
            unicode_enabled=os.getenv("ITERMINAL_UNICODE", "1") == "1",
            animation_enabled=os.getenv("ITERMINAL_ANIMATION", "1") == "1",
            progress_bar_enabled=os.getenv("ITERMINAL_PROGRESS_BAR", "1") == "1",
        )


@dataclass
class SecurityConfig:
    """Security settings."""
    safe_mode: bool = True
    require_confirmation: bool = True
    max_command_length: int = 10000
    whitelist_commands: Optional[List[str]] = None
    blacklist_commands: Optional[List[str]] = None
    
    @classmethod
    def from_env(cls) -> "SecurityConfig":
        """Load from environment variables."""
        whitelist = os.getenv("ITERMINAL_WHITELIST_COMMANDS")
        blacklist = os.getenv("ITERMINAL_BLACKLIST_COMMANDS")
        
        return cls(
            safe_mode=os.getenv("ITERMINAL_SAFE_MODE", "1") == "1",
            require_confirmation=os.getenv("ITERMINAL_CONFIRM", "1") == "1",
            max_command_length=int(os.getenv("ITERMINAL_MAX_CMD_LEN", "10000")),
            whitelist_commands=whitelist.split(",") if whitelist else None,
            blacklist_commands=blacklist.split(",") if blacklist else None,
        )


class Settings:
    """Master settings class - single point of configuration."""
    
    def __init__(self):
        self.performance = PerformanceConfig.from_env()
        self.ai = AIConfig.from_env()
        self.logging = LoggingConfig.from_env()
        self.completion = CompletionConfig.from_env()
        self.ui = UIConfig.from_env()
        self.security = SecurityConfig.from_env()
    
    @classmethod
    def create(cls) -> "Settings":
        """Factory method to create Settings instance."""
        return cls()
    
    def to_dict(self) -> dict:
        """Convert settings to dictionary for logging/debugging."""
        return {
            "performance": self.performance.__dict__,
            "ai": {k: v for k, v in self.ai.__dict__.items() if k != "openrouter_api_key"},
            "logging": self.logging.__dict__,
            "completion": self.completion.__dict__,
            "ui": self.ui.__dict__,
            "security": self.security.__dict__,
        }


# Global settings instance (singleton pattern)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings.create()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global _settings
    _settings = Settings.create()
    return _settings
