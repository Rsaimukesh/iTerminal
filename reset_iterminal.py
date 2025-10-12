#!/usr/bin/env python3
"""
Reset iTerminal Configuration
This script will reset iTerminal's AI configuration and test different providers.
"""

import os
import sys
import subprocess
import requests
import json
import time
from pathlib import Path

# Terminal colors for better readability
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD} {text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")
    
def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")
    
def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.CYAN}ℹ {text}{Colors.ENDC}")

def get_env_file_path():
    """Find the .env file path"""
    # First look in the same directory as the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, '.env')
    
    if os.path.exists(env_path):
        return env_path
    
    # Then try the current directory
    env_path = os.path.abspath('.env')
    if os.path.exists(env_path):
        return env_path
    
    # Create in the script directory if not found
    return os.path.join(script_dir, '.env')

def backup_env_file():
    """Create a backup of the current .env file"""
    env_path = get_env_file_path()
    if os.path.exists(env_path):
        backup_path = f"{env_path}.backup"
        with open(env_path, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
        print_success(f"Created backup of .env file at {backup_path}")
        return backup_path
    return None

def reset_env_file():
    """Reset the .env file to default settings"""
    env_path = get_env_file_path()
    
    # Start with clean defaults
    default_settings = {
        "ITERMINAL_AI_PROVIDER": "openrouter",
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "OLLAMA_MODEL": "llama3",
        "ITERMINAL_CACHE_ENABLED": "1",
        "ITERMINAL_CACHE_DURATION": "7200",
        "ITERMINAL_PERFORMANCE_MODE": "1",
        "ITERMINAL_REDUCED_CONTEXT": "1",
        "ITERMINAL_MINIMAL_OUTPUT": "1",
        "ITERMINAL_FAST_STARTUP": "1",
        "ITERMINAL_HYPERTHREAD_ENABLED": "true",
        "ITERMINAL_MAX_CONCURRENT_TASKS": "16",
        "ITERMINAL_PARALLEL_REQUESTS": "8",
        "ITERMINAL_REQUEST_TIMEOUT": "60"
    }
    
    # Preserve OpenRouter API key if it exists
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip().startswith('OPENROUTER_API_KEY='):
                    key = line.strip().split('=', 1)[1].strip()
                    if key:
                        default_settings['OPENROUTER_API_KEY'] = key
    
    # Write new .env file
    with open(env_path, 'w') as f:
        for key, value in default_settings.items():
            f.write(f"{key}={value}\n")
    
    print_success(f"Reset .env file with default settings at {env_path}")
    return env_path

def test_ollama():
    """Test Ollama availability"""
    print_info("Testing Ollama...")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            if models:
                print_success(f"Ollama is running with {len(models)} models available")
                for model in models[:3]:  # Show first 3 models
                    print_info(f"  - {model['name']}")
                return True
            else:
                print_warning("Ollama is running but no models are available")
                return False
        else:
            print_error(f"Ollama returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Ollama is not running or not installed")
        return False
    except Exception as e:
        print_error(f"Error testing Ollama: {str(e)}")
        return False

def test_openrouter():
    """Test OpenRouter API key"""
    print_info("Testing OpenRouter...")
    
    env_path = get_env_file_path()
    api_key = None
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip().startswith('OPENROUTER_API_KEY='):
                    api_key = line.strip().split('=', 1)[1].strip()
                    if api_key.startswith('"') and api_key.endswith('"'):
                        api_key = api_key[1:-1]
                    break
    
    if not api_key:
        print_error("No OpenRouter API key found in .env file")
        return False
    
    # Test API key
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get("https://openrouter.ai/api/v1/auth/key", headers=headers, timeout=10)
        if response.status_code == 200:
            print_success("OpenRouter API key is valid")
            
            # Test a small completion request
            print_info("Testing with a small completion request...")
            test_url = "https://openrouter.ai/api/v1/chat/completions"
            test_headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/Rsaimukesh/iTerminal",
                "X-Title": "iTerminal"
            }
            test_payload = {
                "model": "openai/gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Reply with just the word 'test'"}],
                "max_tokens": 5
            }
            
            test_response = requests.post(test_url, headers=test_headers, json=test_payload, timeout=15)
            if test_response.status_code == 200:
                content = test_response.json()['choices'][0]['message']['content'].strip()
                print_success(f"API test successful! Response: {content}")
                return True
            elif test_response.status_code == 402:
                print_error("Insufficient credits. You need to purchase credits.")
                return False
            else:
                print_error(f"API test failed with status {test_response.status_code}")
                print_error(f"Response: {test_response.text}")
                return False
        else:
            print_error(f"API key validation failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error testing OpenRouter: {str(e)}")
        return False

def set_ai_provider():
    """Set the AI provider based on available options"""
    print_header("AI Provider Selection")
    
    ollama_available = test_ollama()
    openrouter_available = test_openrouter()
    
    if ollama_available and openrouter_available:
        print_info("\nBoth Ollama and OpenRouter are available.")
        choice = input(f"{Colors.BOLD}Which provider would you like to use? [ollama/openrouter]: {Colors.ENDC}").lower()
        if choice == "ollama":
            update_provider("ollama")
        else:
            update_provider("openrouter")
    elif ollama_available:
        print_info("\nOnly Ollama is available. Setting as default provider.")
        update_provider("ollama")
    elif openrouter_available:
        print_info("\nOnly OpenRouter is available. Setting as default provider.")
        update_provider("openrouter")
    else:
        print_warning("\nNeither Ollama nor OpenRouter is available.")
        print_info("You can:")
        print_info("1. Install Ollama from https://ollama.com")
        print_info("2. Get an OpenRouter API key from https://openrouter.ai/keys")
        
        choice = input(f"{Colors.BOLD}Which provider would you like to configure now? [ollama/openrouter]: {Colors.ENDC}").lower()
        if choice == "ollama":
            print_info("Please run setup_ollama.py after installing Ollama")
            update_provider("ollama")
        else:
            api_key = input(f"{Colors.BOLD}Enter your OpenRouter API key: {Colors.ENDC}")
            update_provider("openrouter", api_key)

def update_provider(provider, api_key=None):
    """Update the .env file with the selected provider"""
    env_path = get_env_file_path()
    
    settings = {
        "ITERMINAL_AI_PROVIDER": provider,
    }
    
    if api_key and provider == "openrouter":
        settings["OPENROUTER_API_KEY"] = api_key
    
    # Read existing content
    lines = []
    if os.path.exists(env_path) and os.path.getsize(env_path) > 0:
        with open(env_path, 'r') as f:
            lines = f.readlines()
    
    # Process existing lines
    updated_lines = []
    for line in lines:
        key = line.split('=')[0].strip() if '=' in line else None
        if key in settings:
            updated_lines.append(f"{key}={settings[key]}\n")
            del settings[key]
        else:
            updated_lines.append(line)
    
    # Add remaining settings
    for key, value in settings.items():
        updated_lines.append(f"{key}={value}\n")
    
    # Write back
    with open(env_path, 'w') as f:
        f.writelines(updated_lines)
    
    print_success(f"Updated AI provider to {provider}")

def main():
    print_header("iTerminal Configuration Reset Tool")
    
    # Create backup
    backup = backup_env_file()
    
    # Reset to defaults
    reset_env_file()
    
    # Test and set provider
    set_ai_provider()
    
    print_header("Configuration Complete")
    print_success("iTerminal has been reconfigured.")
    print_info("Run: python3 /home/sai/Desktop/iTerminal/iterminal.py to start using iTerminal")
    
    if backup:
        print_info(f"If needed, you can restore your backup from: {backup}")

if __name__ == "__main__":
    main()