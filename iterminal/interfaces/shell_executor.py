"""Abstract interface for shell command execution."""
from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class CommandResult:
    """Result of a command execution."""
    command: str
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    success: bool


class ShellExecutor(ABC):
    """Abstract base class for shell command executors."""
    
    @abstractmethod
    def execute(self, command: str, timeout: Optional[int] = None) -> CommandResult:
        """
        Execute a shell command.
        
        Args:
            command: The command to execute
            timeout: Optional timeout in seconds
            
        Returns:
            CommandResult with execution details
        """
        pass
    
    @abstractmethod
    def is_safe_command(self, command: str) -> bool:
        """Check if a command is safe to execute."""
        pass
    
    @abstractmethod
    def validate_command(self, command: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a command before execution.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
