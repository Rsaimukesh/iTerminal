# iTerminal Architecture Implementation Guide

## Overview

This guide explains the new production-ready architecture for iTerminal with comprehensive examples, configuration options, and best practices.

## Quick Start

### 1. Basic Usage (Automatic via CLI)

```bash
# Start iTerminal with new architecture
python -m iterminal.cli

# Or use the main entry point
python iterminal.py
```

### 2. Programmatic Usage with DI

```python
from iterminal.config import get_settings
from iterminal.core import get_application_context

# Get application context (handles all initialization)
context = get_application_context()

# Access services
settings = context.get_settings()
error_handler = context.get_error_handler()
executor_pool = context.get_executor_pool()
autocompleter = context.get_autocompleter()

print(f"AI Provider: {settings.ai.provider.value}")
print(f"Cache Duration: {settings.performance.cache_duration}s")
```

---

## Configuration System

### Environment Variables

All configuration is controlled via environment variables. No code changes needed!

#### Performance Settings
```bash
# Thread/Process configuration
export ITERMINAL_HYPERTHREAD=1                    # Enable hyperthreading (default: 1)
export ITERMINAL_THREAD_COUNT=16                  # Number of threads (default: 16)
export ITERMINAL_PROCESS_COUNT=2                  # Number of processes (default: 2)
export ITERMINAL_PARALLEL_REQUESTS=4              # Parallel AI requests (default: 4)
export ITERMINAL_REQUEST_TIMEOUT=60               # Request timeout seconds (default: 60)

# Caching
export ITERMINAL_CACHE_ENABLED=1                  # Enable caching (default: 1)
export ITERMINAL_CACHE_DURATION=7200              # Cache duration seconds (default: 7200)
```

#### AI Provider Settings
```bash
# AI Provider selection
export ITERMINAL_AI_PROVIDER=auto                 # auto, ollama, or openrouter (default: auto)

# OpenRouter
export OPENROUTER_API_KEY=sk-...

# Ollama (local)
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=llama2

# Retry configuration
export ITERMINAL_RETRY_ATTEMPTS=3                 # Retry attempts (default: 3)
export ITERMINAL_RETRY_BACKOFF=2.0                # Exponential backoff factor (default: 2.0)
```

#### Completion Settings
```bash
export ITERMINAL_COMPLETION=1                     # Enable completion (default: 1)
export ITERMINAL_FUZZY_MATCH=1                    # Fuzzy matching (default: 1)
export ITERMINAL_HISTORY_COMPLETE=1               # History-based (default: 1)
export ITERMINAL_AI_SUGGESTIONS=1                 # AI suggestions (default: 1)
export ITERMINAL_MAX_SUGGESTIONS=10               # Max suggestions (default: 10)
export ITERMINAL_SUGGESTION_DELAY=100             # Delay in ms (default: 100)
export ITERMINAL_CACHE_SUGGESTIONS=1              # Cache suggestions (default: 1)
export ITERMINAL_IGNORE_CASE=1                    # Case-insensitive (default: 1)
```

#### Logging Settings
```bash
export ITERMINAL_LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR (default: INFO)
export ITERMINAL_LOG_FILE=/var/log/iterminal.log  # Log file path (optional)
export ITERMINAL_CONSOLE_LOG=1                    # Console output (default: 1)
export ITERMINAL_STRUCTURED_LOG=1                 # Structured logging (default: 1)
```

#### UI/Theme Settings
```bash
export ITERMINAL_THEME=default                    # Theme name (default: default)
export ITERMINAL_COLORS=1                         # Enable colors (default: 1)
export ITERMINAL_UNICODE=1                        # Enable unicode (default: 1)
export ITERMINAL_ANIMATION=1                      # Enable animations (default: 1)
export ITERMINAL_PROGRESS_BAR=1                   # Progress bars (default: 1)
```

#### Security Settings
```bash
export ITERMINAL_SAFE_MODE=1                      # Safe mode (default: 1)
export ITERMINAL_CONFIRM=1                        # Require confirmation (default: 1)
export ITERMINAL_MAX_CMD_LEN=10000                # Max command length (default: 10000)
export ITERMINAL_WHITELIST_COMMANDS=ls,cat,grep   # Whitelisted commands
export ITERMINAL_BLACKLIST_COMMANDS=rm,dd         # Blacklisted commands
```

### Example Configurations

#### Ultra-Fast Mode (Maximum Performance)
```bash
export ITERMINAL_HYPERTHREAD=1
export ITERMINAL_THREAD_COUNT=32
export ITERMINAL_PARALLEL_REQUESTS=8
export ITERMINAL_CACHE_ENABLED=1
export ITERMINAL_CACHE_DURATION=14400
export ITERMINAL_FUZZY_MATCH=1
export ITERMINAL_HISTORY_COMPLETE=1
```

#### Privacy Mode (Local Only, No API Calls)
```bash
export ITERMINAL_AI_PROVIDER=ollama
export ITERMINAL_CACHE_ENABLED=1
export ITERMINAL_COMPLETION=1
export ITERMINAL_SAFE_MODE=1
```

#### Debug Mode (Verbose Logging)
```bash
export ITERMINAL_LOG_LEVEL=DEBUG
export ITERMINAL_LOG_FILE=/tmp/iterminal-debug.log
export ITERMINAL_STRUCTURED_LOG=1
```

---

## Autocomplete & Tab Completion

### How It Works

The new autocomplete system provides intelligent suggestions from multiple sources:

1. **Command Completion** - Suggests shell commands based on fuzzy matching
2. **File Completion** - Autocompletes file paths with smart directory handling
3. **Git Completion** - Special handling for git subcommands
4. **History Completion** - Suggests previously executed commands by frequency
5. **Fuzzy Matching** - Tolerates typos and partial matches

### Usage Example

```python
from iterminal.completion import get_autocompleter

# Get autocompleter
completer = get_autocompleter()

# Get suggestions for input
suggestions = completer.get_completions("cd /home")

for suggestion in suggestions:
    print(f"{suggestion.text:20} - {suggestion.description}")
    # Output:
    # /home/user/         - Directory
    # /home/documents/    - Directory
    # /home/downloads/    - Directory

# Add executed command to history
completer.add_to_history("ls -la /var/log")

# Get command suggestions
cmd_suggestions = completer.get_completions("ls")
# Returns: ls, lsof, lsb_release, etc.

# Get git command suggestions
git_suggestions = completer.get_completions("git c")
# Returns: checkout, commit, config, etc.
```

### Key Features

#### Fuzzy Matching
```python
from iterminal.completion import FuzzyMatcher

# Fuzzy matching is case-insensitive by default
score = FuzzyMatcher.match("gco", "git checkout")  # 0.82
score = FuzzyMatcher.match("lst", "list")           # 0.60

# Get best matches
matches = FuzzyMatcher.filter_matches("cd", ["cd", "cmake", "code"])
# Returns: [("cd", 1.0), ("cmake", 0.85), ("code", 0.75)]
```

#### History-Based Completion
```python
history = completer.history_completer
history.add_to_history("docker ps -a")
history.add_to_history("docker run -it ubuntu bash")
history.add_to_history("docker ps -a")  # Added again

# Get completions ranked by frequency
suggestions = history.get_history_completions("docker")
# "docker ps -a" appears first (frequency: 2)
```

#### File Path Completion
```python
completer = get_autocompleter()

# Complete file paths
suggestions = completer.file_completer.get_completions("~/Docum")
# Returns: Documents/, Downloads/

# Smart handling of ~
suggestions = completer.file_completer.get_completions("~/.con")
# Returns: .config/, .console/, etc.
```

---

## Error Handling & Resilience

### Circuit Breaker Pattern

Automatically handles API failures and prevents cascading failures:

```python
from iterminal.execution import get_error_handler, CircuitBreakerConfig

handler = get_error_handler()

# Get circuit breaker for AI provider
cb_config = CircuitBreakerConfig(
    name="openrouter",
    failure_threshold=5,
    recovery_timeout=60
)
circuit_breaker = handler.get_circuit_breaker("openrouter", cb_config)

# Execute with circuit breaker
def call_ai():
    return requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        json={"message": "Hello"}
    )

try:
    result = circuit_breaker.call(call_ai)
except Exception as e:
    print(f"Circuit breaker open: {e}")
```

### Retry with Exponential Backoff

```python
from iterminal.execution import Retry, RetryConfig

config = RetryConfig(
    max_attempts=3,
    backoff_factor=2.0,
    initial_delay=1.0,
    max_delay=60.0,
    jitter=True
)

result = Retry.execute(
    func=call_api,
    config=config,
    url="https://api.example.com/data"
)

# Retry delays:
# Attempt 1: Fails, wait 1s
# Attempt 2: Fails, wait 2s
# Attempt 3: Fails, wait 4s
# Attempt 4 (if allowed): Succeeds
```

### Error Categorization

```python
handler = get_error_handler()

try:
    # Some operation
    pass
except Exception as e:
    # Categorize error
    category = handler.categorize_error(e)
    action = handler.get_recovery_action(category)
    
    print(f"Error category: {category.value}")
    print(f"Recovery action: {action}")
    
    # Track error
    handler.track_error("ai_service", e)
    
    # Get statistics
    stats = handler.get_error_stats()
    print(f"Total errors: {stats}")
```

---

## Executor Pool Management

### Centralized Thread/Process Management

```python
from iterminal.execution import get_executor_pool

pool = get_executor_pool()

# Execute in thread pool
future = pool.get_thread_executor().submit(some_function, arg1, arg2)
result = future.result()

# Execute in process pool
future = pool.get_process_executor().submit(cpu_intensive_function)
result = future.result()

# Clean shutdown
pool.shutdown(wait=True)
```

### With Context Manager

```python
from iterminal.execution import ExecutorPool

with ExecutorPool.get_instance() as pool:
    # Executors initialized
    tasks = []
    for item in items:
        future = pool.get_thread_executor().submit(process, item)
        tasks.append(future)
    
    # Get all results
    results = [f.result() for f in tasks]

# Executors automatically shutdown
```

---

## Application Context & Dependency Injection

### Basic Usage

```python
from iterminal.core import get_application_context

# Get context (initializes all services)
context = get_application_context()

# Access any service
settings = context.get_settings()
error_handler = context.get_error_handler()
executor_pool = context.get_executor_pool()
autocompleter = context.get_autocompleter()
```

### Register Custom Services

```python
from iterminal.core import create_application_context

# Create new context for testing
context = create_application_context()

# Register custom service
class MyCustomService:
    def do_something(self):
        pass

context.register("my_service", MyCustomService())

# Get it back
service = context.get("my_service")
```

### Testing with DI

```python
import unittest
from iterminal.core import create_application_context

class TestMyComponent(unittest.TestCase):
    def setUp(self):
        # Create isolated context for test
        self.context = create_application_context()
        
        # Register mock services
        mock_ai = MockAIService()
        self.context.register("ai_service", mock_ai)
    
    def tearDown(self):
        self.context.shutdown()
    
    def test_something(self):
        service = self.context.get("ai_service")
        # Test with mock
```

---

## Production Deployment

### Docker Configuration

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Set production environment variables
ENV ITERMINAL_LOG_LEVEL=WARNING
ENV ITERMINAL_SAFE_MODE=1
ENV ITERMINAL_CACHE_ENABLED=1
ENV ITERMINAL_CACHE_DURATION=14400
ENV OLLAMA_BASE_URL=http://ollama:11434

ENTRYPOINT ["python", "-m", "iterminal.cli"]
```

### Kubernetes ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: iterminal-config
data:
  ITERMINAL_LOG_LEVEL: "INFO"
  ITERMINAL_THREAD_COUNT: "32"
  ITERMINAL_CACHE_ENABLED: "1"
  ITERMINAL_AI_PROVIDER: "openrouter"
  ITERMINAL_SAFE_MODE: "1"
---
apiVersion: v1
kind: Pod
metadata:
  name: iterminal
spec:
  containers:
  - name: iterminal
    image: iterminal:latest
    envFrom:
    - configMapRef:
        name: iterminal-config
```

### Monitoring

```python
from iterminal.execution import get_error_handler

handler = get_error_handler()

# Periodically check error statistics
stats = handler.get_error_stats()

# Log metrics
for component, count in stats.items():
    logger.warning(f"Component {component} had {count} errors")

# Reset statistics
handler.reset_error_stats()
```

---

## Migration Guide (From Old Code)

### Old Code (Still Works)

```python
from iterminal.config import get_api_key, OLLAMA_BASE_URL
from iterminal.ai import explain_command

# Old way still works
api_key = get_api_key()
explanation = explain_command("ls -la")
```

### New Code (Recommended)

```python
from iterminal.core import get_application_context
from iterminal.config import get_settings

# New way
context = get_application_context()
settings = context.get_settings()
api_key = settings.ai.openrouter_api_key
ollama_url = settings.ai.ollama_base_url

# Use services through context
error_handler = context.get_error_handler()
autocompleter = context.get_autocompleter()
```

### Gradual Migration Path

1. **Phase 1**: Update environment variables (configs work immediately)
2. **Phase 2**: Import `ApplicationContext` in new code
3. **Phase 3**: Refactor old modules to use context
4. **Phase 4**: Remove legacy code when all tests pass

---

## Best Practices

### 1. Always Use Dependency Injection

```python
# ❌ Bad: Direct imports and global state
from iterminal.ai import call_openrouter

def my_function():
    result = call_openrouter(prompt)
```

```python
# ✅ Good: Use DI
def my_function(context):
    ai_service = context.get("ai_service")
    result = ai_service.generate_response(prompt)
```

### 2. Handle Errors Gracefully

```python
# ❌ Bad: Let exceptions bubble up
def process():
    api_response = make_api_call()
```

```python
# ✅ Good: Use error handler
def process(context):
    handler = context.get_error_handler()
    try:
        api_response = make_api_call()
    except Exception as e:
        handler.track_error("api_service", e)
        category = handler.categorize_error(e)
        # Handle appropriately
```

### 3. Use Executor Pool for Async Work

```python
# ❌ Bad: Create new threads
import threading
threading.Thread(target=long_task).start()

# ✅ Good: Use executor pool
pool = context.get_executor_pool()
future = pool.get_thread_executor().submit(long_task)
```

### 4. Configure via Environment Variables

```bash
# ✅ Good: All configuration external
export ITERMINAL_THREAD_COUNT=32
export ITERMINAL_CACHE_DURATION=14400
python -m iterminal.cli
```

### 5. Cache Completion Results

```python
# ✅ Good: Completer caches results automatically
completer = context.get_autocompleter()

# First call: builds cache
suggestions = completer.get_completions("ls")

# Subsequent calls: uses cache
suggestions = completer.get_completions("ls -l")
```

---

## Troubleshooting

### Issue: Slow Completions

**Solution**: Check cache settings
```bash
export ITERMINAL_CACHE_SUGGESTIONS=1
export ITERMINAL_CACHE_DURATION=14400
```

### Issue: High Memory Usage

**Solution**: Reduce thread count
```bash
export ITERMINAL_THREAD_COUNT=8
export ITERMINAL_PARALLEL_REQUESTS=2
```

### Issue: API Failures

**Solution**: Enable logging and check circuit breaker
```bash
export ITERMINAL_LOG_LEVEL=DEBUG
export ITERMINAL_LOG_FILE=/tmp/iterminal.log

# Check logs
tail -f /tmp/iterminal.log | grep "Circuit"
```

### Issue: Missing Completions

**Solution**: Clear cache and verify permissions
```bash
python -c "from iterminal.completion import get_autocompleter; get_autocompleter().clear_caches()"
```

---

## Summary

The new architecture provides:

✅ **Unified Configuration** - Single source of truth via environment variables  
✅ **Dependency Injection** - Clean, testable, loosely coupled components  
✅ **Error Resilience** - Circuit breaker, retry, graceful degradation  
✅ **Advanced Completion** - Fuzzy matching, history-based, cached suggestions  
✅ **Production Ready** - Logging, metrics, error tracking, resource management  
✅ **Backward Compatible** - Old code continues to work  

For more information, see:
- [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md) - Visual architecture
- [ARCHITECTURAL_IMPROVEMENTS.md](ARCHITECTURAL_IMPROVEMENTS.md) - Improvement details
