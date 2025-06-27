#!/usr/bin/env python3
"""
Test script for iTerminal's smart command generation functionality.
This demonstrates how the system handles wrong or unclear prompts.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from iterminal.ai import (
    smart_command_generation, 
    suggest_common_commands_for_context,
    handle_ambiguous_prompt,
    correct_typos_and_suggest,
    generate_multiple_interpretations
)
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

def test_smart_commands():
    """Test various unclear or wrong prompts"""
    
    test_cases = [
        "upadte systm",  # Typos
        "show me stuff",  # Vague
        "do the thing",   # Unclear
        "fix computer",   # Ambiguous
        "make it work",   # Too generic
        "list files",     # Clear but test context
        "kill process",   # Context-based
        "find something", # Vague search
        "check status",   # Ambiguous status
        "run program"     # Generic
    ]
    
    console.print(Panel("[bold green]iTerminal Smart Command Generation Test[/bold green]", border_style="green"))
    console.print("Testing how the system handles unclear or wrong prompts...\n")
    
    for i, test_input in enumerate(test_cases, 1):
        console.print(f"[bold blue]Test {i}:[/bold blue] [cyan]'{test_input}'[/cyan]")
        
        # Test smart command generation
        result = smart_command_generation(test_input)
        
        console.print(f"  Method: [yellow]{result['method']}[/yellow]")
        console.print(f"  Command: [green]{result['command']}[/green]")
        console.print(f"  Explanation: [dim]{result['explanation']}[/dim]")
        
        if result.get('alternatives'):
            console.print("  Alternatives:")
            for j, alt in enumerate(result['alternatives'][:2], 1):
                console.print(f"    {j}. [cyan]{alt}[/cyan]")
        
        # Test context suggestions
        context_suggestions = suggest_common_commands_for_context(test_input)
        if context_suggestions:
            console.print("  Context suggestions:")
            for j, suggestion in enumerate(context_suggestions[:2], 1):
                console.print(f"    {j}. [green]{suggestion}[/green]")
        
        console.print()  # Empty line between tests

def test_typo_correction():
    """Test typo correction functionality"""
    
    console.print(Panel("[bold green]Typo Correction Test[/bold green]", border_style="green"))
    
    typos = [
        "upadte systm",
        "proces list", 
        "instal package",
        "restart servic",
        "check disk usag"
    ]
    
    for typo in typos:
        console.print(f"[bold blue]Input:[/bold blue] [cyan]'{typo}'[/cyan]")
        result = correct_typos_and_suggest(typo)
        
        console.print(f"  Corrected: [green]'{result['corrected_input']}'[/green]")
        console.print(f"  Command: [yellow]{result['command']}[/yellow]")
        console.print(f"  Confidence: [blue]{result['confidence']:.2f}[/blue]")
        console.print()

def test_ambiguous_prompts():
    """Test ambiguous prompt handling"""
    
    console.print(Panel("[bold green]Ambiguous Prompt Test[/bold green]", border_style="green"))
    
    ambiguous = [
        "show me everything",
        "fix it",
        "do something useful",
        "check the system",
        "make it better"
    ]
    
    for prompt in ambiguous:
        console.print(f"[bold blue]Input:[/bold blue] [cyan]'{prompt}'[/cyan]")
        result = handle_ambiguous_prompt(prompt)
        
        console.print(f"  Primary: [green]{result['primary_command']}[/green]")
        console.print(f"  Interpretation: [dim]{result['interpretation']}[/dim]")
        console.print(f"  Confidence: [blue]{result['confidence']:.2f}[/blue]")
        
        if result.get('alternatives'):
            console.print("  Alternatives:")
            for i, alt in enumerate(result['alternatives'][:2], 1):
                console.print(f"    {i}. [cyan]{alt}[/cyan]")
        
        console.print()

if __name__ == "__main__":
    try:
        test_smart_commands()
        test_typo_correction()
        test_ambiguous_prompts()
        
        console.print(Panel(
            "[bold green]Test completed![/bold green]\n\n"
            "The enhanced iTerminal now includes:\n"
            "• Smart command generation for unclear prompts\n"
            "• Automatic typo correction\n"
            "• Multiple interpretation attempts\n"
            "• Context-based command suggestions\n"
            "• Interactive prompt fixing with 'fix' command\n\n"
            "Try running 'python iterminal.py' and test with unclear inputs!",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(f"[red]Error during testing: {e}[/red]")
        console.print("[yellow]Make sure you have set up your OpenRouter API key in .env file[/yellow]") 