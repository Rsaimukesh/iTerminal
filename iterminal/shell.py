import subprocess
import shlex
import shutil

# List of interactive commands that don't work well in subprocess
INTERACTIVE_COMMANDS = {
    'nano', 'vim', 'vi', 'emacs', 'less', 'more', 'top', 'htop', 
    'man', 'info', 'ssh', 'telnet', 'ftp', 'sftp', 'screen', 'tmux'
}

# Commands that wait for input (need special handling)
INPUT_WAITING_COMMANDS = {
    'cat', 'tee', 'read', 'mail', 'write', 'wall'
}

# Alternatives for interactive commands
COMMAND_ALTERNATIVES = {
    'nano': 'cat',  # For viewing files
    'vim': 'cat',
    'vi': 'cat', 
    'less': 'cat',
    'more': 'cat',
    'man': 'man --help',  # Show help instead
    'top': 'ps aux',  # Show processes
    'htop': 'ps aux',
}

def is_probably_shell_command(user_input: str) -> bool:
    return bool(user_input.strip() and (user_input.split()[0].isalpha() or user_input.startswith('./')))

def is_interactive_command(cmd: str) -> bool:
    """Check if command is interactive and won't work in subprocess"""
    first_word = cmd.strip().split()[0].lower()
    return first_word in INTERACTIVE_COMMANDS

def is_input_waiting_command(cmd: str) -> bool:
    """Check if command waits for input (like cat without args)"""
    first_word = cmd.strip().split()[0].lower()
    return first_word in INPUT_WAITING_COMMANDS and len(cmd.strip().split()) == 1

def get_command_alternative(cmd: str) -> str:
    """Get alternative command suggestion"""
    first_word = cmd.strip().split()[0].lower()
    return COMMAND_ALTERNATIVES.get(first_word, '')

def run_shell_command(cmd: str):
    # Check for common commands with case issues (likely caps lock)
    first_word = cmd.strip().split()[0] if cmd.strip() else ""
    common_commands = [
        "ls", "pwd", "cd", "cat", "grep", "echo", "find", "rm", "cp", "mv", "touch", "mkdir", "rmdir",
        "apt", "apt-get", "yum", "dnf", "pacman", "curl", "wget", "sudo", "chmod", "chown", "ps", "top",
        "git", "ssh", "scp", "ping", "ifconfig", "ip", "netstat", "tar", "zip", "unzip", "man", "nano", 
        "vim", "less", "more", "head", "tail", "wc", "sort", "uniq", "awk", "sed", "cut", "diff", "xargs"
    ]
    
    # Commands that are typically uppercase (don't convert these)
    uppercase_commands = ["COPY", "MAIL", "TIME", "ECHO", "CC", "MC"]
    
    # Check for all caps (LS, PWD) but only for common commands that aren't meant to be uppercase
    if first_word.isupper() and first_word.lower() in common_commands and first_word not in uppercase_commands:
        # Convert command to lowercase and run it
        cmd = first_word.lower() + cmd[len(first_word):]
    
    # Check for mixed case with first letter capitalized (Ls, Pwd)
    elif (first_word[0].isupper() if first_word else False) and first_word.lower() in common_commands and first_word not in uppercase_commands:
        # Convert command to lowercase and run it
        cmd = first_word.lower() + cmd[len(first_word):]
        
    # Plugin mode: allow all commands except major kernel-modifying ones
    from .config import PLUGIN_MODE
    if PLUGIN_MODE:
        cmd_lower = cmd.strip().lower()
        # Block truly dangerous, kernel-affecting commands
        dangerous = ['rm -rf /', 'dd if=/dev/zero', 'mkfs', 'fdisk', 'shutdown', 'reboot']
        for pat in dangerous:
            if pat in cmd_lower:
                return -1, '', f"Command '{cmd}' is blocked in plugin mode: dangerous operation."
        # Execute everything else
        try:
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()
            return process.returncode, stdout, stderr
        except Exception as e:
            return -1, '', str(e)
    # Detect 'sudo' when it's the first token and provide a clear message if not available
    first_token = cmd.strip().split()[0].lower() if cmd.strip() else ''
    if first_token == 'sudo' and shutil.which('sudo') is None:
        # Provide actionable advice when sudo isn't available in the environment
        error_msg = (
            """It looks like 'sudo' is not available in this environment. """
            """If you're running iTerminal inside a sandbox (Flatpak, container), use your host terminal to run """
            """system-level commands like package updates.\n\n"""
            """You can run the command without 'sudo' here (if appropriate) or run it on your host system."""
        )
        return 127, '', error_msg

    # Check if it's an interactive command
    if is_interactive_command(cmd):
        alternative = get_command_alternative(cmd)
        error_msg = f"Interactive command '{cmd}' detected. Please use your regular terminal for this command.\n\nInteractive commands that don't work in iTerminal:\n- Text editors: nano, vim, vi, emacs\n- Pagers: less, more, man\n- System monitors: top, htop\n- Remote access: ssh, telnet\n- Terminal multiplexers: screen, tmux\n\n"
        
        if alternative:
            error_msg += f"💡 Try this instead: {alternative}\n"
        
        error_msg += "\n💡 To use interactive programs, exit iTerminal first: 'exit'"
        return -1, '', error_msg
    
    # Check if it's an input-waiting command
    if is_input_waiting_command(cmd):
        first_word = cmd.strip().split()[0].lower()
        if first_word == 'cat':
            error_msg = f"Command '{cmd}' is waiting for input. Please provide a filename or use Ctrl+D to exit.\n\n💡 Examples:\n- cat filename.txt\n- cat /etc/passwd\n- echo 'text' | cat\n\n💡 To exit input mode, press Ctrl+C"
        else:
            error_msg = f"Command '{cmd}' is waiting for input. Please provide arguments or use Ctrl+C to cancel.\n\n💡 To exit input mode, press Ctrl+C"
        return -1, '', error_msg
    
    try:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        # Fallback: if command not found and running in FlatpakSandbox, spawn on host
        if process.returncode != 0 and 'command not found' in (stderr or '').lower():
            if shutil.which('flatpak-spawn'):
                host_cmd = f"flatpak-spawn --host {cmd}"
                host_proc = subprocess.Popen(host_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                out2, err2 = host_proc.communicate()
                return host_proc.returncode, out2, err2
        return process.returncode, stdout, stderr
    except Exception as e:
        return -1, '', str(e)