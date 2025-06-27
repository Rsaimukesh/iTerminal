import subprocess
import shlex

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
        return process.returncode, stdout, stderr
    except Exception as e:
        return -1, '', str(e) 