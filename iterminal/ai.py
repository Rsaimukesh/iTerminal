import requests
import json
import hashlib
import time
import os
import threading
import multiprocessing
from typing import Optional, Dict, Any, List, Tuple, Callable
from rich.console import Console
from .config import get_api_key, get_ai_provider, OLLAMA_BASE_URL, OLLAMA_MODEL
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

console = Console()

# Determine optimal thread and process counts for AI operations
CPU_COUNT = multiprocessing.cpu_count()
OPTIMAL_THREADS = min(32, CPU_COUNT * 4)  # Hyperthreading: 4 threads per CPU core
OPTIMAL_PROCESSES = max(2, CPU_COUNT - 1)  # Leave one CPU core for the main thread

# Hyperthread settings from environment
HYPERTHREAD_ENABLED = os.environ.get('ITERMINAL_HYPERTHREAD_ENABLED', 'true').lower() == 'true'
PARALLEL_REQUESTS = int(os.environ.get('ITERMINAL_PARALLEL_REQUESTS', min(8, OPTIMAL_THREADS // 2)))
REQUEST_TIMEOUT = int(os.environ.get('ITERMINAL_REQUEST_TIMEOUT', 60))
MAX_CONCURRENT_TASKS = int(os.environ.get('ITERMINAL_MAX_CONCURRENT_TASKS', OPTIMAL_THREADS))
HYPERTHREAD_ENABLED = os.environ.get('ITERMINAL_HYPERTHREAD', '1') == '1'
THREAD_COUNT = int(os.environ.get('ITERMINAL_THREAD_COUNT', str(OPTIMAL_THREADS)))
PARALLEL_REQUESTS = int(os.environ.get('ITERMINAL_PARALLEL_REQUESTS', '4'))

# Performance settings
CACHE_ENABLED = os.environ.get('ITERMINAL_CACHE_ENABLED', '1') == '1'
PERFORMANCE_MODE = os.environ.get('ITERMINAL_PERFORMANCE_MODE', '1') == '1'
REDUCED_CONTEXT = os.environ.get('ITERMINAL_REDUCED_CONTEXT', '1') == '1'
CACHE_DURATION = int(os.environ.get('ITERMINAL_CACHE_DURATION', '7200'))
PERFORMANCE_MODE = os.environ.get('ITERMINAL_PERFORMANCE_MODE', '1') == '1'
REDUCED_CONTEXT = os.environ.get('ITERMINAL_REDUCED_CONTEXT', '1') == '1'

# Enhanced model list with better fallbacks and reliability
AI_MODELS = [
    "openai/gpt-3.5-turbo",         # Most reliable and affordable
    "anthropic/claude-instant-v1",  # Good backup
    "google/palm-2-chat-bison",     # Another good option
    "meta-llama/llama-2-13b-chat",  # Free option
    "openai/gpt-4-turbo",           # Premium option (used only if others fail)
    "anthropic/claude-2.0"          # Another premium backup
]

# Thread synchronization locks
_request_lock = threading.RLock()  # Reentrant lock for API requests
_cache_lock = threading.RLock()    # Reentrant lock for cache access

# Enhanced executors for parallel AI model requests
_thread_executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_TASKS)
_process_executor = ProcessPoolExecutor(max_workers=OPTIMAL_PROCESSES)

# Thread-safe response cache with read-write optimizations
_response_cache: Dict[str, Dict[str, Any]] = {}

# LRU cache implementation for faster access
_lru_list: List[str] = []  # Tracks recently used keys for fast eviction
_cache_stats = {"hits": 0, "misses": 0, "evictions": 0}

def get_cache_key(prompt: str, system: str = None) -> str:
    """Generate cache key for prompt and system message"""
    content = f"{system or ''}:{prompt}"
    return hashlib.md5(content.encode()).hexdigest()

def get_cached_response(cache_key: str) -> Optional[str]:
    """Get cached response if it exists and is not expired (thread-safe)"""
    if not CACHE_ENABLED:
        return None
    
    with _cache_lock:
        if cache_key in _response_cache:
            cached = _response_cache[cache_key]
            # Cache expires after configured duration
            if time.time() - cached['timestamp'] < CACHE_DURATION:
                # Update LRU status (move to end = most recently used)
                if cache_key in _lru_list:
                    _lru_list.remove(cache_key)
                _lru_list.append(cache_key)
                
                # Log cache hit for debugging
                _cache_stats["hits"] += 1
                if os.environ.get('ITERMINAL_DEBUG', '0') == '1':
                    print(f"Cache hit for {cache_key[:6]}... ({_cache_stats['hits']} hits, {_cache_stats['misses']} misses)")
                return cached['response']
            else:
                # Expired entry
                del _response_cache[cache_key]
                if cache_key in _lru_list:
                    _lru_list.remove(cache_key)
        
        _cache_stats["misses"] += 1
        return None

def cache_response(cache_key: str, response: str):
    """Cache a response with timestamp (thread-safe)"""
    if not CACHE_ENABLED:
        return
    
    with _cache_lock:
        # Limit cache size to prevent memory issues
        max_cache_size = int(os.environ.get('ITERMINAL_MAX_CACHE_SIZE', '1000'))
        
        if len(_response_cache) >= max_cache_size:
            # Efficient LRU eviction - remove 20% of least recently used items
            evict_count = max(1, max_cache_size // 5)
            keys_to_remove = _lru_list[:evict_count]
            
            for k in keys_to_remove:
                if k in _response_cache:
                    del _response_cache[k]
            
            _lru_list[:] = _lru_list[evict_count:]  # Efficient list slicing
            _cache_stats["evictions"] += evict_count
        
        # Add to cache and LRU list
        _response_cache[cache_key] = {
            'response': response,
            'timestamp': time.time()
        }
        _lru_list.append(cache_key)
        
        # Log cache stats in debug mode
        if os.environ.get('ITERMINAL_DEBUG', '0') == '1' and len(_response_cache) % 10 == 0:
            print(f"Cache size: {len(_response_cache)}, hits: {_cache_stats['hits']}, " 
                  f"misses: {_cache_stats['misses']}, evictions: {_cache_stats['evictions']}")

# Worker function for parallel Ollama requests
def _make_ollama_request(url, payload, timeout=60):
    """
    Make an API request to Ollama.
    Returns a tuple of (status_code, response_json) or (status_code, error_message).
    """
    try:
        response = requests.post(url, json=payload, timeout=timeout)
        if response.status_code == 200:
            return response.status_code, response.json()
        return response.status_code, f"Error: Status code {response.status_code}"
    except Exception as e:
        return 500, f"Error: {str(e)}"

def clean_ai_response(response: str) -> str:
    """Enhanced cleaning of AI response by removing markdown formatting and extra text"""
    if not response:
        return ""
    
    # Remove markdown code blocks
    if response.startswith('```') and response.endswith('```'):
        response = response[3:-3].strip()
    elif response.startswith('```'):
        response = response[3:].strip()
    elif response.endswith('```'):
        response = response[:-3].strip()
    
    # Remove language specifiers like ```bash, ```shell, etc.
    lines = response.split('\n')
    if lines and lines[0].strip() in ['bash', 'shell', 'sh', 'zsh', 'python', 'js', 'json']:
        lines = lines[1:]
    
    # Join lines and clean up
    cleaned = '\n'.join(lines).strip()
    
    # Remove common AI prefixes/suffixes
    prefixes_to_remove = [
        'The correct command is:',
        'Here is the command:',
        'You can use:',
        'Try this command:',
        'The command you need is:',
        'Command:',
        'Here\'s the command:',
        'You should use:',
        'I recommend:'
    ]
    
    for prefix in prefixes_to_remove:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
    
    # Remove quotes if they wrap the entire response
    if (cleaned.startswith('"') and cleaned.endswith('"')) or \
       (cleaned.startswith("'") and cleaned.endswith("'")):
        cleaned = cleaned[1:-1].strip()
    
    return cleaned

def ask_openrouter(prompt: str, system: str = None, max_retries: int = 3) -> str:
    """Enhanced OpenRouter API call with better error handling and retries"""
    api_key = get_api_key()
    if not api_key:
        return "[OpenRouter API key not set. Set OPENROUTER_API_KEY env variable. See README.]"
    
    # Check cache first if enabled
    cache_key = get_cache_key(prompt, system)
    if CACHE_ENABLED:
        cached_response = get_cached_response(cache_key)
        if cached_response:
            return cached_response
    
    # Trim prompt if performance mode is enabled
    if PERFORMANCE_MODE and len(prompt) > 500:
        prompt = prompt[:500]
        
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Rsaimukesh/iTerminal",
        "X-Title": "iTerminal"
    }
    messages = []
    if system:
        # Simplify system prompt in performance mode
        if PERFORMANCE_MODE and len(system) > 300:
            system = system[:300]
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    # Parallelize model calls and return first successful completion
    def _call_model(model_name: str):
        payload = {
            "model": model_name,
            "messages": messages,
            "max_tokens": 512,
            "temperature": 0.1,
            "top_p": 0.9,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            return model_name, resp
        except Exception:
            return model_name, None

    futures = [_thread_executor.submit(_call_model, m) for m in AI_MODELS]
    for future in as_completed(futures):
        model, resp = future.result()
        if resp is None:
            continue
        if resp.status_code == 200:
            result = resp.json()
            raw_response = result['choices'][0]['message']['content'].strip()
            cleaned = clean_ai_response(raw_response)
            cache_response(cache_key, cleaned)
            # Cancel remaining model calls
            for f in futures:
                if not f.done(): f.cancel()
            return cleaned
        elif resp.status_code == 401:
            return "[AI error: Invalid API key. Please check your OpenRouter API key.]"
        else:
            continue
    return "[AI error: No available model or network error. Please check your API key or try again later.]"

def _make_ollama_request(url: str, payload: Dict, timeout: int = 60) -> Tuple[int, Dict]:
    """Make a single request to Ollama API (worker function for threading)"""
    try:
        with _request_lock:  # Prevent too many concurrent requests to Ollama
            response = requests.post(url, json=payload, timeout=timeout)
        return response.status_code, response.json() if response.status_code == 200 else {}
    except Exception as e:
        return 500, {"error": str(e)}

def ask_ollama(prompt: str, system: str = None, max_retries: int = 3) -> str:
    """Call Ollama API for local LLM inference with hyperthreaded optimization"""
    # Check cache first if enabled
    if CACHE_ENABLED:
        cache_key = get_cache_key(prompt, system)
        cached_response = get_cached_response(cache_key)
        if cached_response:
            return cached_response
    
    # Trim prompt if performance mode is enabled
    if PERFORMANCE_MODE and len(prompt) > 500:
        prompt = prompt[:500]
    
    url = f"{OLLAMA_BASE_URL}/api/chat"
    
    # Prepare messages
    messages = []
    if system:
        # Simplify system prompt in performance mode
        if PERFORMANCE_MODE and len(system) > 300:
            system = system[:300]
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    # Prepare request payload with optimized settings
    ctx_size = 1024 if REDUCED_CONTEXT else 2048  # Reduce context for better performance
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.1,  # Lower temperature for faster, more deterministic responses
            "top_p": 0.8,        # Lower top_p for faster sampling
            "num_ctx": ctx_size,
            "num_gpu": 1,        # Ensure GPU is used if available
            "seed": 42,          # Fixed seed for consistent responses
            "num_thread": MAX_CONCURRENT_TASKS  # Use optimal thread count for Ollama processing
        }
    }
    
    # Use hyperthreading for request handling if enabled
    if HYPERTHREAD_ENABLED:
        cache_key = get_cache_key(prompt, system)
        
        # Create multiple request futures with different seeds for diversity
        futures = []
        for i in range(min(max_retries, PARALLEL_REQUESTS)):
            # Slightly vary the payload for each parallel request
            payload_copy = payload.copy()
            payload_copy["options"] = payload["options"].copy()
            payload_copy["options"]["seed"] = 42 + i  # Different seed for each request
            
            # Submit the request to thread pool
            futures.append(_thread_executor.submit(
                _make_ollama_request, url, payload_copy, 30 + i*10))
        
        # Process results as they complete
        for future in as_completed(futures):
            status_code, result = future.result()
            if status_code == 200:
                raw_response = result.get('message', {}).get('content', '')
                if not raw_response and 'response' in result:
                    raw_response = result.get('response', '')  # Fallback for older Ollama versions
                
                cleaned = clean_ai_response(raw_response.strip())
                cache_response(cache_key, cleaned)
                return cleaned
        
        # If all parallel requests failed, try sequential approach as fallback
    
    # Sequential approach (traditional or fallback)
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, timeout=60)
            if response.status_code == 200:
                result = response.json()
                raw_response = result.get('message', {}).get('content', '')
                if not raw_response and 'response' in result:
                    raw_response = result.get('response', '')  # Fallback for older Ollama versions
                
                cleaned = clean_ai_response(raw_response.strip())
                if CACHE_ENABLED:
                    cache_key = get_cache_key(prompt, system)
                    cache_response(cache_key, cleaned)
                return cleaned
            else:
                error = f"[Ollama error: Server returned status code {response.status_code}]"
                if attempt < max_retries - 1:
                    time.sleep(1)  # Simple retry delay
        except requests.exceptions.Timeout:
            error = "[Ollama error: Request timed out]"
            if attempt < max_retries - 1:
                time.sleep(1)
        except Exception as e:
            error = f"[Ollama error: {str(e)}]"
            if attempt < max_retries - 1:
                time.sleep(1)
    
    return error

def is_ollama_available() -> bool:
    """Check if Ollama is available by making a ping request"""
    try:
        import requests
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False

def ask_ai(prompt: str, system: str = None) -> str:
    """Main AI interface with provider selection and fallback"""
    current_provider = get_ai_provider()
    
    # Try Ollama if it's the selected provider
    if current_provider == 'ollama':
        # First check if Ollama is available
        if is_ollama_available():
            result = ask_ollama(prompt, system)
            # Check if we got an error response
            if not result.startswith("[Ollama error:"):
                return result
            # If we got an error, fall back to OpenRouter
        
        # Ollama not available or returned an error, fall back to OpenRouter
        api_key = get_api_key()
        if not api_key or api_key == "ollama":
            # No API key for OpenRouter, return error message
            return "[AI ERROR: Ollama server not available and no OpenRouter API key is set]"
        
        # We have an API key, try OpenRouter
        fallback_message = "[AI NOTICE: Ollama server not available. Using OpenRouter as fallback]"
        openrouter_result = ask_openrouter(prompt, system)
        
        # Check if OpenRouter response is an error
        if openrouter_result.startswith("[AI error:") or openrouter_result.startswith("[OpenRouter"):
            return fallback_message + " " + openrouter_result
        
        # Return successful response
        return openrouter_result
    else:
        # Use OpenRouter directly
        return ask_openrouter(prompt, system)

def explain_command(cmd: str) -> str:
    """Enhanced command explanation with more detailed output"""
    system_prompt = """You are a helpful Linux command explainer. Explain commands in simple, beginner-friendly terms. 
    Focus on what the command does, potential risks, and common use cases. Keep explanations clear and concise (2-3 sentences).
    If the command is potentially dangerous, mention safety considerations."""
    prompt = f"Explain this Linux command in simple terms: {cmd}"
    return ask_ai(prompt, system_prompt)

def translate_nl_to_shell(nl: str) -> str:
    """Enhanced natural language to shell translation with better safety and error handling"""
    system_prompt = """You are a Linux command translator. Convert natural language to safe, executable Linux commands.
    - Only output the command, nothing else
    - Do NOT use markdown formatting, code blocks, or quotes
    - Do NOT add explanations or extra text
    - Use common Linux commands (apt, ls, cat, etc.)
    - Prefer safe commands over dangerous ones
    - If the request is potentially dangerous, suggest a safer alternative
    - For file operations, use relative paths when possible
    - For system operations, suggest user-level commands first
    - If the input is unclear or ambiguous, make your best guess based on common Linux tasks
    - For typos or misspellings, correct them and provide the intended command"""
    prompt = f"Translate to Linux command: {nl}"
    result = ask_ai(prompt, system_prompt)
    
    # Ensure error messages are properly formatted to be identifiable
    if result.startswith('[AI error:') or result.startswith('[Ollama') or result.startswith('[OpenRouter'):
        return result
    
    # For general greetings or conversational inputs, return clear message
    if nl.lower().strip() in ['hi', 'hello', 'hey', 'greetings', 'howdy', 'how are you']:
        return "[AI NOTICE: This is a conversational prompt, not a command request]"
    
    return result

def generate_multiple_interpretations(nl: str) -> list:
    """Generate multiple possible interpretations of unclear natural language input"""
    system_prompt = """You are a Linux command interpreter. Given unclear or ambiguous natural language, generate 3-4 possible Linux commands.
    - Output only the commands, one per line
    - Do NOT use markdown formatting, code blocks, or quotes
    - Do NOT add explanations or extra text
    - Include both simple and more specific interpretations
    - Focus on common Linux tasks and operations
    - If the input has typos, provide commands for both the original and corrected versions"""
    
    prompt = f"Generate 3-4 possible Linux commands for this unclear input: {nl}"
    response = ask_ai(prompt, system_prompt)
    
    # Parse multiple commands from response
    commands = []
    for line in response.split('\n'):
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('//'):
            # Clean up any remaining formatting
            line = clean_ai_response(line)
            if line and line not in commands:
                commands.append(line)
    
    return commands[:4]  # Return up to 4 commands

def handle_ambiguous_prompt(nl: str) -> dict:
    """Handle ambiguous or unclear prompts by generating multiple interpretations"""
    system_prompt = """You are a Linux command assistant. Given an unclear or potentially incorrect prompt, provide:
    1. The most likely intended command
    2. Alternative interpretations
    3. A brief explanation of what you think the user wants
    4. Suggestions for clearer input
    
    Format your response as a JSON object with:
    - "primary_command": the most likely command
    - "alternatives": array of alternative commands
    - "interpretation": what you think the user wants
    - "suggestions": array of clearer ways to ask for the same thing
    - "confidence": number between 0-1 indicating your confidence"""
    
    prompt = f"Analyze this unclear Linux command request: {nl}"
    response = ask_ai(prompt, system_prompt)
    
    try:
        # Try to parse JSON response
        if response.startswith('{') and response.endswith('}'):
            return json.loads(response)
    except:
        pass
    
    # Fallback: generate multiple interpretations
    alternatives = generate_multiple_interpretations(nl)
    primary = alternatives[0] if alternatives else "ls"  # Default fallback
    
    return {
        "primary_command": primary,
        "alternatives": alternatives[1:] if len(alternatives) > 1 else [],
        "interpretation": f"I think you want to {nl.lower()}",
        "suggestions": [
            f"list files in current directory",
            f"show system information", 
            f"check running processes"
        ],
        "confidence": 0.3
    }

def correct_typos_and_suggest(nl: str) -> dict:
    """Correct typos in natural language and suggest commands"""
    system_prompt = """You are a Linux command assistant that corrects typos and suggests commands.
    Given input that may contain typos or misspellings, provide:
    1. The corrected natural language
    2. The corresponding Linux command
    3. Alternative interpretations if the correction is uncertain
    
    Format as JSON:
    - "corrected_input": the corrected natural language
    - "command": the Linux command
    - "alternatives": array of other possible corrections
    - "confidence": number between 0-1"""
    
    prompt = f"Correct typos and suggest Linux command for: {nl}"
    response = ask_ai(prompt, system_prompt)
    
    try:
        if response.startswith('{') and response.endswith('}'):
            return json.loads(response)
    except:
        pass
    
    # Fallback: simple correction attempt
    corrected = nl.lower().replace('upadte', 'update').replace('systm', 'system').replace('proces', 'process')
    command = translate_nl_to_shell(corrected)
    
    return {
        "corrected_input": corrected,
        "command": command,
        "alternatives": [],
        "confidence": 0.5
    }

def smart_command_generation(nl: str) -> dict:
    """Smart command generation that handles various types of unclear input"""
    
    # First, try normal translation
    normal_result = translate_nl_to_shell(nl)
    
    # Check if this is a notice or error message from our handlers
    if normal_result.startswith('[AI') or normal_result.startswith('[Ollama') or normal_result.startswith('[OpenRouter'):
        return {
            "command": normal_result,
            "explanation": "This is a notification, not a command",
            "alternatives": [],
            "method": "notice"
        }
    
    # If it looks like an error or is too generic, try more sophisticated approaches
    if (normal_result in ['ls', 'pwd', 'whoami'] or 
        len(normal_result.strip()) < 3):
        
        # Try typo correction
        typo_result = correct_typos_and_suggest(nl)
        if typo_result.get('confidence', 0) > 0.3:
            return {
                "command": typo_result['command'],
                "explanation": f"Corrected '{nl}' to '{typo_result['corrected_input']}'",
                "alternatives": typo_result.get('alternatives', []),
                "method": "typo_correction"
            }
        
        # Try ambiguous prompt handling
        ambiguous_result = handle_ambiguous_prompt(nl)
        if ambiguous_result.get('confidence', 0) > 0.2:
            return {
                "command": ambiguous_result['primary_command'],
                "explanation": ambiguous_result['interpretation'],
                "alternatives": ambiguous_result.get('alternatives', []),
                "method": "interpretation"
            }
        
        # Generate multiple interpretations as fallback
        interpretations = generate_multiple_interpretations(nl)
        if interpretations:
            return {
                "command": interpretations[0],
                "explanation": f"Generated command based on '{nl}'",
                "alternatives": interpretations[1:],
                "method": "generation"
            }
    
    # Return normal result if it seems reasonable
    return {
        "command": normal_result,
        "explanation": f"Translated '{nl}' to command",
        "alternatives": [],
        "method": "translation"
    }

def suggest_common_commands_for_context(nl: str) -> list:
    """Suggest common commands based on keywords in the input"""
    keywords = nl.lower().split()
    suggestions = []
    
    # Common command patterns based on keywords
    patterns = {
        'file': ['ls -la', 'find . -name "*.txt"', 'cat filename', 'head -n 10 filename'],
        'list': ['ls -la', 'ls -lh', 'ls -la | head -10'],
        'find': ['find . -name "pattern"', 'locate filename', 'which command'],
        'search': ['grep -r "text" .', 'find . -name "*.txt" -exec grep -l "text" {} \\;'],
        'process': ['ps aux', 'top', 'htop', 'ps aux | grep process'],
        'kill': ['pkill process', 'killall process', 'kill -9 pid'],
        'update': ['sudo apt update', 'sudo apt upgrade', 'sudo apt update && sudo apt upgrade'],
        'install': ['sudo apt install package', 'sudo apt-get install package'],
        'system': ['uname -a', 'lsb_release -a', 'cat /etc/os-release'],
        'network': ['ifconfig', 'ip addr', 'ping google.com', 'netstat -tuln'],
        'disk': ['df -h', 'du -sh *', 'lsblk', 'fdisk -l'],
        'user': ['whoami', 'who', 'w', 'id'],
        'help': ['man command', 'command --help', 'info command'],
        'clear': ['clear', 'reset', 'echo -e "\\033c"'],
        'history': ['history', 'history | grep pattern', 'fc -l']
    }
    
    for keyword in keywords:
        for pattern, commands in patterns.items():
            if keyword in pattern or pattern in keyword:
                suggestions.extend(commands)
    
    # Remove duplicates and limit results
    unique_suggestions = list(dict.fromkeys(suggestions))
    return unique_suggestions[:5]

def correct_shell_command(cmd: str, error: str) -> str:
    """Enhanced command correction with better error analysis"""
    import difflib
    
    # Handle capitalization issues for common commands
    first_word = cmd.strip().split()[0] if cmd.strip() else ""
    common_commands = [
        "ls", "pwd", "cd", "cat", "grep", "echo", "find", "rm", "cp", "mv", "touch", "mkdir", "rmdir",
        "apt", "apt-get", "yum", "dnf", "pacman", "curl", "wget", "sudo", "ssudo", "chmod", "chown", "ps", "top",
        "git", "ssh", "scp", "ping", "ifconfig", "ip", "netstat", "tar", "zip", "unzip", "man", "nano", 
        "vim", "less", "more", "head", "tail", "wc", "sort", "uniq", "awk", "sed", "cut", "diff", "xargs",
        "clear", "history", "df", "du", "free", "kill", "which", "whoami", "date", "time", "make"
    ]
    
    # Check for case issues (all caps or first letter capitalized)
    if first_word.lower() in common_commands:
        if first_word != first_word.lower():
            # This is a capitalization issue, return the lowercase version
            return first_word.lower() + cmd[len(first_word):]
    
    # Check for common non-existent commands using difflib
    if "no such file or directory" in error.lower():
        # First try to find close matches with common commands
        closest_matches = difflib.get_close_matches(first_word.lower(), common_commands, n=1, cutoff=0.6)
        
        if closest_matches:
            suggested = closest_matches[0] + cmd[len(first_word):]
            explanation = f"'{cmd}' is not found. Did you mean '{suggested}'?"
            
            # Return the suggested command first, then the explanation
            return f"{suggested} [AI: {explanation}]"
        
        # If no close match found, use AI to get a better explanation
        current_provider = get_ai_provider()
        system_prompt = """You are a Linux command fixer. Given a failed command, suggest what the user might have meant.
        - If it's a non-existent command, clearly state it's not a standard Linux command
        - If you can recognize what they might have meant, suggest the correct command
        - Be specific about what command they might have wanted
        - Keep your explanation short and focused"""
        
        prompt = f"Command '{cmd}' failed with error: 'command not found'. What's the most likely correction or alternative?"
        result = ask_ai(prompt, system_prompt)
        
        # Try to extract commands from the AI response using various patterns
        import re
        
        # Pattern 1: Look for quoted commands
        command_match = re.search(r"'([a-z0-9][a-z0-9\-]+)'", result.lower())
        if command_match:
            suggested_command = command_match.group(1)
            if suggested_command in common_commands:
                # We found a valid command in the response
                return f"{suggested_command} [AI: {result}]"
        
        # Pattern 2: Look for commands in code blocks
        code_block_match = re.search(r"```(?:bash|sh)?\s*([a-z0-9][a-z0-9\-]+\s+[^\n]+)", result.lower())
        if code_block_match:
            code_command = code_block_match.group(1).strip()
            first_word_code = code_command.split()[0]
            if first_word_code in common_commands:
                return f"{code_command} [AI: {result}]"
        
        # Pattern 3: Look for "use mv" or similar phrases or "the correct command is/for..."
        use_command_match = re.search(r"(?:use|correct command (?:is|for))[\s'`]*([a-z0-9][a-z0-9\-]+)['`\s]", result.lower())
        if use_command_match:
            use_cmd = use_command_match.group(1)
            if use_cmd in common_commands:
                # Basic suggestion based on the original command
                args = cmd.split()[1:] if len(cmd.split()) > 1 else []
                suggested = f"{use_cmd} {' '.join(args)}".strip()
                return f"{suggested} [AI: {result}]"
                
        # Special cases for common command mistakes
        if cmd.lower().startswith('rn ') and len(cmd.split()) > 1:
            # 'rn' is likely trying to rename a file, suggest 'mv' instead
            file_args = cmd.split(' ', 1)[1]
            return f"mv {file_args} [AI: {result}]"
                
        # If we can't extract a valid command, just return the AI explanation
        return f"[AI: {result}]"
    
    # For other cases, use AI
    system_prompt = """You are a Linux command fixer. Given a failed command and its error, suggest the correct command.
    - Only output the corrected command, nothing else
    - Do NOT use markdown formatting, code blocks, or quotes
    - Do NOT add explanations or extra text
    - Fix typos, missing packages, wrong syntax
    - Use common Linux commands and package managers
    - If the error suggests a missing package, suggest the install command
    - If the error suggests permission issues, suggest the correct sudo usage UNLESS the original command already used 'ssudo'
    - If the command already uses 'ssudo', DO NOT suggest replacing it with 'sudo'
    - If the command uses 'ssudo' but the command doesn't exist, suggest a non-privileged alternative
    - If the error suggests a file not found, suggest common alternatives"""
    
    # Special handling for ssudo command to avoid suggesting sudo when ssudo is already used
    if first_word.lower() == "ssudo":
        system_prompt += """
    - This command is using 'ssudo' which is a special version of sudo for this environment
    - DO NOT suggest replacing 'ssudo' with 'sudo' as this will cause a loop
    - Instead, if the command doesn't work, suggest a non-privileged alternative or a fix that keeps 'ssudo'
    - If the command requires installation, suggest a more specific command that would work"""
    
    prompt = f"Command '{cmd}' failed with error: '{error}'. What's the correct command?"
    return ask_ai(prompt, system_prompt)

def suggest_related_commands(cmd: str) -> str:
    """Enhanced related command suggestions with better categorization"""
    system_prompt = """You are a Linux command expert. Suggest 3-4 related or alternative commands.
    - Only output the commands, one per line
    - Focus on useful alternatives and variations
    - Keep suggestions practical and commonly used
    - Include both simpler and more advanced alternatives
    - Group related commands together"""
    prompt = f"Suggest 3-4 related commands for: {cmd}"
    return ask_ai(prompt, system_prompt)

def analyze_sudo_command_safety(cmd: str) -> Dict[str, Any]:
    """Specialized AI-based analysis for sudo commands to determine if they're safe to run."""
    # Extract the actual command being run with sudo
    sudo_cmd_parts = cmd.strip().split()
    if len(sudo_cmd_parts) < 2:
        return {
            "safe": False,
            "risk_level": "medium",
            "warning": "Incomplete sudo command.",
            "safer_alternative": "",
            "requires_confirmation": True
        }
    
    # Get the command without sudo
    cmd_without_sudo = ' '.join(sudo_cmd_parts[1:])
    
    # Categories of sudo commands
    benign_sudo_cmds = [
        'apt update', 'apt upgrade', 'apt install', 'apt-get update', 'apt-get upgrade',
        'yum update', 'yum upgrade', 'pacman -Syu', 'dnf update', 'zypper update',
        'systemctl start', 'systemctl stop', 'systemctl restart', 'systemctl status',
        'service start', 'service stop', 'service restart', 'service status',
        'cat', 'less', 'more', 'ls', 'find'
    ]
    
    # Common sudo commands that are typically safe
    if any(cmd_without_sudo.startswith(safe_cmd) for safe_cmd in benign_sudo_cmds):
        return {
            "safe": True,
            "risk_level": "low",
            "warning": "This is a common sudo command used for system management.",
            "safer_alternative": "",
            "requires_confirmation": True  # Still require confirmation for sudo commands
        }
    
    # Dangerous commands that should be blocked even with sudo
    dangerous_sudo_cmds = [
        'rm -rf /', 'rm -rf /*', 'dd if=/dev/zero of=/dev/sda', 
        'mkfs', 'fdisk', 'dd status=none of=/dev/sda', 'shred',
        'chown -R root:root /', 'chmod -R 777 /',
        ': > /dev/sda', '> /dev/sda'
    ]
    
    if any(cmd_without_sudo.startswith(dangerous) for dangerous in dangerous_sudo_cmds):
        return {
            "safe": False,
            "risk_level": "critical",
            "warning": "This sudo command is extremely dangerous and could damage your system permanently.",
            "safer_alternative": "",
            "requires_confirmation": True
        }
    
    # For other commands, use the AI to analyze safety
    system_prompt = """You are a Linux security expert analyzing sudo commands. Your task is to determine if a sudo command is safe to run.
    Return a JSON object with:
    - "safe": boolean (true/false)
    - "risk_level": string ("low", "medium", "high", "critical")
    - "warning": string (brief explanation of risks if any)
    - "safer_alternative": string (suggested safer command if applicable)
    - "requires_confirmation": boolean (whether user should confirm before executing)
    
    Guidelines:
    - Most package management commands (apt, yum, etc.) are generally safe
    - System service management (systemctl, service) is generally safe
    - File operations that modify important system files are risky
    - Commands that could cause data loss are high risk
    - Commands that could brick the system are critical risk
    - If unsure, be cautious and mark as requiring confirmation
    """
    
    prompt = f"Analyze the safety of this Linux sudo command: {cmd}"
    response = ask_ai(prompt, system_prompt)
    
    try:
        if response.startswith('{') and response.endswith('}'):
            return json.loads(response)
    except:
        pass
    
    # Fallback: assume medium risk for sudo commands
    return {
        "safe": True,  # Allow but with warning
        "risk_level": "medium",
        "warning": "This sudo command requires elevated privileges. Review carefully before proceeding.",
        "safer_alternative": "",
        "requires_confirmation": True
    }

def analyze_command_safety(cmd: str) -> Dict[str, Any]:
    """Analyze command safety and provide warnings, with input validation and sanitization. Suggest dry-run alternatives for dangerous commands."""
    import re
    # Only block truly dangerous shell metacharacters and patterns
    blocked_patterns = [
        r';', r'&&', r'\|', r'\$', r'`', r'\(', r'\)', r'\[', r'\]', r'\{', r'\}',
        r'\>', r'<', r'\*', r'\?', r'!', r'\^', r'~', r'\#', r'%', r'&', r'\=', r'@', r'\;', r','
    ]
    # Block empty or whitespace-only commands
    if not cmd or not cmd.strip():
        return {
            "safe": False,
            "risk_level": "low",
            "warning": "Empty or whitespace-only command.",
            "safer_alternative": "",
            "requires_confirmation": False
        }
    # Special handling for sudo commands using AI-based safety analysis
    if cmd.strip().startswith('sudo'):
        return analyze_sudo_command_safety(cmd)
    # Block suspicious characters and patterns
    for pat in blocked_patterns:
        if re.search(pat, cmd):
            return {
                "safe": False,
                "risk_level": "high",
                "warning": f"Command contains potentially dangerous or invalid pattern: {pat}",
                "safer_alternative": suggest_dry_run(cmd),
                "requires_confirmation": True
            }
    # Block command injection attempts
    if re.search(r'[;&|`]', cmd):
        return {
            "safe": False,
            "risk_level": "critical",
            "warning": "Command injection attempt detected.",
            "safer_alternative": suggest_dry_run(cmd),
            "requires_confirmation": True
        }
    # Block dangerous commands
    cmd_lower = cmd.lower()
    if any(dangerous in cmd_lower for dangerous in ['rm -rf /', 'dd if=/dev/zero', 'mkfs', 'fdisk']):
        return {
            "safe": False,
            "risk_level": "critical",
            "warning": "This command can cause permanent data loss",
            "safer_alternative": suggest_dry_run(cmd),
            "requires_confirmation": True
        }
    elif any(risky in cmd_lower for risky in ['rm -rf', 'chmod 777', 'chown root']):
        return {
            "safe": False,
            "risk_level": "high",
            "warning": "This command can be dangerous if used incorrectly",
            "safer_alternative": suggest_dry_run(cmd),
            "requires_confirmation": True
        }
    # If passed validation, proceed with AI-based safety analysis
    system_prompt = """You are a Linux security expert. Analyze the safety of a command.\nReturn a JSON object with:\n- \"safe\": boolean (true/false)\n- \"risk_level\": string (\"low\", \"medium\", \"high\", \"critical\")\n- \"warning\": string (explanation of risks if any)\n- \"safer_alternative\": string (suggested safer command if applicable)\n- \"requires_confirmation\": boolean (whether user should confirm)"""
    prompt = f"Analyze the safety of this Linux command: {cmd}"
    response = ask_ai(prompt, system_prompt)
    try:
        if response.startswith('{') and response.endswith('}'):
            return json.loads(response)
    except:
        pass
    # Fallback: safe
    return {
        "safe": True,
        "risk_level": "low",
        "warning": "",
        "safer_alternative": "",
        "requires_confirmation": False
    }

def suggest_dry_run(cmd: str) -> str:
    """Suggest a dry-run or safe alternative for dangerous commands if possible."""
    cmd = cmd.strip()
    if cmd.startswith('rm '):
        return cmd.replace('rm ', 'rm -i ', 1) + '   # -i for interactive prompt before delete'
    if cmd.startswith('cp '):
        return cmd + ' -n   # -n for no-clobber (don\'t overwrite)'
    if cmd.startswith('mv '):
        return cmd + ' -i   # -i for interactive prompt before overwrite'
    if cmd.startswith('git push'):
        return 'git push --dry-run'
    if cmd.startswith('git commit'):
        return 'git commit --dry-run'
    if cmd.startswith('rsync '):
        return cmd + ' --dry-run'
    return ''

def get_command_complexity(cmd: str) -> str:
    """Determine command complexity level for better explanations"""
    system_prompt = """You are a Linux command complexity analyzer. Rate the complexity of a command.
    Return only one word: "beginner", "intermediate", or "advanced"."""
    prompt = f"Rate the complexity of this Linux command: {cmd}"
    response = ask_ai(prompt, system_prompt).lower().strip()
    
    if response in ['beginner', 'intermediate', 'advanced']:
        return response
    return 'intermediate'  # Default fallback 