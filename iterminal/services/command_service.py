"""Command service for managing command execution and history."""
from typing import List, Optional
from ..models.command import Command, CommandStatus, CommandType, Session
from ..interfaces.shell_executor import ShellExecutor, CommandResult
from datetime import datetime
import uuid


class CommandService:
    """Service for managing command execution and history."""
    
    def __init__(self, shell_executor: ShellExecutor):
        self._executor = shell_executor
        self._current_session: Optional[Session] = None
        self._sessions: List[Session] = []
    
    def start_session(self) -> Session:
        """Start a new terminal session."""
        session = Session(
            session_id=str(uuid.uuid4()),
            start_time=datetime.now()
        )
        self._current_session = session
        self._sessions.append(session)
        return session
    
    def end_session(self):
        """End the current session."""
        if self._current_session:
            self._current_session.end_time = datetime.now()
            self._current_session = None
    
    def execute_command(self, command: Command, timeout: Optional[int] = None) -> CommandResult:
        """
        Execute a command and update its metadata.
        
        Args:
            command: The command to execute
            timeout: Optional timeout in seconds
            
        Returns:
            CommandResult with execution details
        """
        command.status = CommandStatus.EXECUTING
        
        result = self._executor.execute(command.text, timeout)
        
        # Update command with results
        command.exit_code = result.exit_code
        command.stdout = result.stdout
        command.stderr = result.stderr
        command.execution_time = result.execution_time
        command.status = CommandStatus.SUCCESS if result.success else CommandStatus.FAILED
        
        # Add to current session
        if self._current_session:
            self._current_session.add_command(command)
            if not result.success:
                self._current_session.errors_encountered += 1
        
        return result
    
    def validate_command(self, command_text: str) -> tuple[bool, Optional[str]]:
        """Validate a command before execution."""
        return self._executor.validate_command(command_text)
    
    def is_safe_command(self, command_text: str) -> bool:
        """Check if a command is safe to execute."""
        return self._executor.is_safe_command(command_text)
    
    def get_command_history(self, limit: Optional[int] = None) -> List[Command]:
        """Get command history from current session."""
        if not self._current_session:
            return []
        
        commands = self._current_session.commands
        if limit:
            return commands[-limit:]
        return commands
    
    def get_session_stats(self) -> dict:
        """Get statistics for the current session."""
        if not self._current_session:
            return {}
        
        return {
            'commands_executed': self._current_session.commands_executed,
            'ai_queries': self._current_session.ai_queries,
            'errors_encountered': self._current_session.errors_encountered,
            'session_duration': (datetime.now() - self._current_session.start_time).total_seconds()
        }
