#!/bin/bash
# setup_ollama.sh - Comprehensive Ollama setup script for iTerminal
# Created by GitHub Copilot

set -e # Exit on error
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$ROOT_DIR/.env"

echo "🚀 Ollama Setup for iTerminal 🚀"
echo "=================================="

# Check if running with sudo (needed for system-wide installation)
if [ "$EUID" -ne 0 ]; then
  echo "⚠️  This script requires sudo privileges for a complete installation."
  echo "Running without sudo will limit some functionality."
  SUDO_AVAILABLE=false
else
  SUDO_AVAILABLE=true
fi

# Functions
check_command() {
  command -v "$1" &> /dev/null
}

# Check if Ollama is already installed
if check_command ollama; then
  echo "✅ Ollama is already installed!"
  OLLAMA_VERSION=$(ollama --version 2>/dev/null || echo "Unknown")
  echo "   Current version: $OLLAMA_VERSION"
  INSTALL_NEEDED=false
else
  echo "❓ Ollama is not installed."
  INSTALL_NEEDED=true
fi

# Installation options
if [ "$INSTALL_NEEDED" = true ]; then
  echo ""
  echo "Installation options:"
  echo "1) Install Ollama system-wide (recommended, requires sudo)"
  echo "2) Download portable Ollama (no sudo required)"
  echo "3) Skip installation (if you plan to install manually or use another provider)"
  
  read -p "Select an option (1-3): " INSTALL_OPTION
  
  case $INSTALL_OPTION in
    1)
      if [ "$SUDO_AVAILABLE" = false ]; then
        echo "❌ System-wide installation requires sudo privileges."
        echo "   Please run this script with sudo or select another option."
        exit 1
      fi
      
      echo "📦 Installing Ollama system-wide..."
      curl -fsSL https://ollama.com/install.sh | sh
      
      if [ $? -ne 0 ]; then
        echo "❌ Failed to install Ollama. Please check error messages above."
        exit 1
      else
        echo "✅ Ollama installed successfully!"
      fi
      ;;
      
    2)
      echo "📦 Downloading portable Ollama..."
      TEMP_DIR=$(mktemp -d)
      if [[ "$(uname -m)" == "x86_64" ]]; then
        ARCH="amd64"
      elif [[ "$(uname -m)" == "aarch64" || "$(uname -m)" == "arm64" ]]; then
        ARCH="arm64"
      else
        echo "❌ Unsupported architecture: $(uname -m)"
        exit 1
      fi
      
      DOWNLOAD_URL="https://ollama.com/download/ollama-linux-$ARCH"
      echo "   Downloading from: $DOWNLOAD_URL"
      curl -L "$DOWNLOAD_URL" -o "$TEMP_DIR/ollama"
      chmod +x "$TEMP_DIR/ollama"
      
      # Create a local bin directory if it doesn't exist
      mkdir -p "$ROOT_DIR/bin"
      mv "$TEMP_DIR/ollama" "$ROOT_DIR/bin/ollama"
      rm -rf "$TEMP_DIR"
      
      echo "✅ Portable Ollama downloaded to $ROOT_DIR/bin/ollama"
      echo "   Adding to PATH for this session..."
      export PATH="$ROOT_DIR/bin:$PATH"
      ;;
      
    3)
      echo "⏭️  Skipping Ollama installation."
      ;;
      
    *)
      echo "❌ Invalid option selected."
      exit 1
      ;;
  esac
fi

# Start Ollama service
echo ""
echo "Starting Ollama service..."

if [ "$INSTALL_OPTION" = "2" ]; then
  # For portable installation, we need to start it directly
  echo "Starting portable Ollama in the background..."
  nohup "$ROOT_DIR/bin/ollama" serve > "$ROOT_DIR/ollama.log" 2>&1 &
  OLLAMA_PID=$!
  echo "   Ollama started with PID: $OLLAMA_PID"
  echo "   Log file: $ROOT_DIR/ollama.log"
  
  # Wait for Ollama to start
  echo "   Waiting for Ollama to start..."
  sleep 3
  
  # Check if still running
  if ps -p $OLLAMA_PID > /dev/null; then
    echo "✅ Portable Ollama started successfully!"
    
    # Save the PID for later
    echo $OLLAMA_PID > "$ROOT_DIR/.ollama.pid"
    echo "   The PID is saved to $ROOT_DIR/.ollama.pid"
    echo "   You can stop Ollama later with: kill \$(cat $ROOT_DIR/.ollama.pid)"
  else
    echo "❌ Failed to start portable Ollama. Check $ROOT_DIR/ollama.log for details."
    exit 1
  fi
  
  # Use the portable Ollama for the rest of the script
  OLLAMA_CMD="$ROOT_DIR/bin/ollama"
else
  # For system-wide installation, try to start the service
  if [ "$SUDO_AVAILABLE" = true ] && systemctl is-active --quiet ollama 2>/dev/null; then
    echo "   Ollama service is already running."
  elif [ "$SUDO_AVAILABLE" = true ]; then
    echo "   Starting Ollama systemd service..."
    systemctl enable --now ollama.service
    
    if systemctl is-active --quiet ollama; then
      echo "✅ Ollama service started successfully!"
    else
      echo "❌ Failed to start Ollama service."
      echo "   Trying to start Ollama manually..."
      nohup ollama serve > "$ROOT_DIR/ollama.log" 2>&1 &
      sleep 3
      echo "   Check $ROOT_DIR/ollama.log for details."
    fi
  else
    echo "   Starting Ollama manually (no systemd control available)..."
    nohup ollama serve > "$ROOT_DIR/ollama.log" 2>&1 &
    OLLAMA_PID=$!
    echo "   Ollama started with PID: $OLLAMA_PID"
    echo "   Log file: $ROOT_DIR/ollama.log"
    sleep 3
    
    # Check if still running
    if ps -p $OLLAMA_PID > /dev/null; then
      echo "✅ Ollama started successfully!"
      echo $OLLAMA_PID > "$ROOT_DIR/.ollama.pid"
    else
      echo "❌ Failed to start Ollama. Check $ROOT_DIR/ollama.log for details."
      exit 1
    fi
  fi
  
  OLLAMA_CMD="ollama"
fi

# Verify Ollama is responding
echo ""
echo "Verifying Ollama connection..."
if curl -s http://localhost:11434/api/tags > /dev/null; then
  echo "✅ Successfully connected to Ollama API!"
else
  echo "❌ Could not connect to Ollama API."
  echo "   This could be a temporary issue. Continuing anyway..."
fi

# Pull a model
echo ""
echo "📥 Would you like to download an LLM model for Ollama? (y/n)"
read -r DOWNLOAD_MODEL

if [[ "$DOWNLOAD_MODEL" =~ ^[Yy]$ ]]; then
  echo ""
  echo "Available models:"
  echo "1) llama3 (recommended, ~4GB)"
  echo "2) deepseek-r1:1.5b (smaller, ~1.5GB)"
  echo "3) gemma:2b (even smaller, ~1.2GB)"
  echo "4) phi3:mini (very small, ~500MB)"
  echo "5) Enter a custom model name"
  echo ""
  echo "Enter model number (1-5):"
  read -r MODEL_CHOICE
  
  case $MODEL_CHOICE in
    1) MODEL="llama3" ;;
    2) MODEL="deepseek-r1:1.5b" ;;
    3) MODEL="gemma:2b" ;;
    4) MODEL="phi3:mini" ;;
    5)
      echo "Enter custom model name (example: mistral:7b):"
      read -r MODEL
      ;;
    *) MODEL="llama3" ;;
  esac
  
  echo "📥 Downloading $MODEL model... This might take a while depending on your internet speed."
  $OLLAMA_CMD pull "$MODEL"
  
  if [ $? -eq 0 ]; then
    echo "✅ $MODEL model downloaded successfully!"
    # Update .env file with this model
    if [ -f "$ENV_FILE" ]; then
      # Check if OLLAMA_MODEL already exists in file
      if grep -q "OLLAMA_MODEL=" "$ENV_FILE"; then
        # Replace existing OLLAMA_MODEL
        sed -i "s/OLLAMA_MODEL=.*/OLLAMA_MODEL=$MODEL/" "$ENV_FILE"
      else
        # Add new OLLAMA_MODEL
        echo "OLLAMA_MODEL=$MODEL" >> "$ENV_FILE"
      fi
      echo "✅ Updated .env file with selected model"
    else
      # Create new .env file
      echo "OLLAMA_MODEL=$MODEL" > "$ENV_FILE"
      echo "✅ Created .env file with selected model"
    fi
  else
    echo "❌ Failed to download the model. You can try again later with: ollama pull $MODEL"
  fi
else
  echo "Skipping model download."
fi

# Configure iTerminal to use Ollama
if [ -f "$ENV_FILE" ]; then
  # Check if ITERMINAL_AI_PROVIDER already exists in file
  if grep -q "ITERMINAL_AI_PROVIDER=" "$ENV_FILE"; then
    # Replace existing ITERMINAL_AI_PROVIDER
    sed -i "s/ITERMINAL_AI_PROVIDER=.*/ITERMINAL_AI_PROVIDER=ollama/" "$ENV_FILE"
  else
    # Add new ITERMINAL_AI_PROVIDER
    echo "ITERMINAL_AI_PROVIDER=ollama" >> "$ENV_FILE"
  fi
  echo "✅ Updated iTerminal to use Ollama as the AI provider"
else
  # Create new .env file
  echo "ITERMINAL_AI_PROVIDER=ollama" > "$ENV_FILE"
  echo "✅ Created .env file with Ollama as the AI provider"
fi

echo ""
echo "🎉 Ollama setup complete!"
echo "You can now run iTerminal with the Ollama provider:"
echo "   cd $ROOT_DIR && python iterminal.py"
echo ""
echo "🔧 If you encounter any issues, please check:"
echo "  1. Is Ollama running? (systemctl status ollama.service or ps aux | grep ollama)"
echo "  2. Is the model downloaded? ($OLLAMA_CMD list)"
echo "  3. Can you access the API? (curl http://localhost:11434/api/tags)"
echo ""
echo "📝 To use a different model later, type 'ollama' in iTerminal."
echo ""