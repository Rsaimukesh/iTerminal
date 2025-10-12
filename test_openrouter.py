#!/usr/bin/env python3
"""
Direct Test Script for OpenRouter API
This script tests the OpenRouter API directly, bypassing iTerminal
"""

import os
import requests
import json
import sys

# Get the API key from environment or .env file
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
                        break
    
    return api_key

def test_api():
    print("Testing OpenRouter API directly...")
    api_key = get_api_key()
    
    if not api_key:
        print("ERROR: No OpenRouter API key found!")
        return False
    
    print(f"Found API key: {api_key[:8]}...{api_key[-4:]}")
    
    # Test endpoint and headers
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/rsaimukesh/iterminal",  
        "X-Title": "iTerminal Direct Test"
    }
    
    # Use a very minimal payload to minimize token usage
    payload = {
        "model": "anthropic/claude-instant-v1",  # One of the cheapest models
        "messages": [{"role": "user", "content": "Say OK only"}],
        "max_tokens": 5,
        "temperature": 0
    }
    
    try:
        print("Sending test request...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text[:200]}")  # Print first 200 chars of response
        
        if response.status_code == 200:
            result = response.json()
            response_text = result['choices'][0]['message']['content'].strip()
            print(f"SUCCESS! Response text: '{response_text}'")
            print("Your OpenRouter API key is working correctly!")
            return True
        elif response.status_code == 402:
            print("FAILED: Insufficient credits.")
            print("You need to purchase credits at: https://openrouter.ai/settings/credits")
            return False
        else:
            print(f"FAILED: Unexpected status code {response.status_code}")
            print(f"Error message: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: Exception occurred: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("OpenRouter Direct Test")
    print("=" * 60)
    
    success = test_api()
    
    if success:
        print("\nTest PASSED. Your OpenRouter API key is working correctly.")
        print("You can now use iTerminal with OpenRouter.")
    else:
        print("\nTest FAILED. Please check the error messages above.")
        print("You may need to:")
        print("1. Purchase credits at: https://openrouter.ai/settings/credits")
        print("2. Get a new API key from: https://openrouter.ai/keys")
        print("3. Try switching to Ollama with: python3 setup_ollama.py")