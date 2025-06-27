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
import os
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional

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
    'fix': 'fix unclear or wrong prompt'
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

def confirm_command(cmd: str, explanation: str, safety_analysis: Optional[Dict[str, Any]] = None) -> str:
    """Enhanced command confirmation with safety analysis"""
    # Create a more informative panel
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
• [cyan]exit[/cyan] - Exit iTerminal

[bold]AI Features:[/bold]
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
    """Enhanced learned commands display"""
    if hasattr(dataset, 'data') and dataset.data:
        table = Table(title="Learned Commands", show_header=True, header_style="bold magenta")
        table.add_column("Natural Language", style="cyan", width=30)
        table.add_column("Command", style="yellow", width=25)
        table.add_column("Explanation", style="green", width=40)
        table.add_column("Complexity", style="blue", width=12)
        
        for item in dataset.data[-10:]:  # Last 10 learned commands
            complexity = get_command_complexity(item['command'])
            table.add_row(
                item['prompt'][:27] + "..." if len(item['prompt']) > 30 else item['prompt'],
                item['command'][:22] + "..." if len(item['command']) > 25 else item['command'],
                item['explanation'][:37] + "..." if len(item['explanation']) > 40 else item['explanation'],
                complexity.capitalize()
            )
        
        console.print(table)
    else:
        console.print("[yellow]No commands learned yet.[/yellow]")

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
        log_entry(f"UNCLEAR_PROMPT: {user_input}\nSMART_CMD: {shell_cmd}\nOUT: {out}\nERR: {err}\nEXPLAIN: {explanation}")
        
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
            except ValueError:
                console.print("[red]Invalid selection.[/red]")
    
    elif choice == "help":
        show_help()

def main_loop():
    """Enhanced main loop with better session management and error handling"""
    get_api_key()  # Ensure API key is set
    dataset = Dataset()
    stats = UsageStats()
    session_manager = SessionManager()
    
    # Welcome message with session info
    console.print("[bold green]Welcome to iTerminal! Type your command or ask in plain English. Type 'exit' or Ctrl-D to quit.[/bold green]")
    console.print("[dim]Type 'help' for more information[/dim]")
    
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
        elif user_input.strip().lower() == 'fix':
            unclear_input = Prompt.ask("Enter the unclear prompt to fix")
            handle_unclear_prompt(unclear_input, dataset, stats)
            continue
        
        # Flag tracks input type
        was_natural_prompt = False

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
                # Skip explanation for valid shell commands that executed successfully
                # Only show explanation if it was a natural language prompt or if there was an error
                log_entry(f"CMD: {user_input}\nOUT: {out}")
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
            # 2. Natural language: try smart command generation first
            was_natural_prompt = True  # Set flag for natural language input
            session_manager.ai_queries += 1
            dataset_result = dataset.search(user_input)
            if dataset_result:
                shell_cmd = dataset_result['command']
                explanation = dataset_result['explanation']
                console.print(Panel(Text(shell_cmd, style="bold yellow"), title="[Suggestion from Dataset]"))
                console.print(Text(explanation, style="italic cyan"))
                choice = Prompt.ask("Run this command?", choices=["Y", "n", "edit", "related"], default="Y")
            else:
                # Use smart command generation for unclear prompts
                smart_result = smart_command_generation(user_input)
                shell_cmd = smart_result['command']
                explanation = explain_command(shell_cmd)
                
                # If the result seems unclear or generic, offer enhanced help
                if (smart_result['method'] != 'translation' or 
                    shell_cmd in ['ls', 'pwd', 'whoami'] or 
                    shell_cmd.startswith('[AI error')):
                    handle_unclear_prompt(user_input, dataset, stats)
                    continue
                
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
                # Show explanation for natural language prompts (was_natural_prompt == True)
                if was_natural_prompt:
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
            elif choice == "related":
                related = suggest_related_commands(user_input)
                console.print(Panel(Text(related, style="yellow"), title="[Related Commands]"))
    
    # Save session data on exit
    session_manager.save_session()
    console.print(f"[bold magenta]Session log saved. Goodbye!") 