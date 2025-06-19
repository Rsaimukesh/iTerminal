# iTerminal

A smart Linux terminal for beginners. Behaves like a normal shell but with minimal AI help for error correction and natural language prompts.

## Features
- Accepts user input (command or plain English)
- Runs valid Linux shell commands and shows real output
- Translates natural language to shell commands using AI (OpenRouter, free)
- Detects and corrects mistyped/invalid shell commands, auto-recommends fixes
- Explains every command in plain English
- Colored output using `rich`
- Logs each session to a local `.log` file

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
requirements.txt
README.md
.env                   # (auto-created, holds your API key, gitignored)
.gitignore
```

## Setup
1. Clone this repo or copy the files to your machine.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run iTerminal:**
   ```bash
   python iterminal.py
   ```
   - On first run, you'll be prompted for your OpenRouter API key (get one free at [https://openrouter.ai/](https://openrouter.ai/)).
   - The key is saved to `.env` (which is gitignored for safety).

## Usage
- Type a Linux command (e.g., `ls -l`) to run it.
- Type a natural language prompt (e.g., `update my system`) to get an AI-suggested command.
- If you mistype a command, iTerminal will auto-recommend a fix.
- For AI-suggested commands, confirm before running: `[Y/n/edit]`.
- Every command is explained in plain English.
- All activity is logged to a `.log` file in the current directory.

## Security
- Your API key is stored in `.env` (never commit this file!).
- `.env` and log files are in `.gitignore` by default.

## Example
```
iTerminal > upadte
Error: /bin/sh: 1: upadte: not found
Did you mean: sudo apt update?
[Explanation] This command updates the package list on a Debian-based system.
Run? [Y/n/edit]: Y
...
```

## Notes
- No GUI, plugin system, or voice input (yet).
- Only works online (OpenRouter or OpenAI required for AI features).
- Works on most Linux distributions.

---
MIT License 