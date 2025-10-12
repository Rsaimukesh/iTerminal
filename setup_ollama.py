#!/usr/bin/env python3
"""
Install and configure Ollama for iTerminal
This script helps set up Ollama as a local AI provider for iTerminal
"""

import os
import sys
import subprocess
import platform
import requests
import time
from pathlib import Path

def print_header(text):
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)

def check_ollama_installed():
    """Check if Ollama is already installed"""
    try:
        result = subprocess.run(["which", "ollama"], 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE)
        return result.returncode == 0
    except Exception:
        return False

def check_ollama_running():
    """Check if Ollama server is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False

def install_ollama_linux():
    """Install Ollama on Linux"""
    print("Installing Ollama...")
    try:
        # Download the install script first, then execute it
        subprocess.run(
            "curl -fsSL https://ollama.com/install.sh -o /tmp/ollama_install.sh && chmod +x /tmp/ollama_install.sh && sh /tmp/ollama_install.sh", 
            shell=True, 
            check=True
        )
        print("✅ Ollama installation completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing Ollama: {str(e)}")
        print("Please install manually from https://ollama.com")
        return False

def start_ollama():
    """Start the Ollama server"""
    print("Starting Ollama server...")
    try:
        # Start Ollama in the background
        subprocess.Popen(
            ["ollama", "serve"], 
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        # Wait for server to start
        for _ in range(10):  # Try for 10 seconds
            if check_ollama_running():
                print("✅ Ollama server started successfully!")
                return True
            time.sleep(1)
            
        print("❌ Ollama server didn't start in the expected time.")
        return False
    except Exception as e:
        print(f"❌ Error starting Ollama: {str(e)}")
        return False

def download_model(model_name="llama3"):
    """Download a model for Ollama"""
    print(f"Downloading the {model_name} model (this may take a while)...")
    try:
        subprocess.run(["ollama", "pull", model_name], check=True)
        print(f"✅ {model_name} model downloaded successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error downloading model: {str(e)}")
        return False

def update_env_file(model_name="llama3"):
    """Update .env file to use Ollama"""
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
        
        # Prepare Ollama settings
        settings = {
            "ITERMINAL_AI_PROVIDER": "ollama",
            "OLLAMA_BASE_URL": "http://localhost:11434",
            "OLLAMA_MODEL": model_name,
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
        
        # Add remaining settings
        for key, value in settings.items():
            updated_lines.append(f"{key}={value}\n")
        
        # Write back
        with open(env_path, 'w') as f:
            f.writelines(updated_lines)
        
        print(f"✅ Updated .env file to use Ollama with {model_name} model")
        return True
    except Exception as e:
        print(f"❌ Error updating .env file: {str(e)}")
        return False

def list_available_models():
    """List models available in Ollama"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            if models:
                print("\nAvailable models:")
                for i, model in enumerate(models, 1):
                    print(f"  {i}. {model['name']}")
                return models
            else:
                print("\nNo models available. You can download one with 'ollama pull <model_name>'")
                return []
        else:
            print(f"\nFailed to list models: {response.status_code}")
            return []
    except Exception as e:
        print(f"\nError listing models: {str(e)}")
        return []

def main():
    print_header("Ollama Setup for iTerminal")
    
    # Check if Ollama is already installed
    if check_ollama_installed():
        print("✅ Ollama is already installed!")
    else:
        print("❌ Ollama is not installed.")
        if platform.system() == "Linux":
            if install_ollama_linux():
                print("Ollama installation successful!")
            else:
                print("Please install Ollama manually from https://ollama.com")
                return
        else:
            print("This script only supports automatic installation on Linux.")
            print("Please install Ollama manually from https://ollama.com")
            return
    
    # Check if Ollama is running
    if check_ollama_running():
        print("✅ Ollama server is already running!")
    else:
        print("❌ Ollama server is not running.")
        if start_ollama():
            print("Ollama server started successfully!")
        else:
            print("Failed to start Ollama server. Please start it manually with 'ollama serve'")
            return
    
    # List available models
    models = list_available_models()
    model_names = [model['name'] for model in models] if models else []
    
    # Check if llama3 is available
    if "llama3" not in model_names and "llama3:latest" not in model_names:
        print("\nThe recommended 'llama3' model is not available.")
        download = input("Would you like to download it now? (y/n): ").lower()
        if download == 'y':
            download_model("llama3")
    
    # Update .env file
    update_env_file("llama3")
    
    print_header("Setup Complete!")
    print("iTerminal is now configured to use Ollama as its AI provider.")
    print("To start using it, run: python3 /home/sai/Desktop/iTerminal/iterminal.py")

if __name__ == "__main__":
    main()