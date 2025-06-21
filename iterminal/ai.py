import requests
from rich.console import Console
from .config import get_api_key

console = Console()

# Try a list of models in order of preference
AI_MODELS = [
    "openchat/openchat-3.5-0106",  # OpenRouter, free
    "mistralai/mixtral-8x7b",
    "openai/gpt-3.5-turbo"  # fallback if available
]


def clean_ai_response(response: str) -> str:
    """Clean AI response by removing markdown formatting and extra text"""
    # Remove markdown code blocks
    if response.startswith('```') and response.endswith('```'):
        response = response[3:-3].strip()
    elif response.startswith('```'):
        response = response[3:].strip()
    elif response.endswith('```'):
        response = response[:-3].strip()
    
    # Remove language specifiers like ```bash, ```shell, etc.
    lines = response.split('\n')
    if lines and lines[0].strip() in ['bash', 'shell', 'sh', 'zsh']:
        lines = lines[1:]
    
    # Join lines and clean up
    cleaned = '\n'.join(lines).strip()
    
    # Remove common AI prefixes/suffixes
    prefixes_to_remove = [
        'The correct command is:',
        'Here is the command:',
        'You can use:',
        'Try this command:',
        'The command you need is:'
    ]
    
    for prefix in prefixes_to_remove:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
    
    return cleaned

def ask_openrouter(prompt: str, system: str = None) -> str:
    api_key = get_api_key()
    if not api_key:
        return "[OpenRouter API key not set. Set OPENROUTER_API_KEY env variable. See README.]"
    
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
    
    for model in AI_MODELS:
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": 256,  # Increased for better responses
            "temperature": 0.1   # Lower for more consistent results
        }
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=30)
            if resp.status_code == 200:
                result = resp.json()
                raw_response = result['choices'][0]['message']['content'].strip()
                return clean_ai_response(raw_response)
            else:
                continue  # Try next model silently
        except Exception as e:
            continue  # Try next model silently
    
    return "[AI error: No available model or network error. Please check your API key or try again later.]"

def ask_ai(prompt: str, system: str = None) -> str:
    return ask_openrouter(prompt, system)

def explain_command(cmd: str) -> str:
    system_prompt = """You are a helpful Linux command explainer. Explain commands in simple, beginner-friendly terms. 
    Focus on what the command does, not how it works technically. Keep explanations under 2 sentences."""
    prompt = f"Explain this Linux command in simple terms: {cmd}"
    return ask_ai(prompt, system_prompt)

def translate_nl_to_shell(nl: str) -> str:
    system_prompt = """You are a Linux command translator. Convert natural language to safe, executable Linux commands.
    - Only output the command, nothing else
    - Do NOT use markdown formatting, code blocks, or quotes
    - Do NOT add explanations or extra text
    - Use common Linux commands (apt, ls, cat, etc.)
    - Prefer safe commands over dangerous ones
    - If unsure, suggest a basic command with a note"""
    prompt = f"Translate to Linux command: {nl}"
    return ask_ai(prompt, system_prompt)

def correct_shell_command(cmd: str, error: str) -> str:
    system_prompt = """You are a Linux command fixer. Given a failed command and its error, suggest the correct command.
    - Only output the corrected command, nothing else
    - Do NOT use markdown formatting, code blocks, or quotes
    - Do NOT add explanations or extra text
    - Fix typos, missing packages, wrong syntax
    - Use common Linux commands and package managers"""
    prompt = f"Command '{cmd}' failed with error: '{error}'. What's the correct command?"
    return ask_ai(prompt, system_prompt)

def suggest_related_commands(cmd: str) -> str:
    """Suggest related or alternative commands"""
    system_prompt = """You are a Linux command expert. Suggest 2-3 related or alternative commands.
    - Only output the commands, one per line
    - Focus on useful alternatives
    - Keep suggestions practical"""
    prompt = f"Suggest 2-3 related commands for: {cmd}"
    return ask_ai(prompt, system_prompt) 