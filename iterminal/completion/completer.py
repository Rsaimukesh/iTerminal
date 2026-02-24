"""Advanced tab completion and autocomplete system with fuzzy matching."""
import os
import re
import logging
from typing import List, Dict, Tuple, Optional, Callable
from dataclasses import dataclass
from pathlib import Path
from difflib import SequenceMatcher
import subprocess
from collections import defaultdict
from functools import lru_cache


logger = logging.getLogger(__name__)


@dataclass
class Completion:
    """Represents a single completion suggestion."""
    text: str
    description: str = ""
    priority: int = 0  # Higher = better
    type: str = "command"  # command, file, parameter, etc.
    
    def __lt__(self, other):
        """Sort by priority (descending)."""
        if self.priority != other.priority:
            return self.priority > other.priority
        return self.text < other.text


class FuzzyMatcher:
    """Fuzzy string matching for autocomplete."""
    
    @staticmethod
    def match(pattern: str, text: str, ignore_case: bool = True) -> float:
        """
        Calculate fuzzy match score between pattern and text.
        Returns score between 0.0 (no match) and 1.0 (perfect match).
        """
        if ignore_case:
            pattern = pattern.lower()
            text = text.lower()
        
        if pattern == text:
            return 1.0
        
        if pattern in text:
            # Substring match - bonus score
            return 0.9
        
        # Check if all pattern characters are in text in order
        pattern_idx = 0
        text_idx = 0
        while pattern_idx < len(pattern) and text_idx < len(text):
            if pattern[pattern_idx] == text[text_idx]:
                pattern_idx += 1
            text_idx += 1
        
        if pattern_idx == len(pattern):
            # All characters matched in order
            return 0.6 + (0.3 * (pattern_idx / len(text)))
        
        # Use SequenceMatcher as fallback
        return SequenceMatcher(None, pattern, text).ratio() * 0.5
    
    @staticmethod
    def filter_matches(
        pattern: str,
        candidates: List[str],
        threshold: float = 0.3,
        ignore_case: bool = True
    ) -> List[Tuple[str, float]]:
        """Filter candidates by fuzzy match score."""
        matches = []
        for candidate in candidates:
            score = FuzzyMatcher.match(pattern, candidate, ignore_case)
            if score >= threshold:
                matches.append((candidate, score))
        
        return sorted(matches, key=lambda x: x[1], reverse=True)


class FileCompleter:
    """File and path completion."""
    
    def __init__(self):
        self.cache: Dict[str, List[str]] = {}
    
    def get_completions(self, partial_path: str, max_results: int = 10) -> List[Completion]:
        """Get file/directory completions for partial path."""
        try:
            # Expand ~ to home directory
            if partial_path.startswith("~"):
                partial_path = os.path.expanduser(partial_path)
            
            # Get directory and prefix
            if os.path.isdir(partial_path):
                directory = partial_path
                prefix = ""
            else:
                directory = os.path.dirname(partial_path) or "."
                prefix = os.path.basename(partial_path)
            
            if not os.path.isdir(directory):
                return []
            
            # Get cached directory listing or list files
            cache_key = directory
            if cache_key not in self.cache:
                try:
                    self.cache[cache_key] = os.listdir(directory)
                except PermissionError:
                    return []
            
            files = self.cache[cache_key]
            
            # Filter by prefix
            matches = [f for f in files if f.startswith(prefix)]
            
            # Build completions
            completions = []
            for filename in matches[:max_results]:
                full_path = os.path.join(directory, filename)
                is_dir = os.path.isdir(full_path)
                
                completions.append(Completion(
                    text=filename + ("/" if is_dir else ""),
                    description="Directory" if is_dir else "File",
                    type="directory" if is_dir else "file",
                    priority=10 if is_dir else 5
                ))
            
            return sorted(completions)
        
        except Exception as e:
            logger.debug(f"Error in file completion: {e}")
            return []
    
    def clear_cache(self):
        """Clear directory cache."""
        self.cache.clear()


class CommandCompleter:
    """Shell command completion."""
    
    def __init__(self):
        self.command_cache: Optional[List[str]] = None
        self.parameter_cache: Dict[str, List[str]] = {}
    
    def get_command_completions(
        self,
        partial_cmd: str,
        max_results: int = 10
    ) -> List[Completion]:
        """Get shell command completions."""
        try:
            # Use bash-completion if available
            if self.command_cache is None:
                self._build_command_cache()
            
            # Fuzzy match against cached commands
            matches = FuzzyMatcher.filter_matches(
                partial_cmd,
                self.command_cache or [],
                threshold=0.3
            )
            
            completions = []
            for cmd, score in matches[:max_results]:
                completions.append(Completion(
                    text=cmd,
                    description="Command",
                    type="command",
                    priority=int(score * 10)
                ))
            
            return sorted(completions)
        
        except Exception as e:
            logger.debug(f"Error in command completion: {e}")
            return []
    
    def _build_command_cache(self):
        """Build cache of available commands."""
        try:
            # Use compgen to get available commands
            result = subprocess.run(
                ["bash", "-ic", "compgen -c"],
                capture_output=True,
                text=True,
                timeout=5
            )
            self.command_cache = sorted(set(result.stdout.strip().split("\n")))
        except Exception as e:
            logger.debug(f"Failed to build command cache: {e}")
            self.command_cache = []
    
    def get_git_completions(self, partial: str, max_results: int = 10) -> List[Completion]:
        """Get git command and subcommand completions."""
        git_commands = [
            "add", "branch", "checkout", "commit", "config", "diff",
            "fetch", "init", "log", "merge", "pull", "push", "rebase",
            "reset", "revert", "rm", "stash", "status", "tag",
        ]
        
        matches = FuzzyMatcher.filter_matches(partial, git_commands, threshold=0.3)
        
        return [
            Completion(
                text=cmd,
                description="Git subcommand",
                type="git_command",
                priority=int(score * 10)
            )
            for cmd, score in matches[:max_results]
        ]


class HistoryCompleter:
    """Completion based on command history."""
    
    def __init__(self, max_history: int = 1000):
        self.history: List[str] = []
        self.max_history = max_history
        self.frequency: Dict[str, int] = defaultdict(int)
    
    def add_to_history(self, command: str) -> None:
        """Add command to history."""
        self.history.append(command)
        self.frequency[command] += 1
        
        # Keep history size limited
        if len(self.history) > self.max_history:
            old_cmd = self.history.pop(0)
            self.frequency[old_cmd] -= 1
            if self.frequency[old_cmd] == 0:
                del self.frequency[old_cmd]
    
    def get_history_completions(
        self,
        partial: str,
        max_results: int = 10
    ) -> List[Completion]:
        """Get completions from history with frequency scoring."""
        # Get unique commands from history
        unique_commands = list(set(self.history))
        
        # Fuzzy match
        matches = FuzzyMatcher.filter_matches(
            partial,
            unique_commands,
            threshold=0.3
        )
        
        # Combine fuzzy score with frequency
        completions = []
        for cmd, fuzzy_score in matches[:max_results]:
            frequency_weight = min(self.frequency[cmd] / 10.0, 1.0)
            combined_priority = int((fuzzy_score + frequency_weight) * 5)
            
            completions.append(Completion(
                text=cmd,
                description=f"History ({self.frequency[cmd]} times)",
                type="history",
                priority=combined_priority
            ))
        
        return sorted(completions)


class AutoCompleter:
    """Main autocomplete engine combining multiple sources."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.file_completer = FileCompleter()
        self.command_completer = CommandCompleter()
        self.history_completer = HistoryCompleter()
        
        self.enabled = self.config.get("enabled", True)
        self.fuzzy_matching = self.config.get("fuzzy_matching", True)
        self.history_based = self.config.get("history_based", True)
        self.max_suggestions = self.config.get("max_suggestions", 10)
        self.ignore_case = self.config.get("ignore_case", True)
    
    def get_completions(self, text: str, context: Optional[Dict] = None) -> List[Completion]:
        """Get completions for given input text."""
        if not self.enabled:
            return []
        
        context = context or {}
        completions: List[Completion] = []
        
        # Determine what type of completion is needed
        if text.startswith("~") or "/" in text or text.startswith("."):
            # File/path completion
            completions.extend(self.file_completer.get_completions(
                text,
                max_results=self.max_suggestions
            ))
        
        elif text.startswith("git "):
            # Git command completion
            partial = text[4:].strip()
            completions.extend(self.command_completer.get_git_completions(
                partial,
                max_results=self.max_suggestions
            ))
        
        else:
            # Command completion
            completions.extend(self.command_completer.get_command_completions(
                text,
                max_results=self.max_suggestions // 2
            ))
            
            # History completion
            if self.history_based:
                completions.extend(self.history_completer.get_history_completions(
                    text,
                    max_results=self.max_suggestions // 2
                ))
        
        # Sort and deduplicate
        seen = set()
        unique_completions = []
        for comp in sorted(completions):
            if comp.text not in seen:
                seen.add(comp.text)
                unique_completions.append(comp)
        
        return unique_completions[:self.max_suggestions]
    
    def add_to_history(self, command: str) -> None:
        """Add executed command to history."""
        self.history_completer.add_to_history(command)
    
    def clear_caches(self) -> None:
        """Clear all caches."""
        self.file_completer.clear_cache()
        self.command_completer.command_cache = None


# Global autocompleter instance
_autocompleter: Optional[AutoCompleter] = None


def get_autocompleter(config: Optional[Dict] = None) -> AutoCompleter:
    """Get or create global autocompleter."""
    global _autocompleter
    if _autocompleter is None:
        _autocompleter = AutoCompleter(config)
    return _autocompleter
