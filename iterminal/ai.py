import requests
import json
import hashlib
import time
from typing import Optional, Dict, Any
from rich.console import Console
from .config import get_api_key, get_ai_provider, OLLAMA_BASE_URL, OLLAMA_MODEL
from concurrent.futures import ThreadPoolExecutor, as_completed

console = Console()

# Enhanced model list with better fallbacks and reliability
AI_MODELS = [
    "anthropic/claude-3.5-sonnet",  # Most reliable
    "openai/gpt-4o-mini",           # Good balance
    "openai/gpt-3.5-turbo",         # Fast and reliable
    "openchat/openchat-3.5-0106",   # Free option
    "mistralai/mixtral-8x7b",       # Alternative free option
    "meta-llama/llama-3.1-8b-instruct"  # Local-friendly
]

# Executor for parallel AI model requests
_executor = ThreadPoolExecutor(max_workers=len(AI_MODELS))

# Response cache for better performance
_response_cache: Dict[str, Dict[str, Any]] = {}

def get_cache_key(prompt: str, system: str = None) -> str:
    """Generate cache key for prompt and system message"""
    content = f"{system or ''}:{prompt}"
    return hashlib.md5(content.encode()).hexdigest()

def get_cached_response(cache_key: str) -> Optional[str]:
    """Get cached response if it exists and is not expired"""
    if cache_key in _response_cache:
        cached = _response_cache[cache_key]
        # Cache expires after 1 hour
        if time.time() - cached['timestamp'] < 3600:
            return cached['response']
        else:
            del _response_cache[cache_key]
    return None

def cache_response(cache_key: str, response: str):
    """Cache a response with timestamp"""
    _response_cache[cache_key] = {
        'response': response,
        'timestamp': time.time()
    }

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
    
    # Check cache first
    cache_key = get_cache_key(prompt, system)
    cached_response = get_cached_response(cache_key)
    if cached_response:
        return cached_response
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/yourgithub/iterminal",
        "X-Title": "iTerminal"
    }
    messages = []
    if system:
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
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            return model_name, resp
        except Exception:
            return model_name, None

    futures = [_executor.submit(_call_model, m) for m in AI_MODELS]
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

def ask_ollama(prompt: str, system: str = None, max_retries: int = 3) -> str:
    """Call Ollama API for local LLM inference"""
    # Check cache first
    cache_key = get_cache_key(prompt, system)
    cached_response = get_cached_response(cache_key)
    if cached_response:
        return cached_response
    
    url = f"{OLLAMA_BASE_URL}/api/chat"
    
    # Prepare messages
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    # Prepare request payload
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "top_p": 0.9,
            "num_ctx": 2048
        }
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                raw_response = result.get('message', {}).get('content', '')
                if not raw_response and 'response' in result:
                    raw_response = result.get('response', '')  # Fallback for older Ollama versions
                
                cleaned = clean_ai_response(raw_response.strip())
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
        "apt", "apt-get", "yum", "dnf", "pacman", "curl", "wget", "sudo", "chmod", "chown", "ps", "top",
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
    - If the error suggests permission issues, suggest the correct sudo usage
    - If the error suggests a file not found, suggest common alternatives"""
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
    # Block sudo commands
    if cmd.strip().startswith('sudo'):
        return {
            "safe": False,
            "risk_level": "high",
            "warning": "sudo commands are not supported in iTerminal. Please run them in your system terminal.",
            "safer_alternative": cmd.strip().replace('sudo ', '', 1),
            "requires_confirmation": True
        }
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