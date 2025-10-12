#!/usr/bin/env python3
"""
Comprehensive iTerminal Fix Tool
This script automatically diagnoses and fixes issues with both Ollama and OpenRouter
"""

import os
import sys
import json
import subprocess
import time

try:
    import requests
    REQUESTS_INSTALLED = True
except ImportError:
    REQUESTS_INSTALLED = False

# Terminal colors
class Colors:
    HEADER = '\033[95m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD} {text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")

def success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def warning(text):
    print(f"{Colors.YELLOW}! {text}{Colors.ENDC}")

def error(text):
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")

def install_requests():
    """Install the requests package if needed"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        success("Installed requests package")
        global REQUESTS_INSTALLED
        REQUESTS_INSTALLED = True
        
        # Re-import requests now that it's installed
        global requests
        import requests
    except Exception as e:
        error(f"Failed to install requests: {e}")
        print("Please install it manually: pip install requests")
        sys.exit(1)

def get_env_file_path():
    """Find the .env file path"""
    # First look in the same directory as the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, '.env')
    
    if os.path.exists(env_path):
        return env_path
    
    # Try project root as fallback
    return env_path  # Default to script directory anyway

def backup_env_file():
    """Create a backup of the current .env file"""
    env_path = get_env_file_path()
    if os.path.exists(env_path):
        backup_path = f"{env_path}.{int(time.time())}.backup"
        with open(env_path, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
        success(f"Created backup at {backup_path}")
        return backup_path
    return None

def load_env_file():
    """Load the current .env file into a dictionary"""
    env_path = get_env_file_path()
    env_vars = {}
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    return env_vars

def save_env_file(env_vars):
    """Save the environment variables to the .env file"""
    env_path = get_env_file_path()
    
    # Keep comments and empty lines
    comments = []
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip().startswith('#') or not line.strip():
                    comments.append(line)
    
    # Write updated file
    with open(env_path, 'w') as f:
        # Write comments first
        for comment in comments:
            f.write(comment)
        
        # Write variables
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    success(f"Updated .env file at {env_path}")

def check_ollama():
    """Check if Ollama is installed and running"""
    print_header("Checking Ollama")
    
    if not REQUESTS_INSTALLED:
        warning("Requests package not installed, can't check Ollama")
        return None
    
    # Check if Ollama server is running
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            if models:
                success(f"Ollama is running with {len(models)} models")
                for i, model in enumerate(models[:3]):
                    print(f"  {i+1}. {model['name']}")
                return models
            else:
                warning("Ollama is running but no models available")
                return []
        else:
            warning(f"Ollama returned status code {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        warning("Ollama is not running or not accessible")
        return None
    except Exception as e:
        error(f"Error checking Ollama: {e}")
        return None

def check_openrouter():
    """Check if OpenRouter API key is valid"""
    print_header("Checking OpenRouter")
    
    if not REQUESTS_INSTALLED:
        warning("Requests package not installed, can't check OpenRouter")
        return False
    
    # Get API key from .env file
    env_vars = load_env_file()
    api_key = env_vars.get('OPENROUTER_API_KEY')
    
    if not api_key:
        warning("No OpenRouter API key found in .env file")
        return False
    
    # Check if API key is valid
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get("https://openrouter.ai/api/v1/auth/key", headers=headers, timeout=10)
        if response.status_code == 200:
            success("OpenRouter API key is valid")
            
            # Test a small request
            test_url = "https://openrouter.ai/api/v1/chat/completions"
            test_headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/Rsaimukesh/iTerminal",
                "X-Title": "iTerminal"
            }
            test_payload = {
                "model": "openai/gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Say only OK"}],
                "max_tokens": 5
            }
            
            print("Testing API with a small request...")
            try:
                test_response = requests.post(test_url, headers=test_headers, json=test_payload, timeout=15)
                if test_response.status_code == 200:
                    content = test_response.json()['choices'][0]['message']['content'].strip()
                    success(f"API test successful: {content}")
                    return True
                elif test_response.status_code == 402:
                    error("Insufficient credits. You need to purchase credits.")
                    return False
                else:
                    error(f"API test failed with status {test_response.status_code}")
                    print(f"Response: {test_response.text}")
                    return False
            except Exception as e:
                error(f"Error testing API: {e}")
                return False
        else:
            error(f"API key validation failed: {response.status_code}")
            return False
    except Exception as e:
        error(f"Error connecting to OpenRouter: {e}")
        return False

def fix_ollama_config():
    """Fix Ollama configuration in .env file"""
    print_header("Fixing Ollama Configuration")
    
    env_vars = load_env_file()
    models = check_ollama()
    
    if not models:
        warning("Cannot find Ollama models. Using default configuration.")
        env_vars['OLLAMA_BASE_URL'] = 'http://localhost:11434'
        env_vars['OLLAMA_MODEL'] = 'llama3:latest'
    else:
        # Find the best model to use
        preferred_models = ['llama3:latest', 'llama3', 'llama2:latest', 'llama2', 'mistral:latest', 'mistral']
        model_names = [model['name'] for model in models]
        
        selected_model = None
        for model in preferred_models:
            if model in model_names:
                selected_model = model
                break
        
        # If no preferred model, use the first available
        if not selected_model and model_names:
            selected_model = model_names[0]
        
        if selected_model:
            success(f"Selected Ollama model: {selected_model}")
            env_vars['OLLAMA_MODEL'] = selected_model
        else:
            warning("No models available. Using default model name.")
            env_vars['OLLAMA_MODEL'] = 'llama3:latest'
    
    # Update the environment file
    save_env_file(env_vars)

def fix_openrouter_config():
    """Fix OpenRouter configuration in .env file"""
    print_header("Fixing OpenRouter Configuration")
    
    env_vars = load_env_file()
    api_key = env_vars.get('OPENROUTER_API_KEY')
    
    if not api_key:
        warning("No OpenRouter API key found. You may need to get one from openrouter.ai.")
        api_key = input("Enter your OpenRouter API key (or press Enter to skip): ")
        if api_key:
            env_vars['OPENROUTER_API_KEY'] = api_key
    
    # Add required OpenRouter configuration
    env_vars['OPENROUTER_TIMEOUT'] = env_vars.get('OPENROUTER_TIMEOUT', '60')
    env_vars['OPENROUTER_REQUEST_RETRIES'] = env_vars.get('OPENROUTER_REQUEST_RETRIES', '3')
    
    # Update the environment file
    save_env_file(env_vars)

def select_provider():
    """Select the AI provider to use"""
    print_header("Selecting AI Provider")
    
    ollama_working = check_ollama() is not None
    openrouter_working = check_openrouter()
    
    env_vars = load_env_file()
    
    if ollama_working and openrouter_working:
        print("Both Ollama and OpenRouter are working!")
        provider = input("Which provider do you want to use? [ollama/openrouter] (default: ollama): ").lower()
        if provider == "openrouter":
            env_vars['ITERMINAL_AI_PROVIDER'] = 'openrouter'
        else:
            env_vars['ITERMINAL_AI_PROVIDER'] = 'ollama'
    elif ollama_working:
        success("Ollama is working. Setting as the default provider.")
        env_vars['ITERMINAL_AI_PROVIDER'] = 'ollama'
    elif openrouter_working:
        success("OpenRouter is working. Setting as the default provider.")
        env_vars['ITERMINAL_AI_PROVIDER'] = 'openrouter'
    else:
        warning("Neither provider is fully working. Setting Ollama as default.")
        warning("You may need to install Ollama or configure OpenRouter correctly.")
        env_vars['ITERMINAL_AI_PROVIDER'] = 'ollama'
    
    save_env_file(env_vars)
    success(f"Selected provider: {env_vars['ITERMINAL_AI_PROVIDER']}")

def main():
    print_header("iTerminal Comprehensive Fix Tool")
    
    # Make sure requests is installed
    if not REQUESTS_INSTALLED:
        warning("Requests package not installed. Installing...")
        install_requests()
    
    # Backup the current .env file
    backup_env_file()
    
    # Fix Ollama configuration
    fix_ollama_config()
    
    # Fix OpenRouter configuration
    fix_openrouter_config()
    
    # Select the best provider
    select_provider()
    
    print_header("Fix Complete!")
    print("iTerminal should now work correctly with your selected AI provider.")
    print("To use iTerminal, run: python3 iterminal.py")

if __name__ == "__main__":
    main()