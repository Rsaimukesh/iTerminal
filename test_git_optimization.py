#!/usr/bin/env python3
"""
Test script to verify Git command optimization in iTerminal
"""
import os
import sys
import time

# Add the parent directory to the path so we can import iterminal modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from iterminal.command_utils import is_git_command, extract_git_subcommand
from iterminal.git_cache import GIT_COMMAND_CACHE

def test_git_detection():
    """Test the Git command detection functionality"""
    test_cases = [
        ("git status", True, "git status"),
        ("git", True, "git"),
        ("git commit -m 'test'", True, "git commit"),
        ("ls -la", False, ""),
        ("  git log  ", True, "git log"),
        ("gitignore", False, "")
    ]
    
    for cmd, expected_is_git, expected_subcommand in test_cases:
        is_git = is_git_command(cmd)
        subcommand = extract_git_subcommand(cmd) if is_git else ""
        
        if is_git != expected_is_git:
            print(f"❌ is_git_command failed for '{cmd}': expected {expected_is_git}, got {is_git}")
        else:
            print(f"✅ is_git_command correct for '{cmd}': {is_git}")
            
        if subcommand != expected_subcommand:
            print(f"❌ extract_git_subcommand failed for '{cmd}': expected '{expected_subcommand}', got '{subcommand}'")
        else:
            print(f"✅ extract_git_subcommand correct for '{cmd}': '{subcommand}'")

def test_git_cache():
    """Test the Git command cache functionality"""
    print("\nTesting Git command cache:")
    
    # Check a few key Git commands that should be in the cache
    test_commands = ["git", "git status", "git commit", "git log"]
    
    for cmd in test_commands:
        subcommand = extract_git_subcommand(cmd)
        if subcommand in GIT_COMMAND_CACHE:
            cache_entry = GIT_COMMAND_CACHE[subcommand]
            # Just show first 50 chars of cached explanation
            preview = cache_entry[:50] + "..." if len(cache_entry) > 50 else cache_entry
            print(f"✅ Cache hit for '{subcommand}': {preview}")
        else:
            print(f"❌ No cache entry found for '{subcommand}'")

def main():
    """Main test function"""
    print("Testing Git command optimization in iTerminal")
    print("-" * 50)
    
    test_git_detection()
    test_git_cache()
    
    print("\nAll tests completed")

if __name__ == "__main__":
    main()