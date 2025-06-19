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


def ask_openrouter(prompt: str, system: str = None) -> str:
    api_key = get_api_key()
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
            "max_tokens": 128,
            "temperature": 0.2
        }
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=30)
            if resp.status_code == 200:
                result = resp.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                continue  # Try next model
        except Exception as e:
            continue
    return "[AI error: No available model or network error. Please check your API key or try again later.]"

def ask_ai(prompt: str, system: str = None) -> str:
    return ask_openrouter(prompt, system)

def explain_command(cmd: str) -> str:
    prompt = f"Explain in simple terms what this command does: {cmd}"
    return ask_ai(prompt)

def translate_nl_to_shell(nl: str) -> str:
    prompt = f"Translate this natural language instruction to a Linux shell command, only output the command, nothing else: {nl}"
    return ask_ai(prompt)

def correct_shell_command(cmd: str, error: str) -> str:
    prompt = f"The user tried to run this command: '{cmd}' and got this error: '{error}'. Suggest the correct Linux shell command, only output the command, nothing else."
    return ask_ai(prompt) 