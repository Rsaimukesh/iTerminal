#!/usr/bin/env python3
"""
Test and fix OpenRouter API connection for iTerminal
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

def test_openrouter_connection():
    print("Testing OpenRouter API connection...")
    load_dotenv()
    
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY not found in environment variables")
        print("Please check your .env file and make sure OPENROUTER_API_KEY is set correctly")
        return False
    
    print(f"API Key found: {api_key[:8]}...{api_key[-4:]}")
    
    url = "https://openrouter.ai/api/v1/auth/key"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            print("✅ OpenRouter API key is valid!")
            data = response.json()
            print(f"Key name: {data.get('name', 'Unknown')}")
            print(f"Rate limit: {data.get('rate_limit_requests', 'Unknown')} requests per month")
            return True
        else:
            print(f"❌ Error: API key validation failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error connecting to OpenRouter: {str(e)}")
        return False

def test_completion():
    print("\nTesting completion API...")
    load_dotenv()
    
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY not found")
        return False
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Rsaimukesh/iTerminal",
        "X-Title": "iTerminal"
    }
    
    payload = {
        "model": "anthropic/claude-3.5-sonnet",
        "messages": [
            {"role": "user", "content": "Return only the word 'success' if you can read this message."}
        ],
        "max_tokens": 10
    }
    
    try:
        print("Sending test request to OpenRouter...")
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            print(f"✅ Completion API working! Response: {content}")
            return True
        else:
            print(f"❌ Error: Completion API failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing completion: {str(e)}")
        return False

def update_env_file():
    print("\nUpdating .env file with correct settings...")
    
    # Look for .env in the current directory first
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    
    if not os.path.exists(env_path):
        # Try the directory where script is located
        env_path = os.path.abspath('.env')
        if not os.path.exists(env_path):
            print(f"❌ Error: .env file not found at {env_path}")
            print(f"Creating new .env file at {env_path}")
            open(env_path, 'a').close()  # Create empty file
    
    print(f"Using .env file at: {env_path}")
    
    try:
        # Read existing content if file exists and is not empty
        lines = []
        if os.path.exists(env_path) and os.path.getsize(env_path) > 0:
            with open(env_path, 'r') as f:
                lines = f.readlines()
        
        # Switch to Ollama since OpenRouter requires credits
        print("Switching AI provider to Ollama due to OpenRouter credit limitations...")
        settings = {
            "ITERMINAL_AI_PROVIDER": "ollama",
            "OLLAMA_BASE_URL": "http://localhost:11434",
            "OLLAMA_MODEL": "llama3",
            "ITERMINAL_DEBUG": "1",
            "ITERMINAL_CACHE_ENABLED": "1",
            "ITERMINAL_CACHE_DURATION": "7200"
        }
        
        # Process existing lines
        updated_lines = []
        for line in lines:
            key = line.split('=')[0].strip() if '=' in line else None
            if key in settings:
                updated_lines.append(f"{key}={settings[key]}\n")
                del settings[key]
            else:
                updated_lines.append(line)
        
        # Add any remaining settings
        for key, value in settings.items():
            updated_lines.append(f"{key}={value}\n")
        
        # Write back to file
        with open(env_path, 'w') as f:
            f.writelines(updated_lines)
        
        print("✅ .env file updated successfully!")
        return True
    except Exception as e:
        print(f"❌ Error updating .env file: {str(e)}")
        return False

def check_ollama_availability():
    print("\nChecking Ollama availability...")
    
    try:
        url = "http://localhost:11434/api/tags"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            models = response.json().get('models', [])
            if models:
                print("✅ Ollama is running and has the following models:")
                for model in models[:5]:  # Show up to 5 models
                    print(f"   - {model['name']}")
                return True
            else:
                print("✅ Ollama is running but no models are available.")
                print("   Run 'ollama pull llama3' to download a model.")
                return False
        else:
            print(f"❌ Ollama returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Ollama is not running. Please start the Ollama server.")
        print("   Install Ollama from https://ollama.com if not installed.")
        return False
    except Exception as e:
        print(f"❌ Error checking Ollama: {str(e)}")
        return False

if __name__ == "__main__":
    print("iTerminal Connection Fix Tool")
    print("============================")
    
    # Test OpenRouter first
    key_valid = test_openrouter_connection()
    if key_valid:
        result = test_completion()
        if not result:
            print("\n⚠️  OpenRouter key is valid but has insufficient credits.")
            print("Switching to Ollama as fallback AI provider...")
            check_ollama_availability()
    else:
        print("\n⚠️  OpenRouter key validation failed.")
        print("Switching to Ollama as fallback AI provider...")
        check_ollama_availability()
    
    # Update .env file to use Ollama
    update_env_file()
    
    print("\n🔧 Configuration has been updated to use Ollama as the AI provider.")
    print("   If Ollama is not installed, get it from https://ollama.com")
    print("   After installation, run: ollama pull llama3")
    print("\n🚀 Restart iTerminal to apply these changes.")