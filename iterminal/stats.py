import os
import json
from typing import Dict, List

USAGE_PATH = os.path.expanduser('~/.iterminal_usage.json')

class UsageStats:
    def __init__(self, path: str = USAGE_PATH):
        self.path = path
        self.usage = self.load()

    def load(self) -> Dict[str, int]:
        if not os.path.exists(self.path):
            return {}
        with open(self.path, 'r') as f:
            try:
                return json.load(f)
            except Exception:
                return {}

    def save(self):
        with open(self.path, 'w') as f:
            json.dump(self.usage, f, indent=2)

    def add(self, command: str):
        if command in self.usage:
            self.usage[command] += 1
        else:
            self.usage[command] = 1
        self.save()

    def suggest(self, prefix: str, n: int = 3) -> List[str]:
        # Suggest most frequent commands starting with prefix
        filtered = {cmd: count for cmd, count in self.usage.items() if cmd.startswith(prefix)}
        sorted_cmds = sorted(filtered, key=filtered.get, reverse=True)
        return sorted_cmds[:n] 