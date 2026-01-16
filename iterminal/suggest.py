try:
    from prompt_toolkit.completion import Completer, Completion, PathCompleter
    from prompt_toolkit.document import Document
    from prompt_toolkit.shortcuts import prompt
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.auto_suggest import AutoSuggest, Suggestion
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError as e:
    PROMPT_TOOLKIT_AVAILABLE = False
    print(f"Warning: prompt_toolkit import failed: {e}")
    # Create dummy classes for when prompt_toolkit is not available
    class Completer:
        pass
    class Completion:
        pass
    class PathCompleter:
        pass
    class Document:
        pass
    class AutoSuggest:
        pass
    class Suggestion:
        def __init__(self, text):
            self.text = text

from typing import List, Optional, Dict, Any
from .dataset import Dataset
from .stats import UsageStats
from .ai import smart_command_generation, suggest_common_commands_for_context
from rich.prompt import Prompt
import os
import re
from difflib import get_close_matches
import math

# Try to import fuzzywuzzy for better fuzzy matching
try:
    from fuzzywuzzy import fuzz
    from fuzzywuzzy import process
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    # Fallback fuzzy matching function
    def fuzz_partial_ratio(a, b):
        return 100 if a.lower() in b.lower() else 0

# Advanced command templates and patterns
COMMAND_TEMPLATES = {
    # Common shortcuts
    'shortcuts': [
        'i',  # Common shortcut for 'install'
        'l',  # Common shortcut for 'ls'
        's',  # Common shortcut for 'status' or 'search'
        'h',  # Common shortcut for 'history'
        'c',  # Common shortcut for 'clear'
        'u',  # Common shortcut for 'update'
        'q',  # Common shortcut for 'quit'
        'f',  # Common shortcut for 'find'
    ],
    'git': [
        'git status',
        'git add .',
        'git commit -m "message"',
        'git push origin main',
        'git pull origin main',
        'git branch',
        'git checkout -b new-branch',
        'git merge branch-name',
        'git log --oneline',
        'git diff'
    ],
    'system': [
        'sudo apt update',
        'sudo apt upgrade',
        'sudo apt install package-name',
        'sudo systemctl status service-name',
        'sudo systemctl start service-name',
        'sudo systemctl stop service-name',
        'sudo systemctl restart service-name'
    ],
    'file': [
        'ls -la',
        'ls -lh',
        'find . -name "*.py"',
        'grep -r "search-term" .',
        'cat filename',
        'head -n 10 filename',
        'tail -n 10 filename',
        'wc -l filename',
        'du -sh directory',
        'df -h'
    ],
    'process': [
        'ps aux',
        'ps aux | grep process-name',
        'top',
        'htop',
        'kill process-id',
        'killall process-name',
        'pkill process-name',
        'pgrep process-name'
    ],
    'network': [
        'ping google.com',
        'curl -I url',
        'wget url',
        'netstat -tuln',
        'ss -tuln',
        'ifconfig',
        'ip addr',
        'route -n'
    ],
    'python': [
        'python3 script.py',
        'python3 -m pip install package',
        'python3 -m pip list',
        'python3 -m venv venv',
        'source venv/bin/activate',
        'pip freeze > requirements.txt'
    ]
}

class SmartAutoSuggest(AutoSuggest):
    """Enhanced auto-suggest that provides real-time command suggestions with inline ghost-text"""
    
    def __init__(self, dataset: Dataset, stats: UsageStats):
        self.dataset = dataset
        self.stats = stats
        self.suggestion_cache = {}
        self.last_suggestion = None
    
    def get_suggestion(self, buffer, document) -> Optional[Suggestion]:
        text = document.text_before_cursor.strip()
        
        if not text:  # Only skip suggestions for empty input
            return None
        
        # Check cache first
        if text in self.suggestion_cache:
            return self.suggestion_cache[text]
        
        # Get suggestions in priority order
        suggestions = self._get_suggestions(text)
        
        if suggestions:
            # Return the best suggestion for inline display
            best_suggestion = suggestions[0]
            suggestion_text = best_suggestion['command']
            
            # For inline suggestions, we want to show only the remaining part
            # that the user hasn't typed yet
            if text.lower() in suggestion_text.lower():
                # Find where the text matches and show the rest
                idx = suggestion_text.lower().find(text.lower())
                if idx == 0:  # Text is at the beginning
                    remaining = suggestion_text[len(text):]
                    if remaining:
                        suggestion_text = remaining
                else:
                    # Text is in the middle, show the full command
                    suggestion_text = best_suggestion['command']
            else:
                # No direct match, show the full command
                suggestion_text = best_suggestion['command']
            
            suggestion_obj = Suggestion(suggestion_text)
            self.suggestion_cache[text] = suggestion_obj
            self.last_suggestion = best_suggestion
            return suggestion_obj
        
        return None
    
    def _get_suggestions(self, text: str) -> List[Dict[str, Any]]:
        """Get suggestions in priority order with scores"""
        suggestions = []
        
        # 1. Dataset suggestions (highest priority)
        dataset_suggestions = self._get_dataset_suggestions(text)
        suggestions.extend(dataset_suggestions)
        
        # 2. Usage stats suggestions
        stats_suggestions = self._get_stats_suggestions(text)
        suggestions.extend(stats_suggestions)
        
        # 3. Fuzzy matching suggestions
        fuzzy_suggestions = self._get_fuzzy_suggestions(text)
        suggestions.extend(fuzzy_suggestions)
        
        # 4. Context-based suggestions
        context_suggestions = self._get_context_suggestions(text)
        suggestions.extend(context_suggestions)
        
        # 5. AI fallback suggestions (if no good matches)
        if not suggestions or all(s['score'] < 50 for s in suggestions):
            ai_suggestions = self._get_ai_suggestions(text)
            suggestions.extend(ai_suggestions)
        
        # Sort by score and remove duplicates
        unique_suggestions = []
        seen_commands = set()
        
        for suggestion in sorted(suggestions, key=lambda x: x['score'], reverse=True):
            if suggestion['command'] not in seen_commands:
                unique_suggestions.append(suggestion)
                seen_commands.add(suggestion['command'])
        
        return unique_suggestions[:5]  # Return top 5 suggestions
    
    def _get_dataset_suggestions(self, text: str) -> List[Dict[str, Any]]:
        """Get suggestions from learned dataset with fuzzy matching"""
        suggestions = []
        
        if not self.dataset.data:
            return suggestions
        
        # Get all prompts and commands from dataset
        prompts = [(item['prompt'], item['command'], item['explanation']) for item in self.dataset.data]
        
        # Fuzzy match against prompts
        for prompt, command, explanation in prompts:
            # Calculate similarity scores
            if FUZZY_AVAILABLE:
                prompt_score = fuzz.token_set_ratio(text.lower(), prompt.lower())
                command_score = fuzz.token_set_ratio(text.lower(), command.lower())
            else:
                prompt_score = fuzz_partial_ratio(text.lower(), prompt.lower())
                command_score = fuzz_partial_ratio(text.lower(), command.lower())
            
            # Use the higher score
            score = max(prompt_score, command_score)
            
            if score >= 45:  # Threshold for dataset suggestions
                suggestions.append({
                    'command': command,
                    'score': score * 1.1,  # Boost dataset suggestions
                    'source': '📚 Dataset',
                    'explanation': explanation,
                    'prompt': prompt
                })
        
        return suggestions
    
    def _get_stats_suggestions(self, text: str) -> List[Dict[str, Any]]:
        """Get suggestions from usage statistics with improved scoring"""
        suggestions = []
        
        if not hasattr(self.stats, 'usage') or not self.stats.usage:
            return suggestions
        
        # Get commands from stats that match the input
        for command, count in self.stats.usage.items():
            if FUZZY_AVAILABLE:
                match_score = fuzz.token_set_ratio(text.lower(), command.lower())
            else:
                match_score = fuzz_partial_ratio(text.lower(), command.lower())

            if match_score > 50:
                # Score based on usage frequency (logarithmic) and match quality
                usage_score = min(10 * math.log(1 + count), 40)  # Logarithmic score, capped at 40
                
                # Weighted average: 70% match score, 30% usage score
                total_score = (0.7 * match_score) + (0.3 * usage_score)
                
                suggestions.append({
                    'command': command,
                    'score': total_score,
                    'source': '🔥 Stats',
                    'usage_count': count
                })
        
        return suggestions
    
    def _get_fuzzy_suggestions(self, text: str) -> List[Dict[str, Any]]:
        """Get suggestions from a predefined list of commands using fuzzy matching"""
        suggestions = []
        
        # Combine all commands from templates into one list
        all_commands = [cmd for sublist in COMMAND_TEMPLATES.values() for cmd in sublist]
        
        # Special case for single-character commands (shortcut commands)
        if len(text) == 1:
            for cmd in all_commands:
                # For single-character inputs, prioritize commands that start with the character
                # or single-character commands that are exact matches
                if cmd.lower().startswith(text.lower()) or cmd.lower() == text.lower():
                    score = 100  # Perfect match for shortcuts
                    suggestions.append({
                        'command': cmd,
                        'score': score,
                        'source': '🔍 Fuzzy'
                    })
                    
                # Also check for common shortcut expansions
                # For example 'i' could suggest 'install'
                shortcut_expansions = {
                    'i': ['install', 'info', 'init'],
                    'l': ['ls', 'list', 'less'],
                    's': ['status', 'search', 'show'],
                    'c': ['clear', 'cat', 'cd'],
                    'h': ['history', 'help', 'head'],
                    'u': ['update', 'upgrade', 'use'],
                    'f': ['find', 'file', 'fetch'],
                }
                
                if text.lower() in shortcut_expansions:
                    for expansion in shortcut_expansions[text.lower()]:
                        if expansion in cmd.lower():
                            score = 95  # High match for shortcut expansions
                            suggestions.append({
                                'command': cmd,
                                'score': score,
                                'source': '🔍 Fuzzy',
                                'explanation': f'Expanded from "{text}" to "{expansion}"'
                            })
        else:
            # Regular fuzzy matching for longer inputs
            for cmd in all_commands:
                if FUZZY_AVAILABLE:
                    score = fuzz.token_set_ratio(text.lower(), cmd.lower())
                else:
                    score = fuzz_partial_ratio(text.lower(), cmd.lower())
                
                if score >= 60:
                    suggestions.append({
                        'command': cmd,
                        'score': score * 0.9,  # Slightly lower weight for fuzzy
                        'source': '🔍 Fuzzy'
                    })
        
        return suggestions
    
    def _get_context_suggestions(self, text: str) -> List[Dict[str, Any]]:
        """Get context-based suggestions"""
        suggestions = []
        text_lower = text.lower()
        
        # Context-based patterns
        context_patterns = {
            'update': ['sudo apt update', 'sudo apt upgrade', 'git pull'],
            'install': ['sudo apt install', 'pip install', 'npm install'],
            'list': ['ls -la', 'ls -lh', 'find . -type f'],
            'find': ['find . -name', 'grep -r', 'locate'],
            'status': ['git status', 'systemctl status', 'ps aux'],
            'start': ['sudo systemctl start', 'python3 script.py'],
            'stop': ['sudo systemctl stop', 'pkill', 'kill'],
            'restart': ['sudo systemctl restart', 'sudo reboot'],
            'search': ['grep -r', 'find . -name', 'locate'],
            'backup': ['cp -r', 'tar -czf', 'rsync -av'],
            'clean': ['sudo apt autoremove', 'sudo apt autoclean'],
            'monitor': ['top', 'htop', 'iotop', 'nethogs']
        }
        
        for pattern, commands in context_patterns.items():
            if pattern in text_lower or (FUZZY_AVAILABLE and fuzz.token_set_ratio(text_lower, pattern) > 70):
                for cmd in commands:
                    if FUZZY_AVAILABLE:
                        score = fuzz.token_set_ratio(text_lower, cmd.lower())
                    else:
                        score = fuzz_partial_ratio(text_lower, cmd.lower())
                    if score >= 40:
                        suggestions.append({
                            'command': cmd,
                            'score': score * 0.95, #Slightly lower weight for context
                            'source': '💡 Context'
                        })
        
        return suggestions
    
    def _get_ai_suggestions(self, text: str) -> List[Dict[str, Any]]:
        """Get AI-powered suggestions as fallback"""
        suggestions = []
        
        try:
            # Use the smart command generation
            result = smart_command_generation(text)
            if result and result.get('command') and not result['command'].startswith('[AI error'):
                suggestions.append({
                    'command': result['command'],
                    'score': 35,  # Lower score for AI suggestions
                    'source': '🤖 AI',
                    'explanation': result.get('explanation', '')
                })
            
            # Get context-based suggestions from AI
            context_suggestions = suggest_common_commands_for_context(text)
            for i, suggestion in enumerate(context_suggestions[:3]):
                suggestions.append({
                    'command': suggestion,
                    'score': 30 - i * 5,  # Decreasing scores
                    'source': '🤖 AI'
                })
                
        except Exception:
            # If AI fails, return empty list
            pass
        
        return suggestions

class CommandCompleter(Completer):
    def __init__(self, dataset: Dataset, stats: UsageStats):
        self.dataset = dataset
        self.stats = stats
        self.auto_suggest = SmartAutoSuggest(dataset, stats)
        if PROMPT_TOOLKIT_AVAILABLE:
            self.path_completer = PathCompleter()
        else:
            self.path_completer = None

    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor.strip()
        
        # Don't suggest if text is empty
        if not text:
            return
            
        # First, try path completion (for file/directory paths)
        if self.path_completer and ('/' in text or text.startswith('./') or text.startswith('../')):
            yield from self.path_completer.get_completions(document, complete_event)
            return
        
        # Get suggestions from auto-suggest system
        suggestions = self.auto_suggest._get_suggestions(text)
        
        for suggestion in suggestions:
            # Create display text with source indicator
            source_icons = {
                '📚 Dataset': '📚',
                '🔥 Stats': '🔥',
                '🔍 Fuzzy': '🔍',
                '💡 Context': '💡',
                '🤖 AI': '🤖'
            }
            
            icon = source_icons.get(suggestion['source'], '🔧')
            command = suggestion['command']
            score = suggestion['score']
            
            # Only show explanation if the suggestion is not an exact match
            show_explanation = False
            if 'explanation' in suggestion:
                # If the user input exactly matches the command, don't show explanation
                if text.strip() != command.strip():
                    show_explanation = True
            
            if show_explanation:
                display_text = f"{icon} {command} ({suggestion['explanation'][:40]}...) [{int(score)}]"
            elif 'usage_count' in suggestion:
                display_text = f"{icon} {command} (used {suggestion['usage_count']} times) [{int(score)}]"
            else:
                display_text = f"{icon} {command} [{int(score)}]"
            
            yield Completion(
                command,
                start_position=-len(text),
                display=display_text
            )
        
        # Fallback to old suggestions if no smart suggestions
        if not suggestions:
            # Suggest from dataset (fuzzy match)
            dataset_suggestion = self.dataset.search(text)
            if dataset_suggestion:
                # Only show explanation if not an exact match
                if text.strip() != dataset_suggestion['command'].strip():
                    display = f"📚 {dataset_suggestion['command']} ({dataset_suggestion['explanation'][:50]}...)"
                else:
                    display = f"📚 {dataset_suggestion['command']}"
                yield Completion(
                    dataset_suggestion['command'], 
                    start_position=-len(text), 
                    display=display
                )
            
            # Suggest from usage stats (prefix match)
            for cmd in self.stats.suggest(text):
                if cmd != text:  # Don't suggest the same text
                    yield Completion(
                        cmd, 
                        start_position=-len(text), 
                        display=f"🔥 {cmd} (used {self.stats.usage.get(cmd, 0)} times)"
                    )
            
            # Advanced template suggestions based on context
            suggestions = self.get_contextual_suggestions(text)
            for suggestion in suggestions:
                yield Completion(
                    suggestion,
                    start_position=-len(text),
                    display=f"💡 {suggestion}"
                )
            
            # Suggest common commands that start with the text
            common_commands = [
                'ls', 'cd', 'pwd', 'cat', 'echo', 'grep', 'find', 'chmod', 'chown',
                'cp', 'mv', 'rm', 'mkdir', 'rmdir', 'touch', 'nano', 'vim', 'git',
                'python', 'pip', 'sudo', 'apt', 'systemctl', 'ps', 'top', 'kill'
            ]
            
            for cmd in common_commands:
                if cmd.startswith(text.lower()) and cmd != text:
                    yield Completion(
                        cmd,
                        start_position=-len(text),
                        display=f"🔧 {cmd}"
                    )

def get_user_input(dataset: Dataset, stats: UsageStats, prompt_text: str = 'iTerminal > '):
    """Enhanced user input with real-time inline suggestions"""
    import sys
    
    # Check if we're in a proper terminal
    if not sys.stdin.isatty() or not PROMPT_TOOLKIT_AVAILABLE:
        # Fallback to simple rich prompt
        return Prompt.ask(prompt_text)
    
    # Create history file in user's home directory
    history_file = os.path.expanduser('~/.iterminal_history')
    
    # Ensure the history file exists and is writable
    try:
        if not os.path.exists(history_file):
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            with open(history_file, 'w') as f:
                pass  # Create empty file
        
        if not os.access(history_file, os.W_OK):
            os.chmod(history_file, 0o600)  # Read/write for owner only
    except Exception:
        # If we can't set up the history file, we'll continue without it
        pass
    
    # Create key bindings for custom behavior
    kb = KeyBindings()
    
    # Note: We don't override up/down as they work by default with history
    # prompt_toolkit handles them automatically when history is provided
    
    @kb.add('tab')
    def _(event):
        """Accept current suggestion with Tab"""
        buffer = event.app.current_buffer
        if buffer.suggestion:
            # Insert the suggestion text
            buffer.insert_text(buffer.suggestion.text)
        else:
            # If no suggestion, cycle through completions
            buffer.complete_next()
    
    @kb.add('s-tab')
    def _(event):
        """Handle shift+tab for reverse completion"""
        event.app.current_buffer.complete_previous()
    
    @kb.add('c-space')
    def _(event):
        """Show all available suggestions"""
        buffer = event.app.current_buffer
        buffer.complete_next()
    
    # Create enhanced completer and auto-suggest
    completer = CommandCompleter(dataset, stats)
    auto_suggest = SmartAutoSuggest(dataset, stats)
    
    try:
        # Try to create FileHistory with the history file
        try:
            history = FileHistory(history_file)
        except Exception:
            # If FileHistory fails, use in-memory history
            from prompt_toolkit.history import InMemoryHistory
            history = InMemoryHistory()
            
        # Use prompt_toolkit with enhanced features for inline suggestions
        result = prompt(
            prompt_text,
            completer=completer,
            auto_suggest=auto_suggest,
            complete_while_typing=True,  # Enable auto-complete while typing
            history=history,
            key_bindings=kb,
            complete_in_thread=True,  # Enable threading for better performance
            mouse_support=True,       # Mouse support
            enable_history_search=True,  # Ctrl+R for history search
            # Enhanced styling for inline suggestions
            style=None,  # Use default style for better ghost-text visibility
            # Ensure proper input handling
            input_processors=None,
            # vi_mode=False ensures emacs mode with proper up/down arrow support
            vi_mode=False,
            # Show completion menu automatically
            complete_style='MULTI_COLUMN',
        )
        return result.strip()  # Ensure clean input
    except Exception as e:
        # Fallback to simple rich prompt if prompt_toolkit fails
        return Prompt.ask(prompt_text)

# Legacy functions for backward compatibility
def get_contextual_suggestions(text: str) -> List[str]:
    """Get contextual suggestions based on what user is typing"""
    suggestions = []
    text_lower = text.lower()
    
    # Git-related suggestions
    if 'git' in text_lower or text_lower.startswith('g'):
        for template in COMMAND_TEMPLATES['git']:
            if template.startswith(text) or text in template:
                suggestions.append(template)
    
    # System management suggestions
    if any(word in text_lower for word in ['update', 'upgrade', 'install', 'system', 'service']):
        for template in COMMAND_TEMPLATES['system']:
            if template.startswith(text) or text in template:
                suggestions.append(template)
    
    # File operations suggestions
    if any(word in text_lower for word in ['file', 'list', 'find', 'search', 'read']):
        for template in COMMAND_TEMPLATES['file']:
            if template.startswith(text) or text in template:
                suggestions.append(template)
    
    # Process management suggestions
    if any(word in text_lower for word in ['process', 'kill', 'top', 'ps', 'running']):
        for template in COMMAND_TEMPLATES['process']:
            if template.startswith(text) or text in template:
                suggestions.append(template)
    
    # Network suggestions
    if any(word in text_lower for word in ['ping', 'curl', 'wget', 'network', 'url']):
        for template in COMMAND_TEMPLATES['network']:
            if template.startswith(text) or text in template:
                suggestions.append(template)
    
    # Python suggestions
    if any(word in text_lower for word in ['python', 'pip', 'venv', 'script']):
        for template in COMMAND_TEMPLATES['python']:
            if template.startswith(text) or text in template:
                suggestions.append(template)
    
    return suggestions[:5]  # Limit to 5 suggestions

def get_natural_language_suggestions(text: str) -> List[str]:
    """Get command suggestions based on natural language patterns"""
    suggestions = []
    text_lower = text.lower()
    
    # Common natural language patterns
    patterns = {
        'show me': ['ls -la', 'ps aux', 'df -h', 'free -h'],
        'list': ['ls -la', 'ls -lh', 'find . -type f'],
        'find': ['find . -name "*.py"', 'grep -r "term" .', 'locate filename'],
        'update': ['sudo apt update', 'git pull origin main', 'pip install --upgrade package'],
        'install': ['sudo apt install package', 'pip install package', 'npm install package'],
        'check': ['git status', 'systemctl status service', 'ps aux | grep process'],
        'start': ['sudo systemctl start service', 'python3 script.py', 'npm start'],
        'stop': ['sudo systemctl stop service', 'pkill process', 'kill process-id'],
        'restart': ['sudo systemctl restart service', 'sudo reboot', 'sudo shutdown -r now'],
        'backup': ['cp -r source destination', 'tar -czf backup.tar.gz directory', 'rsync -av source destination'],
        'search': ['grep -r "term" .', 'find . -name "*.py"', 'locate filename'],
        'monitor': ['top', 'htop', 'iotop', 'nethogs'],
        'clean': ['sudo apt autoremove', 'sudo apt autoclean', 'rm -rf temp/*'],
        'compress': ['tar -czf archive.tar.gz directory', 'zip -r archive.zip directory', 'gzip filename'],
        'extract': ['tar -xzf archive.tar.gz', 'unzip archive.zip', 'gunzip filename.gz']
    }
    
    for pattern, commands in patterns.items():
        if pattern in text_lower:
            for cmd in commands:
                if cmd not in suggestions:
                    suggestions.append(cmd)
    
    return suggestions 