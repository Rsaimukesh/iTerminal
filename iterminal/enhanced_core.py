from rich.console import Console
from rich.prompt import Prompt
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from .shell import is_probably_shell_command, run_shell_command
from .ai import explain_command, translate_nl_to_shell, correct_shell_command, suggest_related_commands, analyze_command_safety, get_command_complexity
from .logger import log_entry
from .config import get_api_key
from .dataset import Dataset
from .suggest import get_user_input
from .stats import UsageStats
import os
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional

console = Console()

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
            'duration': str(duration).split('.')[0],
            'commands_executed': self.commands_executed,
            'ai_queries': self.ai_queries,
            'errors_encountered': self.errors_encountered,
            'success_rate': ((self.commands_executed - self.errors_encountered) / max(self.commands_executed, 1)) * 100
        }

def confirm_command(cmd: str, explanation: str, safety_analysis: Optional[Dict[str, Any]] = None) -> str:
    """Enhanced command confirmation with safety analysis"""
    panel_content = f"[bold yellow]{cmd}[/bold yellow]\n\n[italic cyan]{explanation}[/italic cyan]"
    
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
        elif risk_level == 'medium':
            panel_content += f"\n\n[yellow]⚠️  RISK LEVEL: {risk_level.upper()}[/yellow]"
            if warning:
                panel_content += f"\n[yellow]{warning}[/yellow]"
    
    console.print(Panel(panel_content, title="[AI Suggestion]", border_style="yellow"))
    
    choices = ["Y", "n", "edit", "related", "safety"]
    if safety_analysis and safety_analysis.get('requires_confirmation', False):
        choices.append("force")
    
    return Prompt.ask("Run this command?", choices=choices, default="Y")

def show_enhanced_help():
    """Enhanced help display with more detailed information"""
    help_text = """
[bold green]iTerminal Enhanced Help[/bold green]

[bold]Basic Usage:[/bold]
• Type Linux commands directly: [cyan]ls -la[/cyan]
• Use natural language: [cyan]show me running processes[/cyan]
• Get command explanations automatically
• Safety analysis for potentially dangerous commands

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
• Safety-aware suggestions

[bold]Special Commands:[/bold]
• [cyan]help[/cyan] - Show this help
• [cyan]history[/cyan] - Show command history
• [cyan]stats[/cyan] - Show usage statistics
• [cyan]dataset[/cyan] - Show learned commands
• [cyan]session[/cyan] - Show session information
• [cyan]safety[/cyan] - Analyze command safety
• [cyan]export[/cyan] - Export command history
• [cyan]clear[/cyan] - Clear terminal
• [cyan]exit[/cyan] - Exit iTerminal

[bold]AI Features:[/bold]
• Automatic command correction
• Natural language translation
• Command explanations with complexity levels
• Related command suggestions
• Safety analysis and warnings
• Response caching for faster performance

[bold]Safety Features:[/bold]
• Automatic risk assessment
• Warning for dangerous commands
• Safer alternative suggestions
• Confirmation prompts for risky operations

[bold]Tips:[/bold]
• Commands are automatically learned and remembered
• Interactive programs (nano, vim) work in regular terminal
• Use Tab for file path completion: [cyan]cat /home/sai/Doc[Tab][/cyan]
• Type partial commands to see smart suggestions
• Natural language triggers contextual suggestions
• Session data is automatically saved and restored
"""
    console.print(Panel(help_text, title="[Enhanced Help]", border_style="green"))

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

def enhanced_main_loop():
    """Enhanced main loop with better session management and error handling"""
    get_api_key()  # Ensure API key is set
    dataset = Dataset()
    stats = UsageStats()
    session_manager = SessionManager()
    
    # Welcome message with session info
    console.print("[bold green]Welcome to iTerminal Enhanced! Type your command or ask in plain English. Type 'exit' or Ctrl-D to quit.[/bold green]")
    console.print("[dim]Type 'help' for more information[/dim]")
    
    # Show session info if returning user
    if session_manager.commands_executed > 0:
        session_stats = session_manager.get_session_stats()
        console.print(f"[dim]Welcome back! You've executed {session_stats['commands_executed']} commands with {session_stats['success_rate']:.1f}% success rate.[/dim]")
    
    while True:
        try:
            user_input = get_user_input(dataset, stats, prompt_text="[bold blue]iTerminal Enhanced >[/bold blue] ")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[bold red]Exiting iTerminal Enhanced. Goodbye!")
            session_manager.save_session()
            break
        
        if not user_input.strip():
            continue
        
        if user_input.strip().lower() in ("exit", "quit"):  # Exit
            session_manager.save_session()
            break
        
        # Handle help command
        if user_input.strip().lower() == 'help':
            show_enhanced_help()
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
            show_dataset(dataset)
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
        
        # 1. Try as shell command
        if is_probably_shell_command(user_input):
            session_manager.commands_executed += 1
            
            # Analyze safety before execution
            safety_analysis = analyze_command_safety(user_input)
            if safety_analysis.get('requires_confirmation', False):
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
                explanation = explain_command(user_input)
                console.print(Panel(Text(explanation, style="cyan"), title="[Explanation]"))
                log_entry(f"CMD: {user_input}\nOUT: {out}\nEXPLAIN: {explanation}")
            else:
                session_manager.errors_encountered += 1
                # Error: ask AI for correction
                correction = correct_shell_command(user_input, err)
                explanation = explain_command(correction)
                console.print(f"[red]Error:[/red] {err.strip()}")
                if correction and not correction.startswith('[AI error'):
                    console.print(f"[yellow]Did you mean:[/yellow] [bold]{correction}[/bold]?")
                    console.print(Text(explanation, style="cyan"))
                    choice = Prompt.ask("Run?", choices=["Y", "n", "edit", "related"], default="Y")
                    if choice == "Y":
                        stats.add(correction)
                        ret2, out2, err2 = run_shell_command(correction)
                        if out2:
                            console.print(Text(out2, style="green"))
                        if err2:
                            console.print(Text(err2, style="red"))
                        log_entry(f"FIXED_CMD: {correction}\nOUT: {out2}\nERR: {err2}\nEXPLAIN: {explanation}")
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
                    elif choice == "related":
                        related = suggest_related_commands(user_input)
                        console.print(Panel(Text(related, style="yellow"), title="[Related Commands]"))
                else:
                    console.print("[red]No recommendation available from AI.[/red]")
        else:
            # 2. Natural language: prefer dataset before AI
            session_manager.ai_queries += 1
            dataset_result = dataset.search(user_input)
            if dataset_result:
                shell_cmd = dataset_result['command']
                explanation = dataset_result['explanation']
                console.print(Panel(Text(shell_cmd, style="bold yellow"), title="[Suggestion from Dataset]"))
                console.print(Text(explanation, style="italic cyan"))
                choice = Prompt.ask("Run this command?", choices=["Y", "n", "edit", "related"], default="Y")
            else:
                shell_cmd = translate_nl_to_shell(user_input)
                explanation = explain_command(shell_cmd)
                choice = confirm_command(shell_cmd, explanation)
                # Auto-learn: save to dataset if AI translation is successful
                if shell_cmd and not shell_cmd.startswith('[AI error'):
                    dataset.add(user_input, shell_cmd, explanation)
            
            if choice == "Y":
                stats.add(shell_cmd)
                ret, out, err = run_shell_command(shell_cmd)
                if out:
                    console.print(Text(out, style="green"))
                if err:
                    console.print(Text(err, style="red"))
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
            elif choice == "related":
                related = suggest_related_commands(user_input)
                console.print(Panel(Text(related, style="yellow"), title="[Related Commands]"))
    
    # Save session data on exit
    session_manager.save_session()
    console.print(f"[bold magenta]Session log saved. Goodbye!")

# Import existing functions for compatibility
from .core import show_help, show_history, show_stats, show_dataset, confirm_command as old_confirm_command 