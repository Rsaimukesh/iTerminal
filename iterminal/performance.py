"""
Performance monitoring utilities for iTerminal
"""
import time
from typing import Dict, Any, Optional, Tuple, Callable
import threading

# Track command execution times
command_timings: Dict[str, float] = {}

# Lock for thread-safe access to timing data
_timing_lock = threading.Lock()

def timing_decorator(func: Callable) -> Callable:
    """Decorator to time function execution"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        
        # For shell commands, track the timing by command type
        if args and isinstance(args[0], str):
            cmd = args[0].strip().split()[0] if args[0].strip() else "unknown"
            with _timing_lock:
                if cmd in command_timings:
                    # Moving average to smooth out timing data
                    command_timings[cmd] = (command_timings[cmd] * 0.8) + (duration * 0.2)
                else:
                    command_timings[cmd] = duration
        
        return result
    return wrapper

def get_command_timing(cmd: str) -> Optional[float]:
    """Get the average execution time for a command type"""
    cmd_type = cmd.strip().split()[0] if cmd.strip() else None
    if not cmd_type:
        return None
    
    with _timing_lock:
        return command_timings.get(cmd_type)

def get_all_timings() -> Dict[str, float]:
    """Get all command timings"""
    with _timing_lock:
        return dict(command_timings)