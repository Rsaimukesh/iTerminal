# iTerminal — Smart AI-Powered Linux Terminal

## Overview

iTerminal is a modern Linux terminal emulator designed to make the command-line interface **friendly, accessible, and educational** — especially for beginners. It combines traditional shell functionality with AI-powered natural language understanding, enabling users to enter either standard commands or plain English prompts.

**NEW: Enhanced Smart Command Generation** - iTerminal now intelligently handles wrong, unclear, or ambiguous prompts by generating multiple command interpretations and providing helpful suggestions.

**NEW: Real-time Command Suggestions** - iTerminal now provides intelligent, real-time command suggestions as you type, with fuzzy matching and AI fallback.

---

## Key Features

- **Hybrid Input System**  
  Accepts both traditional shell commands (e.g., `sudo apt update`) and natural language prompts (e.g., "update my system").

- **AI-Powered Command Interpretation**  
  Uses AI (like GPT-4 or OpenRouter) to translate plain language prompts into safe, executable Linux commands.

- **Smart Error Handling & Command Generation**  
  **NEW**: Automatically detects unclear prompts and generates multiple command interpretations. Handles typos, ambiguous requests, and provides context-based suggestions.

- **Real-time Command Suggestions**  
  **NEW**: Intelligent suggestions appear as you type, with fuzzy matching for typos and partial input. Supports TAB completion and right-arrow acceptance.

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

## Real-time Command Suggestions

iTerminal now provides intelligent, real-time command suggestions that appear as you type:

### Smart Suggestion Sources
- **📚 Dataset Suggestions**: From previously learned commands in `~/.iterminal_dataset.json`
- **🔥 Usage-based Suggestions**: Based on your command history and frequency
- **🔍 Fuzzy Matching**: Handles typos and partial input (e.g., "upda" → "sudo apt update")
- **💡 Context-based Suggestions**: Based on keywords and common patterns
- **🤖 AI Fallback**: When no good matches found, AI generates suggestions

### How to Use
- **Type naturally**: Start typing and see suggestions appear
- **TAB completion**: Press Tab to cycle through suggestions
- **Right arrow**: Press → to accept the current suggestion
- **Shift+Tab**: Reverse cycle through suggestions
- **Real-time display**: Suggestions update as you type

### Examples
```
Input: "upda" → Suggestion: "sudo apt update && sudo apt upgrade"
Input: "show" → Suggestion: "ps aux" (show processes)
Input: "find" → Suggestion: "find . -name '*.py'" (find Python files)
Input: "instal" → Suggestion: "sudo apt install package-name" (typo correction)
```

### Keyboard Shortcuts
- **Tab**: Cycle through completions
- **Shift+Tab**: Reverse cycle through completions  
- **→ (Right arrow)**: Accept current suggestion
- **↑/↓**: Navigate command history
- **Ctrl+R**: Search command history

---

## Inline Command Suggestions

iTerminal now features **ghost-text style inline suggestions** that appear as you type:

### How Inline Suggestions Work
- **Ghost-text display**: Suggestions appear as faint text after your cursor
- **Partial completion**: Shows only the remaining part you haven't typed yet
- **Smart matching**: Intelligently matches your input to commands

### Examples of Inline Suggestions
```
You type: "upda"     → Ghost-text: "te system"
You type: "check"    → Ghost-text: " memory" or " disk"
You type: "git"      → Ghost-text: " status"
You type: "list"     → Ghost-text: " files"
You type: "find"     → Ghost-text: " python"
```

### Accepting Inline Suggestions
- **Tab**: Accept the current inline suggestion
- **→ (Right arrow)**: Accept the current inline suggestion
- **Ctrl+Space**: Show all available completions
- **Shift+Tab**: Cycle through completions in reverse

### Suggestion Sources (with icons)
- **📚 Dataset**: From your learned commands in `~/.iterminal_dataset.json`
- **🔥 Stats**: From your command history and usage frequency
- **🔍 Fuzzy**: Fuzzy matching for typos and partial input
- **💡 Context**: Context-based suggestions based on keywords
- **🤖 AI**: AI-generated suggestions when no good matches found

### Testing Inline Suggestions
Run the test script to see inline suggestions in action:
```bash
python3 test_inline_suggestions.py
```

This will demonstrate:
- Ghost-text suggestions as you type
- Smart partial text completion
- Multiple suggestion sources
- Tab and arrow key acceptance

---

## Enhanced Smart Command Generation

iTerminal now includes advanced AI-powered features to handle unclear or incorrect prompts:

### Automatic Typo Correction
- Detects and corrects common typos in natural language
- Examples: "upadte systm" → "update system" → `sudo apt update && sudo apt upgrade`

### Multiple Interpretation Attempts
- When a prompt is unclear, generates 3-4 possible command interpretations
- Provides confidence scores for each interpretation
- Allows users to choose the most appropriate command

### Context-Based Suggestions
- Analyzes keywords in unclear prompts to suggest relevant commands
- Provides alternative commands based on common Linux tasks
- Groups suggestions by category (file operations, system management, etc.)

### Interactive Prompt Fixing
- Use the `fix` command to get help with unclear prompts
- Interactive selection of alternative commands
- Step-by-step guidance for complex requests

### Examples of Smart Handling

| Unclear Input | Smart Interpretation | Generated Command |
|---------------|---------------------|-------------------|
| "upadte systm" | Typo correction | `sudo apt update && sudo apt upgrade` |
| "show me stuff" | Context analysis | `ls -la` |
| "fix computer" | Multiple options | `sudo systemctl status` + alternatives |
| "do the thing" | Best guess | `ls -la` (most common action) |
| "kill process" | Context-based | `ps aux \| grep process` |

---

## Why iTerminal?

New Linux users often struggle with remembering commands, understanding errors, and safely performing tasks. iTerminal acts as a smart assistant that:

- Translates natural language to working Linux commands  
- **NEW**: Handles unclear or wrong prompts intelligently
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
  core.py              # Main REPL logic (enhanced)
  ai.py                # AI helpers (enhanced with smart generation)
  shell.py             # Shell helpers
  logger.py            # Logging
  config.py            # Config and .env
  dataset.py           # Command/intent memory
  suggest.py           # Advanced user input/completion
  stats.py             # Usage statistics
test_smart_commands.py # Test script for new functionality
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
- **NEW**: Type unclear prompts (e.g., `upadte systm`, `show me stuff`) and get smart interpretations.
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
- `fix` - **NEW**: Fix unclear or wrong prompts interactively
- `exit` - Exit iTerminal

---

## Testing the New Features

### Test Smart Command Generation
Run the test script to see the smart command generation in action:

```bash
python test_smart_commands.py
```

This will demonstrate:
- Typo correction
- Multiple interpretation attempts
- Context-based suggestions
- Ambiguous prompt handling

### Test Real-time Command Suggestions
Run the suggestions test script to see the new real-time suggestion system:

```bash
python test_suggestions.py
```

This will demonstrate:
- Real-time command suggestions as you type
- Fuzzy matching for typos and partial input
- Dataset-based suggestions from learned commands
- Usage-based suggestions from command history
- AI fallback suggestions
- Tab completion and right-arrow acceptance

### Interactive Testing
1. Start iTerminal: `python iterminal.py`
2. Try typing partial commands and watch suggestions appear:
   - Type "upda" and see "sudo apt update && sudo apt upgrade" suggested
   - Type "show" and see "ps aux" suggested
   - Type "find" and see "find . -name '*.py'" suggested
3. Use Tab to cycle through suggestions
4. Use → (right arrow) to accept suggestions
5. Try natural language: "update system", "show processes", etc.

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
I'm not sure what you mean by 'upadte'. Let me try to help...
I think you meant: Corrected 'upadte' to 'update'
┌─ AI Suggestion ──────────────────────────────────────┐
│ sudo apt update && sudo apt upgrade                  │
└──────────────────────────────────────────────────────┘
This command updates the package list and upgrades installed packages on a Debian-based system.

Alternative interpretations:
  1. sudo apt update
  2. sudo apt upgrade

Related commands you might want:
  1. sudo apt update
  2. sudo apt upgrade
  3. sudo apt update && sudo apt upgrade

Run the suggested command? [Y/n/edit/alternatives/suggestions/help]: Y
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
- **NEW**: Smart handling of unclear or wrong prompts with multiple interpretations
- **NEW**: Automatic typo correction and context-based suggestions
- Explains every command in plain English
- **Command history navigation** (↑/↓ arrows, Ctrl+R search)
- **File path completion** (Tab key for auto-completion)
- **Smart suggestions** from usage history and learned commands
- Colored output using `rich`
- Logs each session to a local `.log` file
