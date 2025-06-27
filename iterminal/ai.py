import requests
import json
import hashlib
import time
from typing import Optional, Dict, Any
from rich.console import Console
from .config import get_api_key

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
    
    for attempt in range(max_retries):
        for model in AI_MODELS:
            data = {
                "model": model,
                "messages": messages,
                "max_tokens": 512,  # Increased for better responses
                "temperature": 0.1,  # Lower for more consistent results
                "top_p": 0.9,
                "frequency_penalty": 0.1,
                "presence_penalty": 0.1
            }
            try:
                resp = requests.post(url, headers=headers, json=data, timeout=15)
                if resp.status_code == 200:
                    result = resp.json()
                    raw_response = result['choices'][0]['message']['content'].strip()
                    cleaned_response = clean_ai_response(raw_response)
                    
                    # Cache successful response
                    cache_response(cache_key, cleaned_response)
                    return cleaned_response
                elif resp.status_code == 429:  # Rate limit
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                elif resp.status_code == 401:  # Auth error
                    return "[AI error: Invalid API key. Please check your OpenRouter API key.]"
                else:
                    continue  # Try next model
            except requests.exceptions.Timeout:
                continue  # Try next model
            except requests.exceptions.RequestException:
                continue  # Try next model
            except Exception as e:
                continue  # Try next model
    
    return "[AI error: No available model or network error. Please check your API key or try again later.]"

def ask_ai(prompt: str, system: str = None) -> str:
    """Main AI interface with enhanced error handling"""
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
    return ask_ai(prompt, system_prompt)

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
    
    # If it looks like an error or is too generic, try more sophisticated approaches
    if (normal_result.startswith('[AI error') or 
        normal_result in ['ls', 'pwd', 'whoami'] or 
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
    """Analyze command safety and provide warnings"""
    system_prompt = """You are a Linux security expert. Analyze the safety of a command.
    Return a JSON object with:
    - "safe": boolean (true/false)
    - "risk_level": string ("low", "medium", "high", "critical")
    - "warning": string (explanation of risks if any)
    - "safer_alternative": string (suggested safer command if applicable)
    - "requires_confirmation": boolean (whether user should confirm)"""
    
    prompt = f"Analyze the safety of this Linux command: {cmd}"
    response = ask_ai(prompt, system_prompt)
    
    try:
        # Try to parse JSON response
        if response.startswith('{') and response.endswith('}'):
            return json.loads(response)
    except:
        pass
    
    # Fallback analysis
    cmd_lower = cmd.lower()
    if any(dangerous in cmd_lower for dangerous in ['rm -rf /', 'dd if=/dev/zero', 'mkfs', 'fdisk']):
        return {
            "safe": False,
            "risk_level": "critical",
            "warning": "This command can cause permanent data loss",
            "safer_alternative": "",
            "requires_confirmation": True
        }
    elif any(risky in cmd_lower for risky in ['rm -rf', 'chmod 777', 'chown root']):
        return {
            "safe": False,
            "risk_level": "high",
            "warning": "This command can be dangerous if used incorrectly",
            "safer_alternative": "",
            "requires_confirmation": True
        }
    else:
        return {
            "safe": True,
            "risk_level": "low",
            "warning": "",
            "safer_alternative": "",
            "requires_confirmation": False
        }

def get_command_complexity(cmd: str) -> str:
    """Determine command complexity level for better explanations"""
    system_prompt = """You are a Linux command complexity analyzer. Rate the complexity of a command.
    Return only one word: "beginner", "intermediate", or "advanced"."""
    prompt = f"Rate the complexity of this Linux command: {cmd}"
    response = ask_ai(prompt, system_prompt).lower().strip()
    
    if response in ['beginner', 'intermediate', 'advanced']:
        return response
    return 'intermediate'  # Default fallback 