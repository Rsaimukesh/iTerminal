# iTerminal — Smart AI-Powered Linux Terminal

## Overview

iTerminal is a modern Linux terminal emulator designed to make the command-line interface **friendly, accessible, and educational** — especially for beginners. It combines traditional shell functionality with AI-powered natural language understanding, enabling users to enter either standard commands or plain English prompts.

---

## Key Features

- **Hybrid Input System**  
  Accepts both traditional shell commands (e.g., `sudo apt update`) and natural language prompts (e.g., "update my system").

- **AI-Powered Command Interpretation**  
  Uses AI (like GPT-4 or OpenRouter) to translate plain language prompts into safe, executable Linux commands.

- **Error Detection & Interactive Correction**  
  Detects mistyped or failed commands and suggests fixes with user confirmation before execution.

- **Explain Before Execute**  
  Provides plain English explanations of what commands do and potential risks before running them.

- **Real Shell Integration**  
  Runs a real Linux shell underneath to show authentic command output, errors, and behavior.

- **Command History & Interactive Chat**  
  Logs commands, AI prompts, and outputs in a sidebar or chat-style history for easy review and reuse.

- **Safe Mode & User Control**  
  Commands are only run after user confirmation, preventing accidental or harmful actions.

---

## Why iTerminal?

New Linux users often struggle with remembering commands, understanding errors, and safely performing tasks. iTerminal acts as a smart assistant that:

- Translates natural language to working Linux commands  
- Helps correct mistakes interactively  
- Explains commands in simple terms  
- Builds confidence and Linux skills in a safe environment

---

## Future Enhancements (Planned)

- Voice input for hands-free operation  
- Support for multiple package managers and Linux distributions  
- Visual enhancements (graphs, dashboards for command outputs)  
- Plugin architecture for custom extensions  
- Offline AI support using local language models

---

## Project Structure
```
iterminal.py           # Entry point
iterminal/
  __init__.py
  cli.py               # CLI entry point
  core.py              # Main REPL logic
  ai.py                # AI helpers (OpenRouter)
  shell.py             # Shell helpers
  logger.py            # Logging
  config.py            # Config and .env
  dataset.py           # Command/intent memory
  suggest.py           # Advanced user input/completion
  stats.py             # Usage statistics
requirements.txt
README.md
.env                   # (auto-created, holds your API key, gitignored)
.gitignore
```

---

## Setup
1. Clone this repo or copy the files to your machine.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   (Make sure `prompt_toolkit` is included in `requirements.txt` for advanced input features.)
3. **Run iTerminal:**
   ```bash
   python iterminal.py
   ```
   - On first run, you'll be prompted for your OpenRouter API key (get one free at [https://openrouter.ai/](https://openrouter.ai/)).
   - The key is saved to `.env` (which is gitignored for safety).

---

## Usage
- Type a Linux command (e.g., `ls -l`) to run it.
- Type a natural language prompt (e.g., `update my system`) to get an AI-suggested command.
- If you mistype a command, iTerminal will auto-recommend a fix.
- For AI-suggested commands, confirm before running: `[Y/n/edit]`.
- Every command is explained in plain English.
- All activity is logged to a `.log` file in the current directory.

## Navigation Features
- **↑/↓ Arrow Keys**: Navigate through command history
- **Tab Completion**: Auto-complete file paths and commands
- **Ctrl+R**: Search through command history
- **Mouse Support**: Click to position cursor
- **Auto-suggestions**: See command suggestions as you type
- **Smart Completions**: Based on your usage history and learned commands

## Special Commands
- `help` - Show help information
- `history` - Display command history and usage statistics
- `exit` - Exit iTerminal

---

## Troubleshooting

### prompt_toolkit Not Installed
If you see an error like:
```
ModuleNotFoundError: No module named 'prompt_toolkit'
```
Install it with:
```
pip install prompt_toolkit
```

### ImportError: Circular Import
If you see an error like:
```
ImportError: cannot import name 'get_user_input' from partially initialized module 'iterminal.suggest' (most likely due to a circular import)
```
This is due to circular imports between `suggest.py` and `stats.py`. To fix, remove any unnecessary imports between these files, or refactor so that only one depends on the other.

---

## Security
- Your API key is stored in `.env` (never commit this file!).
- `.env` and log files are in `.gitignore` by default.

---

## Example
```
iTerminal > upadte
Error: /bin/sh: 1: upadte: not found
Did you mean: sudo apt update?
[Explanation] This command updates the package list on a Debian-based system.
Run? [Y/n/edit]: Y
...
```

---

## License

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy  
of this software and associated documentation files (the "Software"), to deal  
in the Software without restriction, including without limitation the rights  
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell  
copies of the Software, and to permit persons to whom the Software is  
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all  
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR  
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,  
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE  
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER  
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,  
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE  
SOFTWARE.

---

## Contact

For questions or support, please reach out to [your email or contact info].

## Features
- Accepts user input (command or plain English)
- Runs valid Linux shell commands and shows real output
- Translates natural language to shell commands using AI (OpenRouter, free)
- Detects and corrects mistyped/invalid shell commands, auto-recommends fixes
- Explains every command in plain English
- **Command history navigation** (↑/↓ arrows, Ctrl+R search)
- **File path completion** (Tab key for auto-completion)
- **Smart suggestions** from usage history and learned commands
- Colored output using `rich`
- Logs each session to a local `.log` file
