import subprocess
import shlex
import shutil
import re
import os
import time
from .config import FILTER_APT_WARNINGS
from .command_utils import command_exists, get_command_path, is_sudo_available, sudo_run_test

# Import performance monitoring if available
try:
    from .performance import timing_decorator
except ImportError:
    # Fallback decorator if performance module isn't available
    def timing_decorator(func):
        return func

# Use frozenset for O(1) lookup instead of set/dict for immutable collections
INTERACTIVE_COMMANDS = frozenset({
    'nano', 'vim', 'vi', 'emacs', 'less', 'more', 'top', 'htop', 
    'man', 'info', 'ssh', 'telnet', 'ftp', 'sftp', 'screen', 'tmux'
})

INPUT_WAITING_COMMANDS = frozenset({
    'cat', 'tee', 'read', 'mail', 'write', 'wall'
})

# Use dict for O(1) lookup of alternatives
COMMAND_ALTERNATIVES = {
    'nano': 'cat',
    'vim': 'cat',
    'vi': 'cat',
    'emacs': 'cat',
    'less': 'cat',
    'more': 'cat',
    'top': 'ps aux',
    'htop': 'ps aux',
    'man': 'apropos',
    'info': 'apropos'
}

# Use frozenset for common commands (O(1) lookup)
COMMON_COMMANDS = frozenset({
    "ls", "pwd", "cd", "cat", "grep", "echo", "find", "rm", "cp", "mv", "touch", "mkdir", "rmdir",
    "apt", "apt-get", "yum", "dnf", "pacman", "curl", "wget", "sudo", "chmod", "chown", 
    "ps", "top", "git", "ssh", "scp", "ping", "ifconfig", "ip", "netstat", "tar", "zip", "unzip", 
    "man", "nano", "vim", "less", "more", "head", "tail", "wc", "sort", "uniq", "awk", "sed", 
    "cut", "diff", "xargs"
})

UPPERCASE_COMMANDS = frozenset({"COPY", "MAIL", "TIME", "ECHO", "CC", "MC"})

# Compile regex patterns once for better performance
DANGEROUS_PATTERNS = [
    re.compile(r'rm\s+-rf\s+/', re.IGNORECASE),
    re.compile(r'dd\s+if=/dev/zero', re.IGNORECASE),
    re.compile(r'\bmkfs\b', re.IGNORECASE),
    re.compile(r'\bfdisk\b', re.IGNORECASE),
    re.compile(r'\bshutdown\b', re.IGNORECASE),
    re.compile(r'\breboot\b', re.IGNORECASE)
]

# Use tuple for permission error strings (immutable, faster than list)
PERMISSION_ERRORS = (
    'permission denied', 'not permitted', 'operation not permitted',
    'could not open lock file', 'unable to lock directory'
)

# Cache for command descriptions
COMMON_SUDO_CMDS = {
    'apt': 'package management',
    'apt-get': 'package management',
    'dpkg': 'package management',
    'yum': 'package management',
    'dnf': 'package management',
    'pacman': 'package management',
    'zypper': 'package management',
    'systemctl': 'service management',
    'service': 'service control',
    'mount': 'disk mounting',
    'umount': 'disk unmounting',
    'fdisk': 'disk partitioning',
    'mkfs': 'filesystem creation',
    'chown': 'change file ownership',
    'chmod': 'change file permissions'
}

NON_SUDO_ALTERNATIVES = {
    'apt': ('apt list', 'apt search', 'apt show'),
    'apt-get': ('apt-cache search', 'apt-cache show'),
    'yum': ('yum list', 'yum search', 'repoquery'),
    'dnf': ('dnf list', 'dnf search', 'dnf repoquery'),
    'pacman': ('pacman -Ss', 'pacman -Qi'),
}


def is_probably_shell_command(user_input: str) -> bool:
    """Check if input looks like a shell command."""
    stripped = user_input.strip()
    
    # Special case for git commands - always treat as shell command
    if stripped.startswith("git ") or stripped == "git":
        return True
        
    # Regular shell command detection
    return bool(stripped and not stripped[0].isalpha())


def is_interactive_command(cmd: str) -> bool:
    """Check if command is interactive using O(1) frozenset lookup."""
    return cmd in INTERACTIVE_COMMANDS


def is_input_waiting_command(cmd: str) -> bool:
    """Check if command waits for input using O(1) frozenset lookup."""
    return cmd in INPUT_WAITING_COMMANDS


def get_command_alternative(cmd: str) -> str:
    """Get alternative for interactive command using O(1) dict lookup."""
    return COMMAND_ALTERNATIVES.get(cmd, cmd)


def filter_apt_warning(stderr: str) -> str:
    """Filter out common apt warnings about unstable CLI interface."""
    if not FILTER_APT_WARNINGS or "WARNING: apt does not have a stable CLI interface" not in stderr:
        return stderr
    
    # Use list comprehension for efficient filtering
    return '\n'.join(
        line for line in stderr.splitlines() 
        if "WARNING: apt does not have a stable CLI interface" not in line
    )


def normalize_command_case(cmd: str) -> str:
    """Normalize command case if caps lock is detected."""
    if not cmd.strip():
        return cmd
    
    first_word = cmd.split(None, 1)[0]  # More efficient than strip().split()[0]
    first_word_lower = first_word.lower()
    
    # Early return if command is meant to be uppercase
    if first_word in UPPERCASE_COMMANDS:
        return cmd
    
    # Check if it's a common command that needs case normalization
    if first_word_lower in COMMON_COMMANDS:
        # All caps or first letter caps
        if first_word.isupper() or (first_word[0].isupper() and len(first_word) > 1):
            return first_word_lower + cmd[len(first_word):]
    
    return cmd


def is_dangerous_command(cmd: str) -> bool:
    """Check if command matches dangerous patterns using pre-compiled regex."""
    return any(pattern.search(cmd) for pattern in DANGEROUS_PATTERNS)


def execute_subprocess(cmd: str) -> tuple:
    """Execute command and return (returncode, stdout, stderr)."""
    try:
        process = subprocess.Popen(
            cmd, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        stdout, stderr = process.communicate()
        stderr = filter_apt_warning(stderr)
        return process.returncode, stdout, stderr
    except Exception as e:
        return -1, '', str(e)


def handle_ssudo_command(cmd: str) -> tuple:
    """Deprecated - now just forwards to normal sudo command handling."""
    # Just treat it as a regular sudo command, replacing ssudo with sudo
    cmd_without_ssudo = cmd[6:].strip()  # Remove 'ssudo ' prefix
    
    if not cmd_without_ssudo:
        return 0, "", ""
    
    # Redirect to normal sudo handling
    return run_shell_command(f'sudo {cmd_without_ssudo}')


def build_command_not_found_message(base_command: str) -> tuple:
    """Build error message for command not found."""
    message_parts = [
        f"⚠️ Command '{base_command}' not found in this environment.\n",
        "This could be because:",
        "1. The command is not installed",
        "2. You're in a restricted environment (container/sandbox)",
        "3. The command is not in your PATH\n"
    ]
    
    # Add alternatives if available
    if base_command in NON_SUDO_ALTERNATIVES:
        message_parts.append("Some non-privileged alternatives that might work:")
        message_parts.extend(f"- {alt}" for alt in NON_SUDO_ALTERNATIVES[base_command])
        message_parts.append("")
    
    # Add distribution-specific help
    if base_command in ('apt', 'apt-get', 'dpkg'):
        message_parts.extend([
            f"For Debian/Ubuntu systems, you might need to:",
            f"1. Exit iTerminal and run: sudo apt install {base_command}",
            f"2. Or if in Flatpak: flatpak-spawn --host sudo apt install {base_command}"
        ])
    elif base_command in ('yum', 'dnf'):
        message_parts.extend([
            f"For Red Hat/Fedora systems, you might need to:",
            f"1. Exit iTerminal and run: sudo dnf install {base_command}",
            f"2. Or if in Flatpak: flatpak-spawn --host sudo dnf install {base_command}"
        ])
    
    message_parts.append(
        "\nNote: Using 'sudo' instead of 'ssudo' won't help if the command isn't installed."
        "\nAvoiding circular suggestion between sudo and ssudo."
    )
    
    return 127, '', '\n'.join(message_parts)


def build_permission_denied_message(base_command: str, cmd: str, stderr: str) -> str:
    """Build error message for permission denied."""
    message_parts = [
        f"{stderr}\n",
        f"⚠️ Permission denied: This command requires root privileges, but 'sudo' is not available "
        f"in this environment.\n",
        f"To run {base_command} with elevated permissions, you might need to:",
        f"1. Exit iTerminal and use your regular terminal with sudo",
        f"2. Use your host system's terminal (if in a container/sandbox)"
    ]
    
    # Add Flatpak-specific advice if detected
    if os.path.exists('/usr/bin/flatpak-spawn') or os.path.exists('/app/bin/flatpak-spawn'):
        message_parts.extend([
            "\n💡 Flatpak detected: Try this command instead:",
            f"   flatpak-spawn --host sudo {cmd}"
        ])
    
    return '\n'.join(message_parts)


@timing_decorator
def run_shell_command(cmd: str) -> tuple:
    """
    Execute shell command with proper handling for different command types.
    Returns: (returncode, stdout, stderr)
    """
    # Normalize command case
    cmd = normalize_command_case(cmd)
    
    # Plugin mode: allow all commands except dangerous ones
    from .config import PLUGIN_MODE
    if PLUGIN_MODE:
        if is_dangerous_command(cmd):
            return -1, '', f"Command '{cmd}' is blocked in plugin mode: dangerous operation."
        return execute_subprocess(cmd)
    
    tokens = cmd.strip().split()
    if not tokens:
        return 0, "", ""
    
    first_token = tokens[0].lower()
    
    # Auto-translate package manager commands in Flatpak/container environments
    package_managers = ['apt', 'apt-get', 'dnf', 'yum', 'pacman']
    if first_token in package_managers or (first_token == 'sudo' and len(tokens) > 1 and tokens[1] in package_managers):
        # Check if we're in a Flatpak/container environment
        if os.path.exists('/usr/bin/flatpak-spawn') or os.path.exists('/app/bin/flatpak-spawn'):
            # Auto-translate to flatpak-spawn command
            original_cmd = cmd
            # Use pkexec instead of sudo for GUI password prompts in Flatpak
            if first_token == 'sudo':
                # Replace sudo with pkexec for better GUI integration
                cmd_without_sudo = ' '.join(tokens[1:])
                cmd = f"flatpak-spawn --host pkexec {cmd_without_sudo}"
            else:
                cmd = f"flatpak-spawn --host pkexec {cmd}"
            print(f"Auto-translating package manager command:")
            print(f"  {original_cmd}")
            print(f"  → {cmd}")
            print(f"  Using pkexec for GUI authentication on host system\n")
            tokens = cmd.strip().split()
            first_token = tokens[0].lower()
    
    # Convert ssudo command to sudo command for compatibility
    if first_token == 'ssudo':
        # Replace ssudo with sudo and process as a regular sudo command
        sudo_cmd = 'sudo' + cmd[5:]
        return run_shell_command(sudo_cmd)
    
    # Handle sudo commands by silently running the command without sudo if sudo doesn't exist
    if first_token == 'sudo':
        # Check if sudo is actually available
        if not command_exists('sudo'):
            # If sudo doesn't exist, strip the sudo prefix and run the command directly
            cmd_without_sudo = ' '.join(tokens[1:]) if len(tokens) > 1 else ""
            if not cmd_without_sudo:
                return 0, "", "No command specified after sudo."
            # No note or warning - silently execute without sudo
            return execute_subprocess(cmd_without_sudo)
        # If sudo exists, execute normally
        return execute_subprocess(cmd)
    
    # Handle interactive commands
    if is_interactive_command(first_token):
        alt_cmd = get_command_alternative(first_token)
        if alt_cmd != first_token:
            cmd = f"{alt_cmd} {' '.join(tokens[1:])}"
            print(f"Note: '{first_token}' is an interactive command, using '{alt_cmd}' instead.")
    
    # Fast Git handling - special optimized path for git commands
    if first_token == 'git':
        # Set environment variable to improve Git performance
        env = os.environ.copy()
        
        # Speed up git commands by disabling expensive operations
        if len(tokens) > 1 and tokens[1] in ['status', 'log', 'diff', 'branch', 'ls-files']:
            # These operations benefit from performance tweaks
            env['GIT_TRACE'] = '0'
            env['GIT_PAGER'] = ''  # Disable pager for faster output
            
            # For status/log, turn off some expensive checks
            if tokens[1] in ['status', 'log']:
                env['GIT_OPTIONAL_LOCKS'] = '0'
        
        # Set a timeout for git commands based on the complexity
        timeout = 30  # Default timeout in seconds
        if len(tokens) > 1:
            # Simple commands get shorter timeouts
            if tokens[1] in ['status', 'branch', 'tag', 'remote']:
                timeout = 5
            # More complex operations get longer timeouts
            elif tokens[1] in ['clone', 'pull', 'push', 'fetch']:
                timeout = 60
        
        # For simple git commands, execute directly with performance optimizations
        try:
            process = subprocess.run(
                cmd, 
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                timeout=timeout  # Add timeout to prevent hanging
            )
            return process.returncode, process.stdout, process.stderr
        except subprocess.TimeoutExpired:
            return 1, "", f"Command timed out after {timeout} seconds. Try running in a regular terminal."
        except Exception as e:
            return 1, "", f"Error executing git command: {str(e)}"
        
    # Execute normal command
    return execute_subprocess(cmd)