"""Command models for representing terminal commands and their metadata."""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class CommandType(Enum):
    """Type of command."""
    SHELL = "shell"
    NATURAL_LANGUAGE = "natural_language"
    AI_GENERATED = "ai_generated"
    CORRECTED = "corrected"


class CommandStatus(Enum):
    """Status of command execution."""
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Command:
    """Represents a terminal command with metadata."""
    text: str
    command_type: CommandType
    timestamp: datetime = field(default_factory=datetime.now)
    status: CommandStatus = CommandStatus.PENDING
    
    # Execution details
    exit_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    execution_time: Optional[float] = None
    
    # AI-related metadata
    explanation: Optional[str] = None
    safety_score: Optional[float] = None
    complexity_level: Optional[str] = None
    suggested_alternatives: List[str] = field(default_factory=list)
    
    # Context
    working_directory: Optional[str] = None
    environment_vars: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert command to dictionary."""
        return {
            'text': self.text,
            'command_type': self.command_type.value,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status.value,
            'exit_code': self.exit_code,
            'stdout': self.stdout,
            'stderr': self.stderr,
            'execution_time': self.execution_time,
            'explanation': self.explanation,
            'safety_score': self.safety_score,
            'complexity_level': self.complexity_level,
            'suggested_alternatives': self.suggested_alternatives,
            'working_directory': self.working_directory,
            'environment_vars': self.environment_vars
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Command':
        """Create command from dictionary."""
        return cls(
            text=data['text'],
            command_type=CommandType(data['command_type']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            status=CommandStatus(data['status']),
            exit_code=data.get('exit_code'),
            stdout=data.get('stdout'),
            stderr=data.get('stderr'),
            execution_time=data.get('execution_time'),
            explanation=data.get('explanation'),
            safety_score=data.get('safety_score'),
            complexity_level=data.get('complexity_level'),
            suggested_alternatives=data.get('suggested_alternatives', []),
            working_directory=data.get('working_directory'),
            environment_vars=data.get('environment_vars', {})
        )


@dataclass
class Session:
    """Represents a terminal session."""
    session_id: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    commands: List[Command] = field(default_factory=list)
    
    # Statistics
    commands_executed: int = 0
    ai_queries: int = 0
    errors_encountered: int = 0
    
    def add_command(self, command: Command):
        """Add a command to this session."""
        self.commands.append(command)
        self.commands_executed += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'commands': [cmd.to_dict() for cmd in self.commands],
            'commands_executed': self.commands_executed,
            'ai_queries': self.ai_queries,
            'errors_encountered': self.errors_encountered
        }
