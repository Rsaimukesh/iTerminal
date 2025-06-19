import os
import sys
import subprocess
import shlex
import readline
import datetime
from rich.console import Console
from rich.prompt import Prompt
from rich.text import Text
from rich.panel import Panel
import requests
from iterminal.cli import main_loop

# Optional: Use colorama if rich is not available
# from colorama import init, Fore, Style
# init(autoreset=True)

try:
    import openai
except ImportError:
    openai = None  # Placeholder for OpenAI SDK

# ========== CONFIG ==========
LOG_FILE = f"iterminal_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "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")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", None)

# ========== INIT ==========
console = Console()

if openai:
    openai.api_key = OPENAI_API_KEY

# ========== HELPERS ==========
def log_entry(entry: str):
    with open(LOG_FILE, 'a') as f:
        f.write(entry + '\n')

def is_probably_shell_command(user_input: str) -> bool:
    # Heuristic: if it starts with a known command or has spaces/flags
    return bool(user_input.strip() and (user_input.split()[0].isalpha() or user_input.startswith('./')))

def run_shell_command(cmd: str):
    try:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        return process.returncode, stdout, stderr
    except Exception as e:
        return -1, '', str(e)

def ask_openrouter(prompt: str, system: str = None) -> str:
    if not OPENROUTER_API_KEY:
        return "[OpenRouter API key not set. Set OPENROUTER_API_KEY env variable. See README. ]"
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/yourgithub/iterminal",  # Optional, for open source attribution
        "X-Title": "iTerminal"
    }
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    data = {
        "model": "mistralai/mixtral-8x7b",  # Free and good general model
        "messages": messages,
        "max_tokens": 128,
        "temperature": 0.2
    }
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"[OpenRouter error: {e}]"

def ask_ai(prompt: str, system: str = None) -> str:
    # Prefer OpenRouter, fallback to OpenAI if available
    if OPENROUTER_API_KEY:
        return ask_openrouter(prompt, system)
    try:
        if OPENAI_API_KEY:
            openai.api_key = OPENAI_API_KEY
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=128,
                temperature=0.2,
            )
            return response.choices[0].message.content.strip()
        else:
            return "[No OpenAI or OpenRouter API key set. See README.]"
    except ImportError:
        return "[Neither OpenRouter nor OpenAI available. See README.]"

def explain_command(cmd: str) -> str:
    prompt = f"Explain in simple terms what this command does: {cmd}"
    return ask_ai(prompt)

def translate_nl_to_shell(nl: str) -> str:
    prompt = f"Translate this natural language instruction to a Linux shell command, only output the command, nothing else: {nl}"
    return ask_ai(prompt)

def correct_shell_command(cmd: str, error: str) -> str:
    prompt = f"The user tried to run this command: '{cmd}' and got this error: '{error}'. Suggest the correct Linux shell command, only output the command, nothing else."
    return ask_ai(prompt)

def confirm_command(cmd: str, explanation: str) -> str:
    console.print(Panel(Text(cmd, style="bold yellow"), title="[AI Suggestion]"))
    console.print(Text(explanation, style="italic cyan"))
    return Prompt.ask("Run this command?", choices=["Y", "n", "edit"], default="Y")

if __name__ == "__main__":
    main_loop() 