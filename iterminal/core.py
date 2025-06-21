from rich.console import Console
from rich.prompt import Prompt
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from .shell import is_probably_shell_command, run_shell_command
from .ai import explain_command, translate_nl_to_shell, correct_shell_command, suggest_related_commands
from .logger import log_entry
from .config import get_api_key
from .dataset import Dataset
from .suggest import get_user_input
from .stats import UsageStats
import os

console = Console()

# Command aliases for common tasks
COMMAND_ALIASES = {
    'help': 'show help information',
    'history': 'show command history',
    'clear': 'clear the terminal',
    'stats': 'show usage statistics',
    'dataset': 'show learned commands',
    'suggest': 'get command suggestions'
}

def confirm_command(cmd: str, explanation: str) -> str:
    console.print(Panel(Text(cmd, style="bold yellow"), title="[AI Suggestion]"))
    console.print(Text(explanation, style="italic cyan"))
    return Prompt.ask("Run this command?", choices=["Y", "n", "edit", "related"], default="Y")

def show_help():
    """Display help information"""
    help_text = """
[bold green]iTerminal Help[/bold green]

[bold]Basic Usage:[/bold]
• Type Linux commands directly: [cyan]ls -la[/cyan]
• Use natural language: [cyan]show me running processes[/cyan]
• Get command explanations automatically

[bold]Navigation:[/bold]
• [cyan]↑/↓ arrows[/cyan] - Navigate command history
• [cyan]Tab[/cyan] - Auto-complete commands and file paths
• [cyan]Ctrl+R[/cyan] - Search command history
• [cyan]Mouse[/cyan] - Click to position cursor

[bold]Special Commands:[/bold]
• [cyan]help[/cyan] - Show this help
• [cyan]history[/cyan] - Show command history
• [cyan]exit[/cyan] - Exit iTerminal

[bold]AI Features:[/bold]
• Automatic command correction
• Natural language translation
• Command explanations
• Related command suggestions

[bold]Tips:[/bold]
• Commands are automatically learned and remembered
• Interactive programs (nano, vim) work in regular terminal
• Use Tab for file path completion: [cyan]cat /home/sai/Doc[Tab][/cyan]
"""
    console.print(Panel(help_text, title="[Help]", border_style="green"))

def show_history(dataset: Dataset, stats: UsageStats):
    """Show command history"""
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
    """Show usage statistics"""
    if hasattr(stats, 'usage') and stats.usage:
        total_commands = sum(stats.usage.values())
        unique_commands = len(stats.usage)
        
        console.print(Panel(
            f"[bold]Total Commands:[/bold] {total_commands}\n"
            f"[bold]Unique Commands:[/bold] {unique_commands}\n"
            f"[bold]Most Used:[/bold] {max(stats.usage.items(), key=lambda x: x[1])[0]}",
            title="[Usage Statistics]"
        ))
    else:
        console.print("[yellow]No usage statistics available yet.[/yellow]")

def show_dataset(dataset: Dataset):
    """Show learned commands"""
    if hasattr(dataset, 'data') and dataset.data:
        table = Table(title="Learned Commands")
        table.add_column("Natural Language", style="cyan")
        table.add_column("Command", style="yellow")
        table.add_column("Explanation", style="green")
        
        for item in dataset.data[-10:]:  # Last 10 learned commands
            table.add_row(item['prompt'], item['command'], item['explanation'][:50] + "...")
        
        console.print(table)
    else:
        console.print("[yellow]No commands learned yet.[/yellow]")

def main_loop():
    get_api_key()  # Ensure API key is set
    dataset = Dataset()
    stats = UsageStats()
    console.print("[bold green]Welcome to iTerminal! Type your command or ask in plain English. Type 'exit' or Ctrl-D to quit.[/bold green]")
    console.print("[dim]Type 'help' for more information[/dim]")
    
    while True:
        try:
            user_input = get_user_input(dataset, stats, prompt_text="[bold blue]iTerminal >[/bold blue] ")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[bold red]Exiting iTerminal. Goodbye!")
            break
        if not user_input.strip():
            continue
        if user_input.strip().lower() in ("exit", "quit"):  # Exit
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
        elif user_input.strip().lower() == 'clear':
            console.clear()
            continue
        
        # 1. Try as shell command
        if is_probably_shell_command(user_input):
            stats.add(user_input)
            ret, out, err = run_shell_command(user_input)
            if ret == 0:
                if out:
                    console.print(Text(out, style="green"))
                explanation = explain_command(user_input)
                console.print(Panel(Text(explanation, style="cyan"), title="[Explanation]"))
                log_entry(f"CMD: {user_input}\nOUT: {out}\nEXPLAIN: {explanation}")
            else:
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
    
    console.print(f"[bold magenta]Session log saved.") 