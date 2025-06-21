from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.shortcuts import prompt
from typing import List
from .dataset import Dataset
from .stats import UsageStats
from rich.prompt import Prompt

class CommandCompleter(Completer):
    def __init__(self, dataset: Dataset, stats: UsageStats):
        self.dataset = dataset
        self.stats = stats

    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor.strip()
        
        # Don't suggest if text is empty
        if not text:
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

def get_user_input(dataset: Dataset, stats: UsageStats, prompt_text: str = 'iTerminal > '):
    completer = CommandCompleter(dataset, stats)
    return prompt(prompt_text, completer=completer, complete_while_typing=True) 