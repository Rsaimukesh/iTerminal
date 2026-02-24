from rich.console import Console
from rich.prompt import Prompt
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.layout import Layout
from rich.columns import Columns
from rich.align import Align
from .shell import is_probably_shell_command, run_shell_command
from .ai import explain_command, translate_nl_to_shell, correct_shell_command, suggest_related_commands, analyze_command_safety, get_command_complexity, smart_command_generation, suggest_common_commands_for_context
from .logger import log_entry
from .config import get_api_key
from .dataset import Dataset
from .suggest import get_user_input
from .stats import UsageStats

# Import the fix for sudo messages
try:
    from .fix_sudo_messages import *  # This will apply the monkey patch
except:
    pass  # Ignore if it fails
import os
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

# Import git command cache for fast responses
try:
    from .git_cache import GIT_COMMAND_CACHE
except ImportError:
    GIT_COMMAND_CACHE = {}
    
# Import command utility functions
from .command_utils import is_git_command, extract_git_subcommand, correct_git_typo
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import threading
import multiprocessing
from .config import PLUGIN_MODE
from rich.prompt import Confirm

# Determine optimal thread and process counts
CPU_COUNT = multiprocessing.cpu_count()
OPTIMAL_THREADS = min(32, CPU_COUNT * 4)  # Hyperthreading: 4 threads per CPU
OPTIMAL_PROCESSES = max(2, CPU_COUNT - 1)  # Leave one CPU for main thread

# Enhanced executor for hyperthreaded AI and network-bound calls
executor = ThreadPoolExecutor(max_workers=OPTIMAL_THREADS)

# Separate executor for CPU-intensive operations
process_executor = ProcessPoolExecutor(max_workers=OPTIMAL_PROCESSES)

# Quick parallel task submission wrapper
def run_parallel(tasks, use_processes=False):
    """Run multiple tasks in parallel and return results"""
    ex = process_executor if use_processes else executor
    futures = [ex.submit(func, *args) for func, args in tasks]
    return [future.result() for future in as_completed(futures)]

console = Console()

# Enhanced command aliases for common tasks
COMMAND_ALIASES = {
    'help': 'show help information',
    'history': 'show command history',
    'clear': 'clear the terminal',
    'stats': 'show usage statistics',
    'dataset': 'show learned commands',
    'suggest': 'get command suggestions',
    'safety': 'analyze command safety',
    'session': 'show session information',
    'export': 'export command history',
    'import': 'import commands from file',
    'fix': 'fix unclear or wrong prompt',
    'provider': 'set AI provider (ollama/openrouter)',
    'ollama': 'configure Ollama settings',
    'pause': 'pause and prompt to continue iteration'
}

class SessionManager:
    """Enhanced session management with persistence and analytics"""
    
    def __init__(self):
        self.session_start = datetime.now()
        self.commands_executed = 0
        self.ai_queries = 0
        self.errors_encountered = 0
        self.session_file = os.path.expanduser('~/.iterminal_session.json')
        self.load_session()
    
    def load_session(self):
        """Load session data from file"""
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, 'r') as f:
                    data = json.load(f)
                    self.commands_executed = data.get('commands_executed', 0)
                    self.ai_queries = data.get('ai_queries', 0)
                    self.errors_encountered = data.get('errors_encountered', 0)
            except:
                pass
    
    def save_session(self):
        """Save session data to file"""
        data = {
            'commands_executed': self.commands_executed,
            'ai_queries': self.ai_queries,
            'errors_encountered': self.errors_encountered,
            'last_session': datetime.now().isoformat()
        }
        try:
            with open(self.session_file, 'w') as f:
                json.dump(data, f)
        except:
            pass
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics"""
        duration = datetime.now() - self.session_start
        return {
            'duration': str(duration).split('.')[0],  # Remove microseconds
            'commands_executed': self.commands_executed,
            'ai_queries': self.ai_queries,
            'errors_encountered': self.errors_encountered,
            'success_rate': ((self.commands_executed - self.errors_encountered) / max(self.commands_executed, 1)) * 100
        }

def pause_iteration(message: str = "Continue to iterate?") -> bool:
    """Pause and ask user if they want to continue
    
    Args:
        message: The message to display (default: "Continue to iterate?")
        
    Returns:
        bool: True if the user wants to continue, False to pause
    """
    return Confirm.ask(message, default=True)

def is_safe_auto_execute_command(cmd: str) -> bool:
    """Check if a command is safe to auto-execute without confirmation"""
    # List of safe commands that can auto-execute
    safe_commands = [
        'ls', 'pwd', 'whoami', 'date', 'uptime', 'df', 'free', 'top', 'ps',
        'cat', 'less', 'more', 'head', 'tail', 'wc', 'grep', 'find', 'which',
        'echo', 'history', 'env', 'printenv', 'uname', 'hostname', 'id',
        'groups', 'finger', 'w', 'last', 'lastlog', 'file', 'stat', 'type'
    ]
    
    cmd_parts = cmd.strip().split()
    if not cmd_parts:
        return False
    
    first_word = cmd_parts[0].lower()
    
    # Remove 'sudo' prefix for checking
    if first_word == 'sudo' and len(cmd_parts) > 1:
        first_word = cmd_parts[1].lower()
    
    # Check for safe commands
    if first_word in safe_commands:
        return True
    
    # Safe git commands
    if first_word == 'git' and len(cmd_parts) > 1:
        git_safe_cmds = ['status', 'log', 'diff', 'show', 'branch', 'tag', 'remote', 'ls-files']
        if cmd_parts[1] in git_safe_cmds:
            return True
    
    # Safe package manager commands (update only, not upgrade/install/remove)
    if 'apt update' in cmd or 'apt-get update' in cmd:
        return True
    if 'dnf check-update' in cmd or 'yum check-update' in cmd:
        return True
    
    return False

def confirm_command(cmd: str, explanation: str, safety_analysis: Optional[Dict[str, Any]] = None) -> str:
    """Enhanced command confirmation with safety analysis"""
    # Create a more informative panel
    panel_content = f"[bold yellow]{cmd}[/bold yellow]\n\n[italic cyan]{explanation}[/italic cyan]"
    
    # Check if this is a safe/common command that should auto-execute
    safe_commands = [
        'ls', 'pwd', 'whoami', 'date', 'uptime', 'df', 'free', 'top', 'ps',
        'cat', 'less', 'more', 'head', 'tail', 'wc', 'grep', 'find', 'which',
        'echo', 'history', 'env', 'printenv', 'uname', 'hostname'
    ]
    
    # Check if command starts with safe read-only operations
    cmd_first_word = cmd.strip().split()[0] if cmd.strip() else ''
    is_safe_command = cmd_first_word in safe_commands
    
    # Check for safe git commands
    if cmd.startswith('git '):
        git_safe_cmds = ['status', 'log', 'diff', 'show', 'branch', 'tag', 'remote', 'ls-files']
        git_subcmd = cmd.split()[1] if len(cmd.split()) > 1 else ''
        is_safe_command = git_subcmd in git_safe_cmds
    
    # Check for apt update/upgrade which are safe
    if 'apt update' in cmd or 'apt-get update' in cmd:
        is_safe_command = True
    
    auto_execute = False
    if safety_analysis:
        risk_level = safety_analysis.get('risk_level', 'low')
        warning = safety_analysis.get('warning', '')
        safer_alt = safety_analysis.get('safer_alternative', '')
        
        if risk_level in ['high', 'critical']:
            panel_content += f"\n\n[bold red]⚠️  RISK LEVEL: {risk_level.upper()}[/bold red]"
            if warning:
                panel_content += f"\n[red]{warning}[/red]"
            if safer_alt:
                panel_content += f"\n[green]Safer alternative: {safer_alt}[/green]"
            is_safe_command = False  # Never auto-execute dangerous commands
        elif risk_level == 'medium':
            panel_content += f"\n\n[yellow]⚠️  RISK LEVEL: {risk_level.upper()}[/yellow]"
            if warning:
                panel_content += f"\n[yellow]{warning}[/yellow]"
            is_safe_command = False
        elif risk_level == 'low' and is_safe_command:
            auto_execute = True
    elif is_safe_command:
        # No safety analysis but command is in safe list
        auto_execute = True
    
    console.print(Panel(panel_content, title="[Explanation]", border_style="yellow"))
    
    # Auto-execute safe commands without prompting
    if auto_execute:
        console.print("[dim]Auto-executing safe command...[/dim]")
        return "Y"
    
    choices = ["Y", "n", "edit", "related", "safety"]
    if safety_analysis and safety_analysis.get('requires_confirmation', False):
        choices.append("force")
    
    return Prompt.ask("Run this command?", choices=choices, default="Y")

def show_help():
    """Display help information"""
    help_text = """
[bold green]iTerminal Help[/bold green]

[bold]Basic Usage:[/bold]
• Type Linux commands directly: [cyan]ls -la[/cyan]
• Use natural language: [cyan]show me running processes[/cyan]
• Get command explanations automatically
• Smart handling of unclear or wrong prompts

[bold]Navigation:[/bold]
• [cyan]↑/↓ arrows[/cyan] - Navigate command history
• [cyan]Tab[/cyan] - Auto-complete commands and file paths
• [cyan]Ctrl+R[/cyan] - Search command history
• [cyan]Mouse[/cyan] - Click to position cursor

[bold]Smart Suggestions:[/bold]
• 💡 Contextual command templates (git, system, file ops, etc.)
• 🔥 Frequently used commands from your history
• 📚 Commands from your saved dataset
• 🔧 Common Linux commands
• Natural language pattern matching
• Smart error correction and typo fixing

[bold]Special Commands:[/bold]
• [cyan]help[/cyan] - Show this help
• [cyan]history[/cyan] - Show command history
• [cyan]stats[/cyan] - Show usage statistics
• [cyan]dataset[/cyan] - Show learned commands
• [cyan]clear[/cyan] - Clear terminal
• [cyan]fix[/cyan] - Fix unclear or wrong prompts
• [cyan]provider[/cyan] - Set AI provider (ollama/openrouter)
• [cyan]ollama[/cyan] - Configure Ollama settings
• [cyan]pause[/cyan] - Pause and prompt to continue iteration
• [cyan]exit[/cyan] - Exit iTerminal

[bold]AI Features:[/bold]
• Multiple AI providers (Ollama, OpenRouter)
• Automatic command correction
• Natural language translation
• Command explanations
• Related command suggestions
• Smart prompt interpretation
• Typo correction and suggestions
• Multiple command alternatives

[bold]Error Handling:[/bold]
• Automatic detection of unclear prompts
• Multiple interpretation attempts
• Context-based command suggestions
• Typo correction for natural language
• Alternative command suggestions
• Interactive prompt fixing with 'fix' command

[bold]Tips:[/bold]
• Commands are automatically learned and remembered
• Interactive programs (nano, vim) work in regular terminal
• Use Tab for file path completion: [cyan]cat /home/sai/Doc[Tab][/cyan]
• Type partial commands to see smart suggestions
• Natural language triggers contextual suggestions
• If a prompt is unclear, use the 'fix' command for help
• The system will automatically try to interpret unclear inputs
"""
    console.print(Panel(help_text, title="[Help]", border_style="green"))

def show_session_info(session_manager: SessionManager):
    """Display current session information"""
    stats = session_manager.get_session_stats()
    
    session_panel = Panel(
        f"[bold]Session Duration:[/bold] {stats['duration']}\n"
        f"[bold]Commands Executed:[/bold] {stats['commands_executed']}\n"
        f"[bold]AI Queries:[/bold] {stats['ai_queries']}\n"
        f"[bold]Errors Encountered:[/bold] {stats['errors_encountered']}\n"
        f"[bold]Success Rate:[/bold] {stats['success_rate']:.1f}%",
        title="[Session Information]",
        border_style="blue"
    )
    console.print(session_panel)

def show_history(dataset: Dataset, stats: UsageStats):
    """Enhanced command history display"""
    history_file = os.path.expanduser('~/.iterminal_history')
    
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    console.print("[bold]Recent Commands:[/bold]")
                    for i, line in enumerate(lines[-20:], 1):  # Last 20 commands
                        if line.strip():
                            console.print(f"  [dim]{len(lines)-20+i:2d}.[/dim] [cyan]{line.strip()}[/cyan]")
                else:
                    console.print("[yellow]No command history found.[/yellow]")
        except Exception as e:
            console.print(f"[red]Error reading history: {e}[/red]")
    else:
        console.print("[yellow]No command history file found.[/yellow]")
    
    # Also show usage statistics
    if hasattr(stats, 'usage') and stats.usage:
        console.print("\n[bold]Most Used Commands:[/bold]")
        for cmd, count in sorted(stats.usage.items(), key=lambda x: x[1], reverse=True)[:5]:
            console.print(f"  [green]{count}x[/green] [cyan]{cmd}[/cyan]")

def show_stats(stats: UsageStats):
    """Enhanced usage statistics display"""
    if hasattr(stats, 'usage') and stats.usage:
        total_commands = sum(stats.usage.values())
        unique_commands = len(stats.usage)
        most_used = max(stats.usage.items(), key=lambda x: x[1])
        
        # Create a more detailed stats panel
        stats_content = f"[bold]Total Commands:[/bold] {total_commands}\n"
        stats_content += f"[bold]Unique Commands:[/bold] {unique_commands}\n"
        stats_content += f"[bold]Most Used:[/bold] {most_used[0]} ({most_used[1]} times)\n"
        stats_content += f"[bold]Average Usage:[/bold] {total_commands / unique_commands:.1f} times per command"
        
        console.print(Panel(stats_content, title="[Usage Statistics]", border_style="green"))
    else:
        console.print("[yellow]No usage statistics available yet.[/yellow]")

def show_dataset(dataset: Dataset):
    """Enhanced learned commands display with robust error handling"""
    if not hasattr(dataset, 'data') or not dataset.data:
        console.print("[yellow]No commands learned yet.[/yellow]")
        return
        
    # First try: Simple table display
    try:
        console.print("\n[bold magenta]Learned Commands[/bold magenta]")
        
        # Create a simplified table without complexity (which relies on AI)
        table = Table(show_header=True, header_style="bold")
        table.add_column("Natural Language", style="cyan", width=30)
        table.add_column("Command", style="yellow", width=25)
        table.add_column("Explanation", style="green", width=40)
        
        # Get the last 10 commands, or all if less than 10
        display_items = dataset.data[-10:] if len(dataset.data) > 10 else dataset.data
        
        for item in display_items:
            # Simple error handling for each row
            try:
                prompt = item.get('prompt', '')[:27] + "..." if len(item.get('prompt', '')) > 30 else item.get('prompt', '')
                command = item.get('command', '')[:22] + "..." if len(item.get('command', '')) > 25 else item.get('command', '')
                explanation = item.get('explanation', '')[:37] + "..." if len(item.get('explanation', '')) > 40 else item.get('explanation', '')
                
                table.add_row(prompt, command, explanation)
            except:
                continue  # Skip problematic items
                
        console.print(table)
        
    except Exception as e:
        # Fallback to super simple list if table fails
        try:
            console.print("\n[bold magenta]Learned Commands[/bold magenta]")
            for i, item in enumerate(dataset.data[-5:]):
                console.print(f"[cyan]{i+1}. Prompt:[/cyan] {str(item.get('prompt', ''))}")
                console.print(f"   [yellow]Command:[/yellow] {str(item.get('command', ''))}")
                console.print(f"   [green]Explanation:[/green] {str(item.get('explanation', ''))}")
                console.print("---")
        except Exception as e2:
            # Ultimate fallback - just print data count
            console.print(f"[yellow]Dataset contains {len(dataset.data)} commands.[/yellow]")
            console.print("[red]Could not display dataset contents due to formatting issues.[/red]")
            console.print(f"[dim]Error: {str(e2)}[/dim]")

def analyze_command_safety_wrapper(cmd: str):
    """Wrapper to analyze and display command safety"""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Analyzing command safety...", total=None)
        safety_analysis = analyze_command_safety(cmd)
        progress.update(task, completed=True)
    
    risk_level = safety_analysis.get('risk_level', 'low')
    warning = safety_analysis.get('warning', '')
    safer_alt = safety_analysis.get('safer_alternative', '')
    
    # Color code based on risk level
    if risk_level == 'critical':
        color = 'red'
        icon = '🚨'
    elif risk_level == 'high':
        color = 'red'
        icon = '⚠️'
    elif risk_level == 'medium':
        color = 'yellow'
        icon = '⚠️'
    else:
        color = 'green'
        icon = '✅'
    
    safety_panel = f"[bold {color}]{icon} Risk Level: {risk_level.upper()}[/bold {color}]\n\n"
    safety_panel += f"[bold]Command:[/bold] {cmd}\n\n"
    
    if warning:
        safety_panel += f"[{color}]{warning}[/{color}]\n\n"
    
    if safer_alt:
        safety_panel += f"[green]Safer Alternative:[/green] {safer_alt}"
    
    console.print(Panel(safety_panel, title="[Safety Analysis]", border_style=color))

def export_history():
    """Export command history to a file"""
    history_file = os.path.expanduser('~/.iterminal_history')
    export_file = f"iterminal_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                history_content = f.read()
            
            with open(export_file, 'w') as f:
                f.write(f"iTerminal Command History Export\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write(f"{'='*50}\n\n")
                f.write(history_content)
            
            console.print(f"[green]History exported to: {export_file}[/green]")
        except Exception as e:
            console.print(f"[red]Error exporting history: {e}[/red]")
    else:
        console.print("[yellow]No command history to export.[/yellow]")

def handle_unclear_prompt(user_input: str, dataset: Dataset, stats: UsageStats):
    """Handle unclear or wrong prompts with smart command generation"""
    console.print(f"[yellow]I'm not sure what you mean by '{user_input}'. Let me try to help...[/yellow]")
    
    # Try smart command generation
    smart_result = smart_command_generation(user_input)
    
    if smart_result['method'] == 'typo_correction':
        console.print(f"[green]I think you meant: {smart_result['explanation']}[/green]")
    elif smart_result['method'] == 'interpretation':
        console.print(f"[green]{smart_result['explanation']}[/green]")
    elif smart_result['method'] == 'generation':
        console.print(f"[green]{smart_result['explanation']}[/green]")
    
    # Show the suggested command
    shell_cmd = smart_result['command']
    explanation = explain_command(shell_cmd)
    
    console.print(Panel(Text(shell_cmd, style="bold yellow"), title="[Smart Suggestion]"))
    console.print(Text(explanation, style="italic cyan"))
    
    # Show alternatives if available
    if smart_result.get('alternatives'):
        console.print("\n[bold]Alternative interpretations:[/bold]")
        for i, alt in enumerate(smart_result['alternatives'][:3], 1):
            console.print(f"  {i}. [cyan]{alt}[/cyan]")
    
    # Show context-based suggestions
    context_suggestions = suggest_common_commands_for_context(user_input)
    if context_suggestions:
        console.print("\n[bold]Related commands you might want:[/bold]")
        for i, suggestion in enumerate(context_suggestions[:3], 1):
            console.print(f"  {i}. [green]{suggestion}[/green]")
    
    # Ask user what to do
    choices = ["Y", "n", "edit", "alternatives", "suggestions", "help"]
    choice = Prompt.ask("Run the suggested command?", choices=choices, default="Y")
    
    if choice == "Y":
        stats.add(shell_cmd)
        ret, out, err = run_shell_command(shell_cmd)
        if out:
            console.print(Text(out, style="green"))
        if err:
            console.print(Text(err, style="red"))
        log_entry(f"UNCLEAR_PROMT: {user_input}\nSMART_CMD: {shell_cmd}\nOUT: {out}\nERR: {err}\nEXPLAIN: {explanation}")
        
        # Auto-learn the successful command
        if ret == 0:
            dataset.add(user_input, shell_cmd, explanation)
    
    elif choice == "edit":
        edited = Prompt.ask("Edit command", default=shell_cmd)
        stats.add(edited)
        explanation2 = explain_command(edited)
        console.print(Text(explanation2, style="cyan"))
        ret2, out2, err2 = run_shell_command(edited)
        if out2:
            console.print(Text(out2, style="green"))
        if err2:
            console.print(Text(err2, style="red"))
        log_entry(f"EDITED_UNCLEAR: {edited}\nOUT: {out2}\nERR: {err2}\nEXPLAIN: {explanation2}")
        
        # Save successful edited command to dataset for future use
        if ret2 == 0:
            dataset.add(user_input, edited, explanation2)
            
    elif choice == "alternatives":
        if smart_result.get('alternatives'):
            console.print("\n[bold]Choose an alternative:[/bold]")
            for i, alt in enumerate(smart_result['alternatives'], 1):
                console.print(f"  {i}. [cyan]{alt}[/cyan]")
            try:
                alt_choice = int(Prompt.ask("Select alternative (number)", default="1"))
                if 1 <= alt_choice <= len(smart_result['alternatives']):
                    selected_alt = smart_result['alternatives'][alt_choice - 1]
                    stats.add(selected_alt)
                    ret3, out3, err3 = run_shell_command(selected_alt)
                    if out3:
                        console.print(Text(out3, style="green"))
                    if err3:
                        console.print(Text(err3, style="red"))
                    log_entry(f"ALTERNATIVE_CMD: {selected_alt}\nOUT: {out3}\nERR: {err3}")
                    
                    # Save successful alternatives to dataset for future use
                    if ret3 == 0:
                        explanation3 = explain_command(selected_alt)
                        dataset.add(user_input, selected_alt, explanation3)
            except ValueError:
                console.print("[red]Invalid selection.[/red]")
    
    elif choice == "suggestions":
        context_suggestions = suggest_common_commands_for_context(user_input)
        if context_suggestions:
            console.print("\n[bold]Choose a suggestion:[/bold]")
            for i, suggestion in enumerate(context_suggestions, 1):
                console.print(f"  {i}. [green]{suggestion}[/green]")
            try:
                sug_choice = int(Prompt.ask("Select suggestion (number)", default="1"))
                if 1 <= sug_choice <= len(context_suggestions):
                    selected_sug = context_suggestions[sug_choice - 1]
                    stats.add(selected_sug)
                    ret4, out4, err4 = run_shell_command(selected_sug)
                    if out4:
                        console.print(Text(out4, style="green"))
                    if err4:
                        console.print(Text(err4, style="red"))
                    log_entry(f"SUGGESTION_CMD: {selected_sug}\nOUT: {out4}\nERR: {err4}")
                    
                    # Save successful suggestions to dataset for future use
                    if ret4 == 0:
                        explanation4 = explain_command(selected_sug)
                        dataset.add(user_input, selected_sug, explanation4)
            except ValueError:
                console.print("[red]Invalid selection.[/red]")
    
    elif choice == "help":
        show_help()

def show_why():  
    """Explain key behaviors and design choices."""
    text = (
        "iTerminal is designed to combine AI assistance with real shell execution. "
        "It runs commands in a sandboxed environment and uses fallbacks (like flatpak-spawn) "
        "to execute host-level commands when needed. "
        "Plugin mode bypasses AI prompts and safety checks, allowing seamless integration in other apps."
    )
    console.print(Panel(text, title="[Why iTerminal]", border_style="cyan"))

def ensure_history_file():
    """Ensure history file exists and is writable"""
    history_file = os.path.expanduser('~/.iterminal_history')
    try:
        if not os.path.exists(history_file):
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            with open(history_file, 'w') as f:
                pass  # Just create the file
        
        # Make sure it's writable
        if not os.access(history_file, os.W_OK):
            os.chmod(history_file, 0o600)  # Read/write for owner only
            
        return True
    except Exception as e:
        console.print(f"[yellow]Warning: Could not set up history file: {e}[/yellow]")
        return False

def main_loop():
    """Enhanced main loop with better session management and error handling"""
    get_api_key()  # Ensure API key is set
    dataset = Dataset()
    stats = UsageStats()
    session_manager = SessionManager()
    
    # Ensure history file is properly set up
    ensure_history_file()
    
    # Welcome message with session info
    from iterminal.config import get_ai_provider, get_ollama_status
    current_provider = get_ai_provider()
    console.print("[bold green]Welcome to iTerminal! Type your command or ask in plain English. Type 'exit' or Ctrl-D to quit.[/bold green]")
    
    # More prominent AI provider information
    provider_color = "green" if current_provider == "ollama" else "cyan"
    console.print(f"Type 'help' for more information | AI Provider: [bold {provider_color}]{current_provider.upper()}[/bold {provider_color}]")
    
    # If using Ollama, show status
    if current_provider == 'ollama':
        status, message = get_ollama_status()
        if status:
            console.print(f"[dim green]✓ {message}[/dim green]")
        else:
            console.print(f"[dim yellow]⚠ {message} (Falling back to OpenRouter)[/dim yellow]")
    
    # Show session info if returning user
    if session_manager.commands_executed > 0:
        session_stats = session_manager.get_session_stats()
        console.print(f"[dim]Welcome back! You've executed {session_stats['commands_executed']} commands with {session_stats['success_rate']:.1f}% success rate.[/dim]")
    
    while True:
        try:
            user_input = get_user_input(dataset, stats, prompt_text="iTerminal > ")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[bold red]Exiting iTerminal. Goodbye!")
            session_manager.save_session()
            break
        
        if not user_input.strip():
            continue
        
        if user_input.strip().lower() in ("exit", "quit"):  # Exit
            session_manager.save_session()
            break
        
        # Handle help command
        if user_input.strip().lower() == 'help':
            show_help()
            continue
        
        log_entry(f"USER: {user_input}")
        
        # Handle special commands
        if user_input.strip().lower() == 'history':
            show_history(dataset, stats)
            continue
        elif user_input.strip().lower() == 'stats':
            show_stats(stats)
            continue
        elif user_input.strip().lower() == 'dataset':
            try:
                show_dataset(dataset)
            except Exception as e:
                console.print("[red]Error displaying dataset:[/red]", str(e))
                console.print("[yellow]Try running the dataset repair script:[/yellow] python scripts/repair_dataset.py")
            continue
        elif user_input.strip().lower() == 'session':
            show_session_info(session_manager)
            continue
        elif user_input.strip().lower() == 'safety':
            cmd_to_analyze = Prompt.ask("Enter command to analyze")
            analyze_command_safety_wrapper(cmd_to_analyze)
            continue
        elif user_input.strip().lower() == 'export':
            export_history()
            continue
        elif user_input.strip().lower() == 'clear':
            console.clear()
            continue
        elif user_input.strip().lower() == 'fix':
            unclear_input = Prompt.ask("Enter the unclear prompt to fix")
            handle_unclear_prompt(unclear_input, dataset, stats)
            continue
        elif user_input.strip().lower() == 'provider':
            from iterminal.config import set_ai_provider, get_ollama_status, get_ai_provider
            current_provider = get_ai_provider()
            console.print(f"[bold]Current AI provider:[/bold] [green]{current_provider}[/green]")
            
            if current_provider == 'ollama':
                status, message = get_ollama_status()
                console.print(f"[dim]Ollama status: {message}[/dim]")
            
            new_provider = Prompt.ask(
                "Select AI provider", 
                choices=["ollama", "openrouter"], 
                default=current_provider
            )
            
            if set_ai_provider(new_provider):
                console.print(f"[green]AI provider set to {new_provider}![/green]")
                # Show message about Ollama configuration if switching to it
                if new_provider == 'ollama':
                    console.print("[yellow]You can configure Ollama settings by typing 'ollama'[/yellow]")
                # Force reload from global
                from iterminal.config import get_ai_provider
                updated_provider = get_ai_provider()
                console.print(f"[dim]Provider set to: {updated_provider}[/dim]")
            continue
        elif user_input.strip().lower() == 'ollama':
            from iterminal.config import configure_ollama
            configure_ollama()
            continue
        elif user_input.strip().lower() == 'why':
            show_why()
            continue
        elif user_input.strip().lower() == 'pause':
            if not pause_iteration():
                console.print("[yellow]Iteration paused. Press Enter to resume.[/yellow]")
                input()
            continue
        
        # Flag tracks input type
        was_natural_prompt = False

        # 1. Plugin mode shortcut: execute all commands (shell.run blocks only dangerous ones)
        if PLUGIN_MODE and is_probably_shell_command(user_input):
            session_manager.commands_executed += 1
            ret, out, err = run_shell_command(user_input)
            if out:
                console.print(Text(out, style="green"))
            if err:
                console.print(Text(err, style="red"))
            log_entry(f"PLUGIN_CMD: {user_input}\nOUT: {out}\nERR: {err}")
            continue
        # 1. Try as shell command
        if is_probably_shell_command(user_input):
            session_manager.commands_executed += 1
            
            # Auto-correct Git typos immediately without confirmation
            if is_git_command(user_input):
                corrected_input = correct_git_typo(user_input)
                if corrected_input != user_input:
                    console.print(f"[yellow]Auto-correcting:[/yellow] {user_input} → [bold]{corrected_input}[/bold]")
                    user_input = corrected_input
            
            # FAST PATH: Check for Git commands and provide instant cached response
            if is_git_command(user_input):
                git_subcommand = extract_git_subcommand(user_input)
                if git_subcommand in GIT_COMMAND_CACHE:
                    # Fast path: Get cached Git explanation before running the command
                    cached_explanation = GIT_COMMAND_CACHE[git_subcommand]
                    
                    # Show a panel with the explanation immediately
                    console.print(Panel(
                        Text(cached_explanation, style="cyan"),
                        title=f"[Git Command: {git_subcommand}]",
                        border_style="green"
                    ))
                    
                    # Log that we're using the cached response for faster Git commands
                    log_entry(f"FAST_GIT_CACHE: {user_input}")
                    
                    # Add a visual indicator that the command is being executed
                    with console.status("[bold green]Running Git command...[/]"):
                        # Execute the Git command
                        ret, out, err = run_shell_command(user_input)
                        
                    # Show the output of the command
                    if out:
                        console.print(Text(out, style="green"))
                    if err:
                        console.print(Text(err, style="red"))
                    
                    # Skip the rest of the processing for this command
                    continue
            
            # Analyze safety before execution
            safety_analysis = analyze_command_safety(user_input)
            if safety_analysis.get('requires_confirmation', False):
                # Skip AI explanation for Git commands that have cached explanations
                if is_git_command(user_input):
                    git_subcommand = extract_git_subcommand(user_input)
                    if git_subcommand in GIT_COMMAND_CACHE:
                        explanation = GIT_COMMAND_CACHE[git_subcommand]
                    else:
                        explanation = explain_command(user_input)
                else:
                    explanation = explain_command(user_input)
                
                choice = confirm_command(user_input, explanation, safety_analysis)
                if choice == "n":
                    continue
                elif choice == "edit":
                    user_input = Prompt.ask("Edit command", default=user_input)
                elif choice == "safety":
                    analyze_command_safety_wrapper(user_input)
                    continue
                elif choice == "force":
                    pass  # Continue with execution
                elif choice == "related":
                    related = suggest_related_commands(user_input)
                    console.print(Panel(Text(related, style="yellow"), title="[Related Commands]"))
                    continue
            
            ret, out, err = run_shell_command(user_input)
            if ret == 0:
                if out:
                    console.print(Text(out, style="green"))
                # Skip explanation for valid shell commands that executed successfully
                # Only show explanation if it was a natural language prompt or if there was an error
                log_entry(f"CMD: {user_input}\nOUT: {out}")
            else:
                session_manager.errors_encountered += 1
                # Special-case: environment missing sudo (sandbox/container)
                if err and "It looks like 'sudo' is not available in this environment" in err:
                    console.print(f"[yellow]Warning:[/] {err}")
                    # Automatically strip 'sudo' and re-run
                    parts = user_input.strip().split()
                    if parts and parts[0].lower() == 'sudo':
                        stripped = ' '.join(parts[1:])
                    else:
                        stripped = user_input
                    console.print(f"[cyan]Re-running without sudo:[/] {stripped}")
                    stats.add(stripped)
                    ret2, out2, err2 = run_shell_command(stripped)
                    if out2:
                        console.print(Text(out2, style="green"))
                    if err2:
                        console.print(Text(err2, style="red"))
                    log_entry(f"AUTO_SUDO_STRIP: {user_input} -> {stripped}\nOUT: {out2}\nERR: {err2}")
                    continue

                # Error: ask AI for correction
                correction = correct_shell_command(user_input, err)
                explanation = explain_command(correction)
                console.print(f"[red]Error:[/red] {err.strip()}")
                
                if correction and not correction.startswith('[AI error'):
                    # Extract command and AI explanation if provided in new format: "command [AI: explanation]"
                    actual_command = correction
                    ai_explanation = None
                    
                    if " [AI:" in correction and correction.endswith("]"):
                        parts = correction.split(" [AI:", 1)
                        actual_command = parts[0].strip()
                        ai_explanation = parts[1].rstrip("]").strip()
                    
                    # Get current AI provider for display
                    from .config import get_ai_provider
                    current_provider = get_ai_provider().upper()
                    
                    # Prevent circular suggestions between sudo and ssudo
                    first_word_original = user_input.strip().split()[0].lower() if user_input.strip() else ""
                    first_word_suggested = actual_command.strip().split()[0].lower() if actual_command.strip() else ""
                    
                    # If user typed 'ssudo' and AI suggests 'sudo', or vice versa, don't show the suggestion
                    if (first_word_original == "ssudo" and first_word_suggested == "sudo") or \
                       (first_word_original == "sudo" and first_word_suggested == "ssudo"):
                        # Skip this suggestion to avoid a loop
                        console.print("[yellow]Avoiding circular suggestion between sudo and ssudo.[/yellow]")
                        continue
                    
                    # Auto-correct for Git commands and simple typos without confirmation
                    should_auto_correct = False
                    
                    # Check if it's a Git command with minor typo
                    if is_git_command(actual_command) and not is_git_command(user_input):
                        # User tried to use Git but made a typo (e.g., "gt status" -> "git status")
                        should_auto_correct = True
                    # Check for very similar commands (minor typos)
                    elif len(user_input) > 3 and len(actual_command) > 3:
                        # Calculate similarity - if correction is very similar, auto-correct
                        from difflib import SequenceMatcher
                        similarity = SequenceMatcher(None, user_input.lower(), actual_command.lower()).ratio()
                        if similarity > 0.8:  # More than 80% similar
                            should_auto_correct = True
                    
                    if should_auto_correct:
                        # Auto-correct without asking
                        console.print(f"[yellow]Auto-correcting:[/yellow] [bold]{actual_command}[/bold] [dim]({current_provider} AI)[/dim]")
                        if ai_explanation:
                            console.print(f"[dim cyan]{ai_explanation}[/dim cyan]")
                        
                        stats.add(actual_command)
                        ret2, out2, err2 = run_shell_command(actual_command)
                        if out2:
                            console.print(Text(out2, style="green"))
                        if err2:
                            console.print(Text(err2, style="red"))
                        log_entry(f"AUTO_CORRECTED: {user_input} -> {actual_command}\nOUT: {out2}\nERR: {err2}\nEXPLAIN: {ai_explanation or explanation}")
                        
                        # Save successful auto-corrections to dataset for future use
                        if ret2 == 0:
                            dataset.add(user_input, actual_command, ai_explanation or explanation)
                        continue
                    
                    # For other corrections, show suggestion and ask
                    if ai_explanation:
                        # Show both the command and the AI's explanation
                        console.print(f"[yellow]Did you mean:[/yellow] [bold]{actual_command}[/bold]? [dim]({current_provider} AI)[/dim]")
                        console.print(f"[cyan]{ai_explanation}[/cyan]")
                    else:
                        # Show the command and the standard explanation
                        console.print(f"[yellow]Did you mean:[/yellow] [bold]{correction}[/bold]? [dim]({current_provider} AI)[/dim]")
                        console.print(Text(explanation, style="cyan"))
                    
                    choice = Prompt.ask("Run?", choices=["Y", "n", "edit", "related"], default="Y")
                    if choice == "Y":
                        # Always use the actual_command, not the full explanation
                        stats.add(actual_command)
                        ret2, out2, err2 = run_shell_command(actual_command)
                        if out2:
                            console.print(Text(out2, style="green"))
                        if err2:
                            console.print(Text(err2, style="red"))
                        log_entry(f"FIXED_CMD: {actual_command}\nOUT: {out2}\nERR: {err2}\nEXPLAIN: {ai_explanation or explanation}")
                        
                        # Save successful command corrections to dataset for future use
                        if ret2 == 0:
                            dataset.add(user_input, actual_command, ai_explanation or explanation)
                    elif choice == "edit":
                        edited = Prompt.ask("Edit command", default=correction)
                        stats.add(edited)
                        explanation2 = explain_command(edited)
                        console.print(Text(explanation2, style="cyan"))
                        ret3, out3, err3 = run_shell_command(edited)
                        if out3:
                            console.print(Text(out3, style="green"))
                        if err3:
                            console.print(Text(err3, style="red"))
                        log_entry(f"EDITED_CMD: {edited}\nOUT: {out3}\nERR: {err3}\nEXPLAIN: {explanation2}")
                        
                        # Save successful edited commands to dataset for future use
                        if ret3 == 0:
                            dataset.add(user_input, edited, explanation2)
                    elif choice == "related":
                        related = suggest_related_commands(user_input)
                        console.print(Panel(Text(related, style="yellow"), title="[Related Commands]"))
                else:
                    console.print("[red]No recommendation available from AI.[/red]")
        else:
            # 2. Natural language: try smart command generation first
            was_natural_prompt = True  # Set flag for natural language input
            session_manager.ai_queries += 1
            dataset_result = dataset.search(user_input)
            if dataset_result:
                shell_cmd = dataset_result['command']
                explanation = dataset_result['explanation']
                # Check if this is an exact match (case insensitive)
                is_exact_match = dataset_result.get('prompt', '').lower() == user_input.lower()
                
                console.print(Panel(Text(shell_cmd, style="bold yellow"), title="[Suggestion from Dataset]"))
                console.print(Text(explanation, style="italic cyan"))
                
                # Check if this is a safe command that should auto-execute
                safe_auto_execute = is_safe_auto_execute_command(shell_cmd)
                
                # Auto-execute if exact match OR if it's a safe command, otherwise ask for confirmation
                if is_exact_match or safe_auto_execute:
                    if is_exact_match:
                        console.print("[green]Exact match found in dataset. Auto-executing...[/green]")
                    else:
                        console.print("[dim]Auto-executing safe command...[/dim]")
                    choice = "Y"
                else:
                    choice = Prompt.ask("Run this command?", choices=["Y", "n", "edit", "related"], default="Y")
            else:
                # Use smart command generation and explanation in parallel for unclear prompts
                smart_future = executor.submit(smart_command_generation, user_input)
                smart_result = smart_future.result()
                shell_cmd = smart_result['command']
                
                # Check for error messages from the AI - more comprehensive check
                if (shell_cmd.startswith('[Ollama') or 
                    shell_cmd.startswith('[AI') or
                    'ERROR' in shell_cmd.upper() or
                    shell_cmd.startswith('[OpenRouter')):
                    console.print(f"[yellow]AI Error:[/yellow] {shell_cmd}")
                    
                    # Provide more specific guidance based on the error message
                    if "Ollama server not available" in shell_cmd:
                        console.print("[yellow]Ollama is not installed or not running on this system.[/yellow]")
                        console.print("[cyan]You can install Ollama by running: sudo bash scripts/install_ollama.sh[/cyan]")
                        console.print("[cyan]Or switch to OpenRouter by typing: provider openrouter[/cyan]")
                    else:
                        console.print("[yellow]Please check if Ollama is running or if your OpenRouter API key is set.[/yellow]")
                        console.print("[dim]Hint: Type 'provider' to switch AI providers or 'ollama' to configure Ollama.[/dim]")
                    continue
                
                expl_future = executor.submit(explain_command, shell_cmd)
                explanation = expl_future.result()
                
                # If the result seems unclear or generic, offer enhanced help
                if (smart_result['method'] != 'translation' or 
                    shell_cmd in ['ls', 'pwd', 'whoami']):
                    handle_unclear_prompt(user_input, dataset, stats)
                    continue
                
                choice = confirm_command(shell_cmd, explanation)
                # Auto-learn: save to dataset if AI translation is successful
                if shell_cmd and not shell_cmd.startswith('[AI error'):
                    dataset.add(user_input, shell_cmd, explanation)
            
            if choice == "Y":
                stats.add(shell_cmd)
                
                # Check if this is a Git command and use cache for fast explanation
                git_explanation_shown = False
                if is_git_command(shell_cmd):
                    git_subcommand = extract_git_subcommand(shell_cmd)
                    if git_subcommand in GIT_COMMAND_CACHE:
                        # Show the cached Git explanation before running the command
                        git_explanation = GIT_COMMAND_CACHE[git_subcommand]
                        console.print(Panel(
                            Text(git_explanation, style="cyan"),
                            title=f"[Git Command: {git_subcommand}]",
                            border_style="green"
                        ))
                        git_explanation_shown = True
                        # Update the explanation to include the cached one
                        explanation = f"{explanation}\n\n{git_explanation}"
                        log_entry(f"GIT_CACHE_USED: {shell_cmd}")
                
                # Execute the command
                ret, out, err = run_shell_command(shell_cmd)
                if out:
                    console.print(Text(out, style="green"))
                if err:
                    console.print(Text(err, style="red"))
                
                # Show explanation for natural language prompts if not already shown from git cache
                if was_natural_prompt and not git_explanation_shown:
                    console.print(Panel(Text(explanation, style="cyan"), title="[Explanation]"))
                
                log_entry(f"NL_CMD: {user_input}\nSHELL: {shell_cmd}\nOUT: {out}\nERR: {err}\nEXPLAIN: {explanation}")
            elif choice == "edit":
                edited = Prompt.ask("Edit command", default=shell_cmd)
                stats.add(edited)
                explanation2 = explain_command(edited)
                console.print(Text(explanation2, style="cyan"))
                ret2, out2, err2 = run_shell_command(edited)
                if out2:
                    console.print(Text(out2, style="green"))
                if err2:
                    console.print(Text(err2, style="red"))
                log_entry(f"EDITED_NL_CMD: {edited}\nOUT: {out2}\nERR: {err2}\nEXPLAIN: {explanation2}")
                
                # Save successful edited commands to dataset for future use
                if ret2 == 0:
                    dataset.add(user_input, edited, explanation2)
            elif choice == "related":
                related = suggest_related_commands(user_input)
                console.print(Panel(Text(related, style="yellow"), title="[Related Commands]"))
    
    # Save session data on exit
    session_manager.save_session()
    console.print(f"[bold magenta]Session log saved. Goodbye!")