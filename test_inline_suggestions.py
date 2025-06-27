#!/usr/bin/env python3
"""
Test script for iTerminal's inline command suggestions.
This demonstrates the ghost-text style suggestions that appear as you type.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from iterminal.suggest import SmartAutoSuggest, get_user_input
from iterminal.dataset import Dataset
from iterminal.stats import UsageStats
from rich.console import Console
from rich.panel import Panel

console = Console()

def create_test_dataset():
    """Create a test dataset with sample commands"""
    dataset = Dataset()
    
    # Add some test entries for inline suggestions
    test_entries = [
        ("update system", "sudo apt update && sudo apt upgrade", "Updates all system packages"),
        ("check memory", "free -h", "Shows memory usage"),
        ("list files", "ls -la", "Lists all files in current directory"),
        ("find python", "find . -name '*.py'", "Finds all Python files"),
        ("check disk", "df -h", "Shows disk space usage"),
        ("install package", "sudo apt install package-name", "Installs a package"),
        ("git status", "git status", "Shows git repository status"),
        ("backup files", "tar -czf backup.tar.gz directory", "Creates a backup archive"),
        ("search text", "grep -r 'search-term' .", "Searches for text in files"),
        ("monitor system", "htop", "Interactive system monitor"),
        ("show processes", "ps aux", "Shows all running processes"),
        ("check network", "netstat -tuln", "Shows network connections"),
        ("clean system", "sudo apt autoremove", "Removes unused packages"),
        ("restart service", "sudo systemctl restart service-name", "Restarts a service"),
        ("check logs", "journalctl -f", "Shows system logs")
    ]
    
    for prompt, command, explanation in test_entries:
        dataset.add(prompt, command, explanation)
    
    return dataset

def create_test_stats():
    """Create test usage statistics"""
    stats = UsageStats()
    
    # Add some frequently used commands
    test_commands = [
        "ls -la", "sudo apt update", "git status", "ps aux", "df -h",
        "find . -name '*.py'", "grep -r 'term' .", "htop", "sudo apt install",
        "tar -czf backup.tar.gz", "free -h", "netstat -tuln"
    ]
    
    for cmd in test_commands:
        stats.add(cmd)
        # Add some commands multiple times to simulate usage
        if cmd in ["ls -la", "git status", "ps aux"]:
            for _ in range(5):
                stats.add(cmd)
    
    return stats

def test_inline_suggestions():
    """Test the inline suggestion functionality"""
    
    console.print(Panel("[bold green]Testing Inline Command Suggestions[/bold green]", border_style="green"))
    
    # Create test data
    dataset = create_test_dataset()
    stats = create_test_stats()
    
    # Create SmartAutoSuggest instance
    auto_suggest = SmartAutoSuggest(dataset, stats)
    
    # Test cases for inline suggestions
    test_cases = [
        ("upda", "Should suggest: 'te system' (from 'update system')"),
        ("check", "Should suggest: ' memory' or ' disk' (from dataset)"),
        ("list", "Should suggest: ' files' (from 'list files')"),
        ("find", "Should suggest: ' python' (from 'find python')"),
        ("git", "Should suggest: ' status' (from 'git status')"),
        ("backup", "Should suggest: ' files' (from 'backup files')"),
        ("search", "Should suggest: ' text' (from 'search text')"),
        ("monitor", "Should suggest: ' system' (from 'monitor system')"),
        ("show", "Should suggest: ' processes' (from 'show processes')"),
        ("restart", "Should suggest: ' service' (from 'restart service')")
    ]
    
    for input_text, description in test_cases:
        console.print(f"\n[bold blue]Input:[/bold blue] [cyan]'{input_text}'[/cyan]")
        console.print(f"[dim]{description}[/dim]")
        
        # Get suggestions
        suggestions = auto_suggest._get_suggestions(input_text)
        
        if suggestions:
            console.print("  [bold]Inline suggestions:[/bold]")
            for i, suggestion in enumerate(suggestions[:3], 1):  # Show top 3
                source_icons = {
                    'dataset': '📚',
                    'stats': '🔥',
                    'fuzzy': '🔍',
                    'context': '💡',
                    'ai': '🤖',
                    'ai_context': '🤖'
                }
                
                icon = source_icons.get(suggestion['source'], '🔧')
                command = suggestion['command']
                score = suggestion['score']
                
                # Calculate what would be shown as inline text
                if input_text.lower() in command.lower():
                    idx = command.lower().find(input_text.lower())
                    if idx == 0:
                        inline_text = command[len(input_text):]
                        if inline_text:
                            display_text = f"  {i}. {icon} [green]'{inline_text}'[/green] (from '{command}') [{score}]"
                        else:
                            display_text = f"  {i}. {icon} [green]'{command}'[/green] [{score}]"
                    else:
                        display_text = f"  {i}. {icon} [green]'{command}'[/green] [{score}]"
                else:
                    display_text = f"  {i}. {icon} [green]'{command}'[/green] [{score}]"
                
                console.print(display_text)
        else:
            console.print("  [yellow]No inline suggestions found[/yellow]")

def show_usage_instructions():
    """Show usage instructions for inline suggestions"""
    
    console.print(Panel(
        "[bold green]Inline Command Suggestions - Usage Guide[/bold green]\n\n"
        "[bold]How it works:[/bold]\n"
        "• Type commands and see ghost-text suggestions appear inline\n"
        "• Suggestions show only the remaining part you haven't typed\n"
        "• Example: Type 'upda' → see 'te system' as ghost-text\n"
        "• Example: Type 'check' → see ' memory' as ghost-text\n\n"
        "[bold]Keyboard shortcuts:[/bold]\n"
        "• [cyan]Tab[/cyan]: Accept the current inline suggestion\n"
        "• [cyan]→ (Right arrow)[/cyan]: Accept the current inline suggestion\n"
        "• [cyan]Ctrl+Space[/cyan]: Show all available completions\n"
        "• [cyan]Shift+Tab[/cyan]: Cycle through completions in reverse\n\n"
        "[bold]Suggestion sources:[/bold]\n"
        "• 📚 Dataset: From your learned commands\n"
        "• 🔥 Stats: From your command history\n"
        "• 🔍 Fuzzy: Fuzzy matching for typos\n"
        "• 💡 Context: Context-based suggestions\n"
        "• 🤖 AI: AI-generated suggestions\n\n"
        "[bold]Try these examples:[/bold]\n"
        "• Type 'upda' → should suggest 'te system'\n"
        "• Type 'check' → should suggest ' memory' or ' disk'\n"
        "• Type 'git' → should suggest ' status'\n"
        "• Type 'list' → should suggest ' files'",
        border_style="blue"
    ))

def interactive_demo():
    """Interactive demo of inline suggestions"""
    
    console.print(Panel(
        "[bold green]Interactive Inline Suggestions Demo[/bold green]\n\n"
        "This will start an interactive session where you can test inline suggestions.\n"
        "Type partial commands and see ghost-text suggestions appear.\n\n"
        "[bold]Try these examples:[/bold]\n"
        "• upda (should suggest 'te system')\n"
        "• check (should suggest ' memory')\n"
        "• git (should suggest ' status')\n"
        "• list (should suggest ' files')\n\n"
        "Press Tab or → to accept suggestions.\n"
        "Type 'exit' to quit the demo.",
        border_style="green"
    ))
    
    # Create test data
    dataset = create_test_dataset()
    stats = create_test_stats()
    
    try:
        # Start interactive session
        result = get_user_input(dataset, stats, "[bold blue]Demo >[/bold blue] ")
        console.print(f"[green]You entered:[/green] {result}")
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted.[/yellow]")

if __name__ == "__main__":
    try:
        test_inline_suggestions()
        show_usage_instructions()
        
        console.print(Panel(
            "[bold green]Test completed![/bold green]\n\n"
            "The inline suggestion system now provides:\n"
            "• Ghost-text suggestions as you type\n"
            "• Smart partial text completion\n"
            "• Multiple suggestion sources\n"
            "• Tab and arrow key acceptance\n\n"
            "Would you like to try the interactive demo? (y/n): ",
            border_style="green"
        ))
        
        choice = input().lower().strip()
        if choice in ['y', 'yes']:
            interactive_demo()
        
    except Exception as e:
        console.print(f"[red]Error during testing: {e}[/red]")
        console.print("[yellow]Make sure you have installed the required dependencies:[/yellow]")
        console.print("[cyan]pip install prompt_toolkit fuzzywuzzy python-Levenshtein[/cyan]")
