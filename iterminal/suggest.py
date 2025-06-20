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
        # Suggest from dataset
        dataset_suggestion = self.dataset.search(text)
        if dataset_suggestion:
            yield Completion(dataset_suggestion['command'], start_position=-len(text), display=dataset_suggestion['command'])
        # Suggest from usage stats
        for cmd in self.stats.suggest(text):
            yield Completion(cmd, start_position=-len(text), display=cmd)

def get_user_input(dataset: Dataset, stats: UsageStats, prompt_text: str = 'iTerminal > '):
    return Prompt.ask(prompt_text) 