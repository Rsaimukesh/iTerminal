"""
Patch to remove 'sudo not found' messages from iTerminal.
This patch should be applied at the start of the program.
"""

import builtins
import sys
import io

# Save the original print function
original_print = builtins.print

# Create a wrapper function that filters out sudo messages
def filtered_print(*args, **kwargs):
    # Check if any argument contains the sudo message
    should_print = True
    for arg in args:
        if isinstance(arg, str) and "Note: 'sudo' not found, executing" in arg:
            should_print = False
            break
    
    # Only call the original print if it's not the sudo message
    if should_print:
        original_print(*args, **kwargs)

# Replace the built-in print function with our filtered version
builtins.print = filtered_print

# Also patch stdout write to catch any direct writes
original_stdout_write = sys.stdout.write

def filtered_write(text):
    if isinstance(text, str) and "Note: 'sudo' not found, executing" in text:
        return len(text)  # Pretend we wrote it
    return original_stdout_write(text)

# Apply the stdout patch
if not isinstance(sys.stdout, io.StringIO):  # Don't patch StringIO instances
    sys.stdout.write = filtered_write