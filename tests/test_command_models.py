"""Unit tests for command models."""
import unittest
from datetime import datetime
from iterminal.models.command import Command, CommandType, CommandStatus, Session


class TestCommand(unittest.TestCase):
    """Test cases for Command model."""
    
    def test_command_creation(self):
        """Test creating a command."""
        cmd = Command(
            text="ls -la",
            command_type=CommandType.SHELL
        )
        
        self.assertEqual(cmd.text, "ls -la")
        self.assertEqual(cmd.command_type, CommandType.SHELL)
        self.assertEqual(cmd.status, CommandStatus.PENDING)
    
    def test_command_to_dict(self):
        """Test command serialization to dict."""
        cmd = Command(
            text="pwd",
            command_type=CommandType.SHELL,
            exit_code=0,
            stdout="/home/user"
        )
        
        data = cmd.to_dict()
        
        self.assertEqual(data['text'], "pwd")
        self.assertEqual(data['command_type'], "shell")
        self.assertEqual(data['exit_code'], 0)
        self.assertEqual(data['stdout'], "/home/user")
    
    def test_command_from_dict(self):
        """Test command deserialization from dict."""
        data = {
            'text': 'echo test',
            'command_type': 'shell',
            'timestamp': datetime.now().isoformat(),
            'status': 'success',
            'exit_code': 0
        }
        
        cmd = Command.from_dict(data)
        
        self.assertEqual(cmd.text, 'echo test')
        self.assertEqual(cmd.command_type, CommandType.SHELL)
        self.assertEqual(cmd.status, CommandStatus.SUCCESS)


class TestSession(unittest.TestCase):
    """Test cases for Session model."""
    
    def test_session_creation(self):
        """Test creating a session."""
        session = Session(session_id="test-123")
        
        self.assertEqual(session.session_id, "test-123")
        self.assertEqual(session.commands_executed, 0)
        self.assertEqual(len(session.commands), 0)
    
    def test_add_command(self):
        """Test adding commands to session."""
        session = Session(session_id="test-123")
        cmd = Command(text="ls", command_type=CommandType.SHELL)
        
        session.add_command(cmd)
        
        self.assertEqual(len(session.commands), 1)
        self.assertEqual(session.commands_executed, 1)
    
    def test_session_to_dict(self):
        """Test session serialization."""
        session = Session(session_id="test-123")
        cmd = Command(text="pwd", command_type=CommandType.SHELL)
        session.add_command(cmd)
        
        data = session.to_dict()
        
        self.assertEqual(data['session_id'], "test-123")
        self.assertEqual(data['commands_executed'], 1)
        self.assertEqual(len(data['commands']), 1)


if __name__ == '__main__':
    unittest.main()
