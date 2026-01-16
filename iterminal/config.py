import os
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt

load_dotenv()
console = Console()

ENV_PATH = '.env'

# Plugin mode: if set, skip blocking of most commands (only block kernel modification cmds)
PLUGIN_MODE = os.environ.get('ITERMINAL_PLUGIN_MODE', '0') == '1'

# Filter apt warnings: if set, filter out the "WARNING: apt does not have a stable CLI interface" message
FILTER_APT_WARNINGS = os.environ.get('ITERMINAL_FILTER_APT_WARNINGS', '1') == '1'

# Performance and threading settings
CACHE_ENABLED = os.environ.get('ITERMINAL_CACHE_ENABLED', '1') == '1'
PERFORMANCE_MODE = os.environ.get('ITERMINAL_PERFORMANCE_MODE', '1') == '1' 
REDUCED_CONTEXT = os.environ.get('ITERMINAL_REDUCED_CONTEXT', '1') == '1'
HYPERTHREAD_ENABLED = os.environ.get('ITERMINAL_HYPERTHREAD_ENABLED', 'true').lower() == 'true'

# AI provider configuration
def refresh_env():
    """Refresh environment variables from .env file"""
    load_dotenv(override=True)

def get_ai_provider():
    """Get the current AI provider from environment variable or default"""
    return os.environ.get('ITERMINAL_AI_PROVIDER', 'openrouter').lower()

AI_PROVIDER = get_ai_provider()  # 'ollama' or 'openrouter'
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3')  # Default model for Ollama

# Function to update the Ollama model name in environment
def update_ollama_model(model_name):
    """Update the Ollama model name in the environment and globals"""
    global OLLAMA_MODEL
    OLLAMA_MODEL = model_name
    os.environ['OLLAMA_MODEL'] = model_name

def get_ollama_status():
    """Check if Ollama server is available"""
    try:
        import requests
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        if response.status_code == 200:
            available_models = [model['name'] for model in response.json().get('models', [])]
            
            # Check if the model matches exactly or if base model name is present
            model_found = False
            base_model = OLLAMA_MODEL.split(':')[0] if ':' in OLLAMA_MODEL else OLLAMA_MODEL
            
            if OLLAMA_MODEL in available_models:
                model_found = True
                return True, f"Ollama running with {OLLAMA_MODEL} model available"
            
            # Check if we can find any version of the base model
            matching_models = [m for m in available_models if m.startswith(f"{base_model}:") or m == base_model]
            if matching_models:
                # Use the first available version and update the model name
                detected_model = matching_models[0]
                update_ollama_model(detected_model)
                return True, f"Ollama running with {detected_model} model selected"
            elif available_models:
                return True, f"Ollama running, but {OLLAMA_MODEL} not found. Available models: {', '.join(available_models[:3])}"
            else:
                return False, "Ollama running but no models available"
        else:
            return False, f"Ollama server returned status code {response.status_code}"
    except Exception as e:
        return False, f"Ollama server not available: {str(e)}"

def set_ai_provider(provider: str):
    """Set the AI provider in the environment and .env file"""
    if provider.lower() not in ['openrouter', 'ollama']:
        return False
        
    # Direct approach - set environment variable first
    os.environ['ITERMINAL_AI_PROVIDER'] = provider.lower()
    
    # Update or create .env file
    if os.path.exists(ENV_PATH):
        # Read existing content
        with open(ENV_PATH, 'r') as f:
            lines = f.readlines()
        
        # Update or append setting
        found = False
        for i, line in enumerate(lines):
            if line.strip().startswith('ITERMINAL_AI_PROVIDER='):
                lines[i] = f"ITERMINAL_AI_PROVIDER={provider.lower()}\n"
                found = True
                break
        
        if not found:
            lines.append(f"ITERMINAL_AI_PROVIDER={provider.lower()}\n")
            
        # Write back to file
        with open(ENV_PATH, 'w') as f:
            f.writelines(lines)
    else:
        # Create new file
        with open(ENV_PATH, 'w') as f:
            f.write(f"ITERMINAL_AI_PROVIDER={provider.lower()}\n")
    
    # Log for debugging
    print(f"Provider set to {provider.lower()}")
    
    return True

def configure_ollama():
    """Configure Ollama settings"""
    global OLLAMA_BASE_URL, OLLAMA_MODEL
    
    # Check current Ollama status
    status, message = get_ollama_status()
    if status:
        console.print(f"[green]✓ {message}[/green]")
    else:
        console.print(f"[yellow]⚠ {message}[/yellow]")
        console.print("[yellow]You may need to install Ollama or start the Ollama server.[/yellow]")
        console.print("[cyan]Visit https://ollama.com for installation instructions.[/cyan]")

    # Get custom URL if needed
    url = Prompt.ask("Ollama server URL", default=OLLAMA_BASE_URL)
    if url != OLLAMA_BASE_URL:
        with open(ENV_PATH, 'a') as f:
            f.write(f"\nOLLAMA_BASE_URL={url}\n")
        os.environ['OLLAMA_BASE_URL'] = url
        OLLAMA_BASE_URL = url
    
    # Get custom model if needed
    model = Prompt.ask("Ollama model to use", default=OLLAMA_MODEL)
    if model != OLLAMA_MODEL:
        with open(ENV_PATH, 'a') as f:
            f.write(f"\nOLLAMA_MODEL={model}\n")
        os.environ['OLLAMA_MODEL'] = model
        OLLAMA_MODEL = model
    
    load_dotenv(override=True)
    console.print("[green]Ollama configuration saved![/green]")
    return True


def get_api_key():
    # If using Ollama, no API key is needed
    if AI_PROVIDER == 'ollama':
        return "ollama"  # Not actually used but prevents API key prompt
        
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