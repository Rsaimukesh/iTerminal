#!/usr/bin/env python3
"""
Utility script to diagnose Git command issues in iTerminal
"""
import os
import sys
import time
import subprocess
from typing import Dict, Any, Tuple

def test_git_command(cmd: str, timeout: int = 10) -> Tuple[int, str, str, float]:
    """Test a Git command and measure its execution time"""
    print(f"Testing command: {cmd}")
    start_time = time.time()
    
    try:
        # Set Git environment variables to speed things up
        env = os.environ.copy()
        env['GIT_TRACE'] = '0'
        env['GIT_PAGER'] = ''
        env['GIT_OPTIONAL_LOCKS'] = '0'
        
        # Run the command with a timeout
        process = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            timeout=timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        return process.returncode, process.stdout, process.stderr, duration
    
    except subprocess.TimeoutExpired:
        end_time = time.time()
        duration = end_time - start_time
        return -1, "", f"Command timed out after {timeout} seconds", duration
    
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        return -1, "", str(e), duration

def main():
    """Main function for Git command diagnostics"""
    # Default commands to test
    test_commands = [
        "git --version",
        "git status",
        "git log -5",
        "git add --dry-run .",
        "git add --help"
    ]
    
    # If command-line arguments are provided, use them instead
    if len(sys.argv) > 1:
        test_commands = [" ".join(sys.argv[1:])]
    
    print("Git Command Performance Test")
    print("-" * 50)
    
    results = []
    for cmd in test_commands:
        returncode, stdout, stderr, duration = test_git_command(cmd)
        
        status = "✅ Success" if returncode == 0 else f"❌ Failed (code {returncode})"
        
        # Truncate output for display
        if len(stdout) > 500:
            stdout = stdout[:500] + "... [truncated]"
        
        results.append({
            "command": cmd,
            "status": status,
            "duration": duration,
            "stdout": stdout,
            "stderr": stderr
        })
    
    # Display results in a table format
    print("\nResults:")
    print("-" * 80)
    print(f"{'Command':<30} {'Status':<15} {'Duration':<10} {'Output'}")
    print("-" * 80)
    
    for result in results:
        output = result["stderr"] if result["stderr"] else result["stdout"]
        output = output.replace("\n", " ")[:30]
        print(f"{result['command']:<30} {result['status']:<15} {result['duration']:.2f}s      {output}")
    
    print("-" * 80)
    
    # Offer recommendations
    print("\nRecommendations:")
    for result in results:
        if result["duration"] > 5:
            print(f"- '{result['command']}' is slow ({result['duration']:.2f}s). Consider using a direct terminal.")
        if "Permission denied" in result.get("stderr", ""):
            print(f"- '{result['command']}' has permission issues. Check your repository access.")
    
    print("\nFor detailed Git diagnostics, run: git fsck --full")

if __name__ == "__main__":
    main()