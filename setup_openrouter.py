#!/usr/bin/env python3
"""
Switches iTerminal to use OpenRouter with proper API configuration
"""

import os
import sys
import requests
from pathlib import Path

def print_header(text):
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)

def get_api_key():
    # First check environment
    api_key = os.environ.get('OPENROUTER_API_KEY')
    
    # If not in environment, check .env file
    if not api_key:
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    if line.strip().startswith('OPENROUTER_API_KEY='):
                        api_key = line.strip().split('=', 1)[1].strip()
                        if api_key.startswith('"') and api_key.endswith('"'):
                            api_key = api_key[1:-1]
                        break
    
    # If still not found, prompt user
    if not api_key:
        print("OpenRouter API key not found.")
        api_key = input("Please enter your OpenRouter API key: ").strip()
        
    return api_key

def check_api_key(api_key):
    print("Checking OpenRouter API key...")
    
    url = "https://openrouter.ai/api/v1/auth/key"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ OpenRouter API key is valid!")
            return True
        else:
            print(f"❌ API key validation failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error connecting to OpenRouter: {str(e)}")
        return False

def check_credits(api_key):
    print("Checking available credits...")
    
    # First check credits with the key endpoint
    url = "https://openrouter.ai/api/v1/auth/key"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            rate_limit = data.get('rate_limit_requests')
            if rate_limit:
                print(f"✅ You have {rate_limit} requests available per month")
                return True
            else:
                # If credits couldn't be determined, make a test request
                print("Testing API with a small request...")
                test_url = "https://openrouter.ai/api/v1/chat/completions"
                test_headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/Rsaimukesh/iTerminal",
                    "X-Title": "iTerminal"
                }
                test_payload = {
                    "model": "openai/gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "Say only the word 'working'"}],
                    "max_tokens": 5
                }
                
                test_response = requests.post(test_url, headers=test_headers, json=test_payload, timeout=15)
                if test_response.status_code == 200:
                    print("✅ API is working! You have sufficient credits.")
                    return True
                elif test_response.status_code == 402:
                    print("❌ Insufficient credits. You need to purchase credits.")
                    return False
                else:
                    print("⚠️ Could not determine available credits, but proceeding anyway")
                    return True
        else:
            print(f"❌ Failed to check credits: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking credits: {str(e)}")
        # Still return true to let the user try
        print("⚠️ Could not check credits, but proceeding anyway")
        return True

def update_env_file(api_key):
    print("Updating .env configuration...")
    
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    
    if not os.path.exists(env_path):
        # Try current directory
        env_path = os.path.abspath('.env')
        
    if not os.path.exists(env_path):
        print(f"Creating new .env file at {env_path}")
        Path(env_path).touch()
    
    try:
        # Read existing content
        lines = []
        if os.path.exists(env_path) and os.path.getsize(env_path) > 0:
            with open(env_path, 'r') as f:
                lines = f.readlines()
        
        # Prepare OpenRouter settings
        settings = {
            "ITERMINAL_AI_PROVIDER": "openrouter",
            "OPENROUTER_API_KEY": api_key,
            "OPENROUTER_TIMEOUT": "60",
            "OPENROUTER_REQUEST_RETRIES": "3"
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
        
        # Add remaining settings
        for key, value in settings.items():
            updated_lines.append(f"{key}={value}\n")
        
        # Write back
        with open(env_path, 'w') as f:
            f.writelines(updated_lines)
        
        print(f"✅ Updated .env file to use OpenRouter")
        return True
    except Exception as e:
        print(f"❌ Error updating .env file: {str(e)}")
        return False

def main():
    print_header("OpenRouter Setup for iTerminal")
    
    # Get and validate API key
    api_key = get_api_key()
    if not check_api_key(api_key):
        print("\nYour OpenRouter API key appears to be invalid.")
        print("Please get a valid key from: https://openrouter.ai/keys")
        return
    
    # Check credits
    if not check_credits(api_key):
        print("\nYour OpenRouter account may not have sufficient credits.")
        print("You can purchase credits at: https://openrouter.ai/settings/credits")
        proceed = input("Do you want to continue anyway? (y/n): ").lower()
        if proceed != 'y':
            return
    
    # Update .env file
    update_env_file(api_key)
    
    print_header("Setup Complete!")
    print("iTerminal is now configured to use OpenRouter as its AI provider.")
    print("To start using it, run: python3 /home/sai/Desktop/iTerminal/iterminal.py")

if __name__ == "__main__":
    main()