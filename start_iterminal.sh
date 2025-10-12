#!/bin/bash

# Script to fix and start iTerminal

echo "=================================================="
echo " iTerminal Quick Fix and Start"
echo "=================================================="

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Step 1: Install requirements
echo "Installing required packages..."
pip install -r requirements.txt

# Step 2: Run the fix script
echo -e "\nRunning the fix script..."
python3 fix_iterminal.py

# Step 3: Start iTerminal
echo -e "\nStarting iTerminal..."
python3 iterminal.py