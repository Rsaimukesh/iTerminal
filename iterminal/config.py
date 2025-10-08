import os
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt

load_dotenv()
console = Console()

ENV_PATH = '.env'

# Plugin mode: if set, skip blocking of most commands (only block kernel modification cmds)
PLUGIN_MODE = os.environ.get('ITERMINAL_PLUGIN_MODE', '0') == '1'


def get_api_key():
    api_key = os.environ.get('OPENROUTER_API_KEY', None)
    if not api_key:
        console.print("[bold yellow]No OpenRouter API key found. Please paste your API key (it will be saved to .env):[/bold yellow]")
        key = Prompt.ask("Enter your OpenRouter API key", password=True)
        with open(ENV_PATH, 'a') as f:
            f.write(f"\nOPENROUTER_API_KEY={key}\n")
        load_dotenv(override=True)
        api_key = os.environ.get('OPENROUTER_API_KEY', None)
        if api_key:
            console.print("[green]API key saved to .env![/green]")
        else:
            console.print("[red]Failed to save API key. Please check .env permissions.[/red]")
    return api_key 