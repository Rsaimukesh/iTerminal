# iTerminal Auto-Correction Feature

## Overview
The auto-correction feature in iTerminal automatically detects and fixes common Git command typos without requiring user confirmation, significantly improving the user experience.

## Key Features

### 1. Instant Git Typo Correction
- **No confirmation needed** for common typos
- Automatically corrects 44+ common Git command mistakes
- Displays a subtle notification showing the correction

### 2. Smart Detection
The system uses multiple methods to identify correctable mistakes:

#### a) Dictionary-Based Corrections
Common typos like:
- `gt` → `git`
- `gti` → `git`
- `git statsu` → `git status`
- `git comit` → `git commit`
- `git pussh` → `git push`

#### b) Similarity-Based Corrections
For commands with >80% similarity:
- `git statuss` → `git status` (95.24% similar)
- `git commmit` → `git commit` (95.24% similar)
- Minor misspellings are automatically corrected

### 3. User Experience Improvements

#### Before (Old Behavior):
```
iTerminal > gt status
Error: Command not found
Did you mean: git status? (Y/n/edit/related): _
[User has to type Y and press Enter]
```

#### After (New Behavior):
```
iTerminal > gt status
Auto-correcting: gt status → git status
╭─────────────────── [Git Command: git status] ───────────────────╮
│ Git status shows the state of the working directory...          │
╰──────────────────────────────────────────────────────────────────╯
Running Git command...
On branch main
Your branch is up to date with 'origin/main'.
```

### 4. Cached Explanations
Git commands get instant explanations from the cache:
- No AI query delay
- Consistent, high-quality explanations
- 15+ common Git commands pre-cached

### 5. Performance Optimizations
- Git commands execute with optimized environment variables
- Timeout protection (5-60s depending on command)
- Status indicators for long-running operations

## Supported Typo Corrections

### Git Command Typos
- `gt`, `gti`, `got`, `gi`, `gir` → `git`

### Subcommand Typos
| Typo | Correction |
|------|-----------|
| `git statsu` | `git status` |
| `git stats` | `git status` |
| `git satus` | `git status` |
| `git ad` | `git add` |
| `git comit` | `git commit` |
| `git pussh` | `git push` |
| `git pul` | `git pull` |
| `git branc` | `git branch` |
| `git chekcout` | `git checkout` |
| `git clon` | `git clone` |
| `git lon` | `git log` |
| `git dif` | `git diff` |
| `git merg` | `git merge` |
| `git fetc` | `git fetch` |

...and 30+ more variations!

## Configuration

The auto-correction feature is enabled by default. To customize:

### Adjust Similarity Threshold
Edit `core.py` line ~820:
```python
if similarity > 0.8:  # Change this value (0.0-1.0)
    should_auto_correct = True
```

### Disable Auto-Correction
To always ask for confirmation, set:
```python
should_auto_correct = False
```

### Add Custom Typo Corrections
Edit `git_cache.py` and add to `GIT_TYPO_CORRECTIONS`:
```python
GIT_TYPO_CORRECTIONS = {
    # ... existing entries ...
    "my_typo": "correct_command",
}
```

## Testing

Run the comprehensive test suite:
```bash
python test_auto_correction.py
```

This tests:
- ✅ 44+ typo corrections
- ✅ Similarity-based detection
- ✅ Git command recognition
- ✅ Auto-correction logic

## Benefits

1. **Faster Workflow**: No interruption for common mistakes
2. **Learning Tool**: Shows corrections so users learn proper commands
3. **Less Frustration**: Typos don't break the flow
4. **Smart Detection**: Knows when to auto-correct vs. when to ask
5. **Transparent**: Always shows what was corrected

## Examples in Action

### Example 1: Simple Typo
```
iTerminal > gt add .
Auto-correcting: gt add . → git add .
╭─────────────────── [Git Command: git add] ──────────────────╮
│ The git add command adds new or changed files...            │
╰──────────────────────────────────────────────────────────────╯
Running Git command...
```

### Example 2: Subcommand Typo
```
iTerminal > git statsu
Auto-correcting: git statsu → git status
╭─────────────────── [Git Command: git status] ───────────────╮
│ Git status shows the state of the working directory...      │
╰──────────────────────────────────────────────────────────────╯
On branch main
...
```

### Example 3: Complex Command with Typo
```
iTerminal > git comit -m "Fix bug"
Auto-correcting: git comit → git commit
╭─────────────────── [Git Command: git commit] ───────────────╮
│ The git commit command captures a snapshot...                │
╰──────────────────────────────────────────────────────────────╯
[main a1b2c3d] Fix bug
 1 file changed, 5 insertions(+)
```

## Technical Details

### Auto-Correction Logic
1. **Command entered** → Check if it's a shell command
2. **Is Git command?** → Check for typos in dictionary
3. **Typo found?** → Auto-correct and notify user
4. **No typo?** → Check similarity with AI suggestions
5. **High similarity?** → Auto-correct
6. **Low similarity?** → Ask user for confirmation

### Performance Impact
- Dictionary lookup: **O(1)** - instant
- Similarity check: **O(n)** where n = command length (negligible)
- Total overhead: **<1ms** per command

## Future Enhancements

Planned improvements:
- [ ] Learn from user corrections (adaptive dictionary)
- [ ] Support for other command-line tools (npm, docker, etc.)
- [ ] Configurable auto-correction preferences per user
- [ ] Statistics on most common typos
- [ ] Suggest aliases for frequently mistyped commands

## Conclusion

The auto-correction feature makes iTerminal more user-friendly by:
- Reducing friction in the workflow
- Eliminating unnecessary confirmation prompts
- Providing instant feedback on corrections
- Maintaining transparency about what was changed

This creates a smoother, more intuitive experience while still keeping users informed about their commands.