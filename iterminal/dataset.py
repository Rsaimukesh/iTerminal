import os
import json
from typing import List, Dict, Optional
from difflib import get_close_matches

DATASET_PATH = os.path.expanduser('~/.iterminal_dataset.json')

class Dataset:
    def __init__(self, path: str = DATASET_PATH):
        self.path = path
        self.data = self.load()

    def load(self) -> List[Dict]:
        if not os.path.exists(self.path):
            return []
        with open(self.path, 'r') as f:
            try:
                return json.load(f)
            except Exception:
                return []

    def save(self):
        with open(self.path, 'w') as f:
            json.dump(self.data, f, indent=2)

    def add(self, prompt: str, command: str, explanation: str):
        entry = {"prompt": prompt, "command": command, "explanation": explanation}
        self.data.append(entry)
        self.save()

    def search(self, prompt: str, cutoff: float = 0.7) -> Optional[Dict]:
        """
        Search for a matching prompt in the dataset with improved matching.
        First tries exact matches, then fuzzy matching with difflib.
        
        Args:
            prompt: The prompt to search for
            cutoff: The minimum similarity score to consider a match (0.0-1.0)
            
        Returns:
            Dict or None: The matching dataset entry or None if no match found
        """
        # First try exact match (case insensitive)
        for item in self.data:
            if item['prompt'].lower() == prompt.lower():
                return item
        
        # Then try fuzzy matching
        prompts = [item['prompt'] for item in self.data]
        matches = get_close_matches(prompt, prompts, n=1, cutoff=cutoff)
        if matches:
            for item in self.data:
                if item['prompt'] == matches[0]:
                    return item
        
        return None 