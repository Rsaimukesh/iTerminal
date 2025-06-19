from rich.console import Console
from rich.prompt import Prompt
from rich.text import Text
from rich.panel import Panel
from .shell import is_probably_shell_command, run_shell_command
from .ai import explain_command, translate_nl_to_shell, correct_shell_command
from .logger import log_entry
from .config import get_api_key

console = Console()

def confirm_command(cmd: str, explanation: str) -> str:
    console.print(Panel(Text(cmd, style="bold yellow"), title="[AI Suggestion]"))
    console.print(Text(explanation, style="italic cyan"))
    return Prompt.ask("Run this command?", choices=["Y", "n", "edit"], default="Y")

def main_loop():
    get_api_key()  # Ensure API key is set
    console.print("[bold green]Welcome to iTerminal! Type your command or ask in plain English. Type 'exit' or Ctrl-D to quit.[/bold green]")
    while True:
        try:
            user_input = Prompt.ask("[bold blue]iTerminal >[/bold blue]")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[bold red]Exiting iTerminal. Goodbye!")
            break
        if not user_input.strip():
            continue
        if user_input.strip().lower() in ("exit", "quit"):  # Exit
            break
        log_entry(f"USER: {user_input}")
        # 1. Try as shell command
        if is_probably_shell_command(user_input):
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
                    choice = Prompt.ask("Run?", choices=["Y", "n", "edit"], default="Y")
                    if choice == "Y":
                        ret2, out2, err2 = run_shell_command(correction)
                        if out2:
                            console.print(Text(out2, style="green"))
                        if err2:
                            console.print(Text(err2, style="red"))
                        log_entry(f"FIXED_CMD: {correction}\nOUT: {out2}\nERR: {err2}\nEXPLAIN: {explanation}")
                    elif choice == "edit":
                        edited = Prompt.ask("Edit command", default=correction)
                        explanation2 = explain_command(edited)
                        console.print(Text(explanation2, style="cyan"))
                        ret3, out3, err3 = run_shell_command(edited)
                        if out3:
                            console.print(Text(out3, style="green"))
                        if err3:
                            console.print(Text(err3, style="red"))
                        log_entry(f"EDITED_CMD: {edited}\nOUT: {out3}\nERR: {err3}\nEXPLAIN: {explanation2}")
                else:
                    console.print("[red]No recommendation available from AI.[/red]")
        else:
            # 2. Natural language: ask AI for shell command
            shell_cmd = translate_nl_to_shell(user_input)
            explanation = explain_command(shell_cmd)
            choice = confirm_command(shell_cmd, explanation)
            if choice == "Y":
                ret, out, err = run_shell_command(shell_cmd)
                if out:
                    console.print(Text(out, style="green"))
                if err:
                    console.print(Text(err, style="red"))
                log_entry(f"NL_CMD: {user_input}\nSHELL: {shell_cmd}\nOUT: {out}\nERR: {err}\nEXPLAIN: {explanation}")
            elif choice == "edit":
                edited = Prompt.ask("Edit command", default=shell_cmd)
                explanation2 = explain_command(edited)
                console.print(Text(explanation2, style="cyan"))
                ret2, out2, err2 = run_shell_command(edited)
                if out2:
                    console.print(Text(out2, style="green"))
                if err2:
                    console.print(Text(err2, style="red"))
                log_entry(f"EDITED_NL_CMD: {edited}\nOUT: {out2}\nERR: {err2}\nEXPLAIN: {explanation2}")
    console.print(f"[bold magenta]Session log saved.") 