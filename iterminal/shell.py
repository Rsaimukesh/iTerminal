import subprocess
import shlex

# List of interactive commands that don't work well in subprocess
INTERACTIVE_COMMANDS = {
    'nano', 'vim', 'vi', 'emacs', 'less', 'more', 'top', 'htop', 
    'man', 'info', 'ssh', 'telnet', 'ftp', 'sftp', 'screen', 'tmux'
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
    
    try:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        return process.returncode, stdout, stderr
    except Exception as e:
        return -1, '', str(e) 