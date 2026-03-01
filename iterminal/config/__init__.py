"""Configuration package initialization."""
import os
from dotenv import load_dotenv
from .settings import (
    Settings,
    PerformanceConfig,
    AIConfig,
    LoggingConfig,
    CompletionConfig,
    UIConfig,
    SecurityConfig,
    AIProviderType,
    LogLevel,
    get_settings,
    reload_settings,
)

# Legacy configuration constants and functions
load_dotenv()
ENV_PATH = '.env'

FILTER_APT_WARNINGS = os.environ.get('ITERMINAL_FILTER_APT_WARNINGS', '1') == '1'
PLUGIN_MODE = os.environ.get('ITERMINAL_PLUGIN_MODE', '0') == '1'
CACHE_ENABLED = os.environ.get('ITERMINAL_CACHE_ENABLED', '1') == '1'
PERFORMANCE_MODE = os.environ.get('ITERMINAL_PERFORMANCE_MODE', '1') == '1'
REDUCED_CONTEXT = os.environ.get('ITERMINAL_REDUCED_CONTEXT', '1') == '1'
HYPERTHREAD_ENABLED = os.environ.get('ITERMINAL_HYPERTHREAD_ENABLED', 'true').lower() == 'true'

def refresh_env():
    """Refresh environment variables from .env file"""
    load_dotenv(override=True)

def get_ai_provider():
    """Get the current AI provider from environment variable or default"""
    return os.environ.get('ITERMINAL_AI_PROVIDER', 'openrouter').lower()

AI_PROVIDER = get_ai_provider()
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3')

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
            
            model_found = False
            base_model = OLLAMA_MODEL.split(':')[0] if ':' in OLLAMA_MODEL else OLLAMA_MODEL
            
            if OLLAMA_MODEL in available_models:
                model_found = True
                return True, f"Ollama running with {OLLAMA_MODEL} model available"
            
            matching_models = [m for m in available_models if m.startswith(f"{base_model}:") or m == base_model]
            if matching_models:
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
        
    os.environ['ITERMINAL_AI_PROVIDER'] = provider.lower()
    
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, 'r') as f:
            lines = f.readlines()
        
        found = False
        for i, line in enumerate(lines):
            if line.strip().startswith('ITERMINAL_AI_PROVIDER='):
                lines[i] = f"ITERMINAL_AI_PROVIDER={provider.lower()}\n"
                found = True
                break
        
        if not found:
            lines.append(f"ITERMINAL_AI_PROVIDER={provider.lower()}\n")
            
        with open(ENV_PATH, 'w') as f:
            f.writelines(lines)
    else:
        with open(ENV_PATH, 'w') as f:
            f.write(f"ITERMINAL_AI_PROVIDER={provider.lower()}\n")
    
    return True

def get_api_key():
    """Get the API key for the configured AI provider"""
    if AI_PROVIDER == 'ollama':
        return "ollama"
        
    api_key = os.environ.get('OPENROUTER_API_KEY', None)
    if not api_key:
        from rich.console import Console
        from rich.prompt import Prompt
        console = Console()
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

__all__ = [
    "Settings",
    "PerformanceConfig",
    "AIConfig",
    "LoggingConfig",
    "CompletionConfig",
    "UIConfig",
    "SecurityConfig",
    "AIProviderType",
    "LogLevel",
    "get_settings",
    "reload_settings",
    "FILTER_APT_WARNINGS",
    "PLUGIN_MODE",
    "CACHE_ENABLED",
    "PERFORMANCE_MODE",
    "REDUCED_CONTEXT",
    "HYPERTHREAD_ENABLED",
    "ENV_PATH",
    "AI_PROVIDER",
    "OLLAMA_BASE_URL",
    "OLLAMA_MODEL",
    "refresh_env",
    "get_ai_provider",
    "update_ollama_model",
    "get_ollama_status",
    "set_ai_provider",
    "get_api_key",
]
