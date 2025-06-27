#!/usr/bin/env python3
"""
Test script for iTerminal's real-time command suggestions.
This demonstrates the enhanced suggestion system with fuzzy matching and AI fallback.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from iterminal.suggest import SmartAutoSuggest, CommandCompleter
from iterminal.dataset import Dataset
from iterminal.stats import UsageStats
from rich.console import Console
from rich.panel import Panel

console = Console()

def create_test_dataset():
    """Create a test dataset with sample commands"""
    dataset = Dataset()
    
    # Add some test entries
    test_entries = [
        ("update system", "sudo apt update && sudo apt upgrade", "Updates all system packages"),
        ("show processes", "ps aux", "Shows all running processes"),
        ("list files", "ls -la", "Lists all files in current directory"),
        ("find python files", "find . -name '*.py'", "Finds all Python files"),
        ("check disk space", "df -h", "Shows disk space usage"),
        ("install package", "sudo apt install package-name", "Installs a package"),
        ("git status", "git status", "Shows git repository status"),
        ("backup files", "tar -czf backup.tar.gz directory", "Creates a backup archive"),
        ("search text", "grep -r 'search-term' .", "Searches for text in files"),
        ("monitor system", "htop", "Interactive system monitor")
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
        "tar -czf backup.tar.gz"
    ]
    
    for cmd in test_commands:
        stats.add(cmd)
        # Add some commands multiple times to simulate usage
        if cmd in ["ls -la", "git status", "ps aux"]:
            for _ in range(5):
                stats.add(cmd)
    
    return stats

def test_smart_auto_suggest():
    """Test the SmartAutoSuggest functionality"""
    
    console.print(Panel("[bold green]Testing SmartAutoSuggest Real-time Suggestions[/bold green]", border_style="green"))
    
    # Create test data
    dataset = create_test_dataset()
    stats = create_test_stats()
    
    # Create SmartAutoSuggest instance
    auto_suggest = SmartAutoSuggest(dataset, stats)
    
    # Test cases with different types of input
    test_cases = [
        ("upda", "Typo/partial match for 'update'"),
        ("show", "Natural language for 'show processes'"),
        ("list", "Natural language for 'list files'"),
        ("find", "Natural language for 'find python files'"),
        ("check", "Natural language for 'check disk space'"),
        ("instal", "Typo for 'install'"),
        ("git", "Direct command match"),
        ("backup", "Natural language for 'backup files'"),
        ("search", "Natural language for 'search text'"),
        ("monitor", "Natural language for 'monitor system'"),
        ("xyz", "Unknown input - should trigger AI fallback"),
        ("do something", "Vague input - should trigger AI fallback")
    ]
    
    for input_text, description in test_cases:
        console.print(f"\n[bold blue]Input:[/bold blue] [cyan]'{input_text}'[/cyan] - {description}")
        
        # Get suggestions
        suggestions = auto_suggest._get_suggestions(input_text)
        
        if suggestions:
            console.print("  [bold]Suggestions:[/bold]")
            for i, suggestion in enumerate(suggestions[:3], 1):  # Show top 3
                source_icons = {
                    'dataset': '��',
                    'stats': '🔥',
                    'fuzzy': '🔍',
                    'context': '💡',
                    'ai': '🤖',
                    'ai_context': '🤖'
                }
                
                icon = source_icons.get(suggestion['source'], '🔧')
                command = suggestion['command']
                score = suggestion['score']
                source = suggestion['source']
                
                # Add explanation if available
                if 'explanation' in suggestion:
                    display_text = f"  {i}. {icon} [green]{command}[/green] ({suggestion['explanation'][:40]}...) [dim][{source}: {score}][/dim]"
                elif 'usage_count' in suggestion:
                    display_text = f"  {i}. {icon} [green]{command}[/green] (used {suggestion['usage_count']} times) [dim][{source}: {score}][/dim]"
                else:
                    display_text = f"  {i}. {icon} [green]{command}[/green] [dim][{source}: {score}][/dim]"
                
                console.print(display_text)
        else:
            console.print("  [yellow]No suggestions found[/yellow]")

def test_command_completer():
    """Test the CommandCompleter functionality"""
    
    console.print(Panel("[bold green]Testing CommandCompleter Tab Completion[/bold green]", border_style="green"))
    
    # Create test data
    dataset = create_test_dataset()
    stats = create_test_stats()
    
    # Create CommandCompleter instance
    completer = CommandCompleter(dataset, stats)
    
    # Test cases for tab completion
    test_cases = [
        ("upda", "Tab completion for 'update'"),
        ("show", "Tab completion for 'show processes'"),
        ("git", "Tab completion for 'git status'"),
        ("ls", "Tab completion for 'ls -la'"),
        ("find", "Tab completion for 'find python files'")
    ]
    
    for input_text, description in test_cases:
        console.print(f"\n[bold blue]Input:[/bold blue] [cyan]'{input_text}'[/cyan] - {description}")
        
        # Simulate document for completion
        from prompt_toolkit.document import Document
        doc = Document(input_text, len(input_text))
        
        # Get completions
        completions = list(completer.get_completions(doc, None))
        
        if completions:
            console.print("  [bold]Completions:[/bold]")
            for i, completion in enumerate(completions[:3], 1):  # Show top 3
                console.print(f"  {i}. {completion.display}")
        else:
            console.print("  [yellow]No completions found[/yellow]")

def test_fuzzy_matching():
    """Test fuzzy matching functionality"""
    
    console.print(Panel("[bold green]Testing Fuzzy Matching[/bold green]", border_style="green"))
    
    # Test cases for fuzzy matching
    test_cases = [
        ("upadte", "update"),
        ("systm", "system"),
        ("instal", "install"),
        ("proces", "process"),
        ("backup", "backup"),
        ("monitor", "monitor")
    ]
    
    for typo, correct in test_cases:
        console.print(f"\n[bold blue]Typo:[/bold blue] [red]'{typo}'[/red] → [green]'{correct}'[/green]")
        
        # Test with fuzzy matching if available
        try:
            from fuzzywuzzy import fuzz
            score = fuzz.partial_ratio(typo.lower(), correct.lower())
            console.print(f"  [dim]Fuzzy match score: {score}[/dim]")
        except ImportError:
            console.print("  [yellow]Fuzzy matching not available (fuzzywuzzy not installed)[/yellow]")

def show_usage_instructions():
    """Show usage instructions for the new features"""
    
    console.print(Panel(
        "[bold green]Real-time Command Suggestions - Usage Guide[/bold green]\n\n"
        "[bold]Features:[/bold]\n"
        "• 📚 Dataset suggestions (from learned commands)\n"
        "• 🔥 Usage-based suggestions (from command history)\n"
        "• 🔍 Fuzzy matching (handles typos and partial input)\n"
        "• 💡 Context-based suggestions (based on keywords)\n"
        "• 🤖 AI fallback suggestions (when no good matches)\n\n"
        "[bold]How to use:[/bold]\n"
        "• Type commands naturally: 'upda' → 'sudo apt update && sudo apt upgrade'\n"
        "• Use Tab for completion: Type 'git' then Tab\n"
        "• Use → arrow to accept suggestions: Type 'show' then →\n"
        "• Suggestions appear in real-time as you type\n"
        "• Commands are learned and remembered automatically\n\n"
        "[bold]Keyboard shortcuts:[/bold]\n"
        "• Tab: Cycle through completions\n"
        "• Shift+Tab: Reverse cycle through completions\n"
        "• → (Right arrow): Accept current suggestion\n"
        "• ↑/↓: Navigate command history\n"
        "• Ctrl+R: Search command history",
        border_style="blue"
    ))

if __name__ == "__main__":
    try:
        test_smart_auto_suggest()
        test_command_completer()
        test_fuzzy_matching()
        show_usage_instructions()
        
        console.print(Panel(
            "[bold green]Test completed![/bold green]\n\n"
            "The enhanced suggestion system now includes:\n"
            "• Real-time command suggestions as you type\n"
            "• Fuzzy matching for typos and partial input\n"
            "• AI fallback when no good matches found\n"
            "• Priority-based suggestion ranking\n"
            "• Visual indicators for suggestion sources\n\n"
            "Try running 'python iterminal.py' and test the new features!",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(f"[red]Error during testing: {e}[/red]")
        console.print("[yellow]Make sure you have installed the required dependencies:[/yellow]")
        console.print("[cyan]pip install fuzzywuzzy python-Levenshtein[/cyan]")
