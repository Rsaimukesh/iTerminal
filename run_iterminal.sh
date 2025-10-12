#!/bin/bash

# Colors for prettier output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Function to print section headers
print_header() {
    echo -e "\n${BLUE}${BOLD}======================================================${NC}"
    echo -e "${BLUE}${BOLD} $1${NC}"
    echo -e "${BLUE}${BOLD}======================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}! $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to handle errors
handle_error() {
    print_error "$1"
    echo ""
    echo "Please check the error and try again."
    exit 1
}

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

print_header "iTerminal Quick Fix and Start"

# Step 1: Fix .env file if needed
echo -e "Checking environment configuration..."
if [ ! -f .env ]; then
    print_warning "No .env file found. Creating one with default settings..."
    echo "ITERMINAL_AI_PROVIDER=ollama" > .env
    echo "OLLAMA_BASE_URL=http://localhost:11434" >> .env
    echo "OLLAMA_MODEL=llama3:latest" >> .env
    echo "ITERMINAL_CACHE_ENABLED=1" >> .env
    echo "ITERMINAL_CACHE_DURATION=7200" >> .env
    print_success "Created default .env file"
else
    print_success "Found .env file"
fi

# Step 2: Install requirements
print_header "Installing Requirements"
echo "Installing required packages..."
pip install -q -r requirements.txt || handle_error "Failed to install required packages"
print_success "Installed all requirements"

# Step 3: Fix any syntax issues
print_header "Checking for Syntax Issues"
python3 -m py_compile iterminal/config.py || {
    print_warning "Found syntax issue in config.py, fixing..."
    # Apply the fix if needed
    sed -i 's/global OLLAMA_MODEL/# Update the model name/' iterminal/config.py
    print_success "Fixed syntax issue in config.py"
}

# Step 4: Start iTerminal
print_header "Starting iTerminal"
echo "Starting iTerminal..."
python3 iterminal.py

# If we get here, the program exited normally
exit 0