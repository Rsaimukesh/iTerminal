try:
    from prompt_toolkit.completion import Completer, Completion, PathCompleter
    from prompt_toolkit.document import Document
    from prompt_toolkit.shortcuts import prompt
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.key_bindings import KeyBindings
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False

from typing import List
from .dataset import Dataset
from .stats import UsageStats
from rich.prompt import Prompt
import os

class CommandCompleter(Completer):
    def __init__(self, dataset: Dataset, stats: UsageStats):
        self.dataset = dataset
        self.stats = stats
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
            
        # Suggest from dataset (fuzzy match)
        dataset_suggestion = self.dataset.search(text)
        if dataset_suggestion:
            yield Completion(
                dataset_suggestion['command'], 
                start_position=-len(text), 
                display=f"📚 {dataset_suggestion['command']} ({dataset_suggestion['explanation'][:50]}...)"
            )
        
        # Suggest from usage stats (prefix match)
        for cmd in self.stats.suggest(text):
            if cmd != text:  # Don't suggest the same text
                yield Completion(
                    cmd, 
                    start_position=-len(text), 
                    display=f"🔥 {cmd} (used {self.stats.usage.get(cmd, 0)} times)"
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
                    display=f"💡 {cmd}"
                )

def get_user_input(dataset: Dataset, stats: UsageStats, prompt_text: str = 'iTerminal > '):
    if not PROMPT_TOOLKIT_AVAILABLE:
        # Fallback to simple rich prompt
        return Prompt.ask(prompt_text)
    
    # Create history file in user's home directory
    history_file = os.path.expanduser('~/.iterminal_history')
    
    # Create key bindings for custom behavior
    kb = KeyBindings()
    
    @kb.add('up')
    def _(event):
        """Navigate up in history"""
        event.app.current_buffer.auto_up()
    
    @kb.add('down')
    def _(event):
        """Navigate down in history"""
        event.app.current_buffer.auto_down()
    
    @kb.add('tab')
    def _(event):
        """Handle tab completion"""
        event.app.current_buffer.complete_next()
    
    @kb.add('s-tab')
    def _(event):
        """Handle shift+tab for reverse completion"""
        event.app.current_buffer.complete_previous()
    
    completer = CommandCompleter(dataset, stats)
    
    try:
        # Use prompt_toolkit with history and auto-suggestions
        result = prompt(
            prompt_text,
            completer=completer,
            complete_while_typing=True,
            history=FileHistory(history_file),
            auto_suggest=AutoSuggestFromHistory(),
            key_bindings=kb,
            complete_in_thread=True,  # Better performance
            mouse_support=True,       # Mouse support
            enable_history_search=True,  # Ctrl+R for history search
        )
        return result
    except Exception as e:
        # Fallback to simple rich prompt if prompt_toolkit fails
        return Prompt.ask(prompt_text) 