"""Utility functions for command detection and path handling"""
import os
import shutil
import subprocess
from typing import List, Tuple, Optional

# Common system paths to check for commands
SYSTEM_PATHS = [
    '/usr/bin/',
    '/bin/',
    '/usr/sbin/',
    '/sbin/',
    '/usr/local/bin/',
    '/usr/local/sbin/'
]

# System commands that are often installed but might not be in PATH
SYSTEM_COMMANDS = {
    'apt': '/usr/bin/apt',
    'apt-get': '/usr/bin/apt-get',
    'yum': '/usr/bin/yum',
    'dnf': '/usr/bin/dnf',
    'pacman': '/usr/bin/pacman',
    'rpm': '/usr/bin/rpm',
    'dpkg': '/usr/bin/dpkg',
    'systemctl': '/usr/bin/systemctl',
    'sudo': '/usr/bin/sudo',
    'ssh': '/usr/bin/ssh',
    'docker': '/usr/bin/docker',
    'podman': '/usr/bin/podman',
    'flatpak': '/usr/bin/flatpak',
    'snap': '/usr/bin/snap',
    'ip': '/usr/sbin/ip'
}

def command_exists(cmd: str) -> bool:
    """
    Check if a command exists, using multiple methods for reliability.
    
    Args:
        cmd: The command to check
        
    Returns:
        bool: True if the command exists, False otherwise
    """
    # Method 1: Check with shutil.which
    if shutil.which(cmd) is not None:
        return True
    
    # Method 2: Check common system paths
    for path in SYSTEM_PATHS:
        if os.path.exists(path + cmd):
            return True
    
    # Method 3: Check known system commands
    if cmd in SYSTEM_COMMANDS and os.path.exists(SYSTEM_COMMANDS[cmd]):
        return True
    
    # Method 4: Last resort, try running it directly
    try:
        # Use a harmless flag like --version or --help to check if it exists
        result = subprocess.run([cmd, '--version'], 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE, 
                                timeout=0.5)  # Short timeout
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        try:
            # Try --help as an alternative
            result = subprocess.run([cmd, '--help'], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE, 
                                    timeout=0.5)
            return result.returncode == 0 or result.returncode == 1  # Some commands return 1 for help
        except:
            pass
    
    return False

def get_command_path(cmd: str) -> Optional[str]:
    """Get the full path to a command"""
    # Use shutil.which first
    path = shutil.which(cmd)
    if path:
        return path
    
    # Check common system paths
    for sys_path in SYSTEM_PATHS:
        full_path = sys_path + cmd
        if os.path.exists(full_path):
            return full_path
    
    # Check known system commands
    if cmd in SYSTEM_COMMANDS and os.path.exists(SYSTEM_COMMANDS[cmd]):
        return SYSTEM_COMMANDS[cmd]
    
    return None

def is_sudo_available() -> bool:
    """Check if sudo is available in the system"""
    return command_exists('sudo')

def sudo_run_test() -> Tuple[bool, str]:
    """Test if sudo can be run without issues"""
    if not is_sudo_available():
        return False, "sudo not found"
    
    try:
        # Try a harmless sudo command
        result = subprocess.run(['sudo', '-n', 'true'], 
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               timeout=1)
        if result.returncode == 0:
            return True, "sudo available and working"
        else:
            stderr = result.stderr.decode('utf-8', errors='replace')
            return False, f"sudo found but might require password: {stderr.strip()}"
    except Exception as e:
        return False, f"sudo error: {str(e)}"
        
def is_git_command(command: str) -> bool:
    """Check if a command is a git command
    
    Args:
        command: The command string to check
    
    Returns:
        bool: True if this is a git command, False otherwise
    """
    command = command.strip()
    
    # Check if command starts with "git" followed by a space or nothing
    if command.startswith("git ") or command == "git":
        return True
        
    return False

def extract_git_subcommand(command: str) -> str:
    """Extract the git subcommand from a git command
    
    Args:
        command: The git command string
        
    Returns:
        str: The git subcommand or empty string if not found
    """
    command = command.strip()
    
    if command == "git":
        # Just "git" command with no subcommand
        return "git"
    
    if not command.startswith("git "):
        return ""
        
    parts = command.split()
    if len(parts) >= 2:
        # Return "git subcommand" format
        return f"git {parts[1]}"
    else:
        # Just "git" command (should be handled by first condition)
        return "git"
