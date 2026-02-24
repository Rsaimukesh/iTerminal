"""
Quick reference for the new iTerminal architecture.
Usage: python iterminal/quick_reference.py
"""

from iterminal.config import get_settings, PerformanceConfig, AIConfig
from iterminal.core import get_application_context
from iterminal.completion import get_autocompleter
from iterminal.execution import get_error_handler, CircuitBreakerConfig, Retry, RetryConfig


def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_config():
    """Demonstrate configuration system."""
    print_section("1. Configuration System")
    
    settings = get_settings()
    print("Performance Settings:")
    print(f"  Hyperthread Enabled: {settings.performance.hyperthread_enabled}")
    print(f"  Thread Count: {settings.performance.thread_count}")
    print(f"  Cache Enabled: {settings.performance.cache_enabled}")
    print(f"  Cache Duration: {settings.performance.cache_duration}s")
    
    print("\nAI Settings:")
    print(f"  Provider: {settings.ai.provider.value}")
    print(f"  Ollama Base URL: {settings.ai.ollama_base_url}")
    print(f"  Ollama Model: {settings.ai.ollama_model}")
    
    print("\nCompletion Settings:")
    print(f"  Completion Enabled: {settings.completion.enabled}")
    print(f"  Fuzzy Matching: {settings.completion.fuzzy_matching}")
    print(f"  Max Suggestions: {settings.completion.max_suggestions}")
    
    print("\nLogging Settings:")
    print(f"  Log Level: {settings.logging.level.value}")
    print(f"  Console Output: {settings.logging.console_output}")


def demo_di():
    """Demonstrate dependency injection."""
    print_section("2. Dependency Injection Container")
    
    context = get_application_context()
    
    print("Application Context initialized!")
    print("\nRegistered Services:")
    print("  - error_handler: ErrorHandler")
    print("  - executor_pool: ExecutorPool")
    print("  - autocompleter: AutoCompleter")
    
    print("\nAccessing Services:")
    error_handler = context.get_error_handler()
    print(f"  error_handler: {type(error_handler).__name__}")
    
    executor_pool = context.get_executor_pool()
    print(f"  executor_pool: {type(executor_pool).__name__}")
    
    autocompleter = context.get_autocompleter()
    print(f"  autocompleter: {type(autocompleter).__name__}")


def demo_completion():
    """Demonstrate autocomplete system."""
    print_section("3. Advanced Tab Completion")
    
    completer = get_autocompleter()
    
    print("File Completion (~/Doc):")
    file_completions = completer.file_completer.get_completions("~/.con", max_results=3)
    for comp in file_completions:
        print(f"  - {comp.text:20} ({comp.description})")
    
    print("\nCommand Completion (git):")
    git_completions = completer.command_completer.get_git_completions("co", max_results=3)
    for comp in git_completions:
        print(f"  - {comp.text:20} ({comp.description})")
    
    print("\nHistory-Based Completion:")
    completer.add_to_history("ls -la /var/log")
    completer.add_to_history("ls -la /var/log")
    completer.add_to_history("cd /home")
    
    history_completions = completer.history_completer.get_history_completions("ls", max_results=3)
    for comp in history_completions:
        print(f"  - {comp.text:30} ({comp.description})")
    
    print("\nFuzzy Matching:")
    from iterminal.completion import FuzzyMatcher
    
    test_cases = [
        ("gco", "git checkout"),
        ("lst", "list"),
        ("dc", "docker"),
    ]
    
    for pattern, text in test_cases:
        score = FuzzyMatcher.match(pattern, text)
        print(f"  '{pattern}' vs '{text}': {score:.2f}")


def demo_resilience():
    """Demonstrate error handling and resilience."""
    print_section("4. Error Handling & Resilience")
    
    handler = get_error_handler()
    
    print("Circuit Breaker States:")
    print("  - CLOSED: Normal operation (accepting requests)")
    print("  - OPEN: Failing, rejecting requests")
    print("  - HALF_OPEN: Testing recovery")
    
    print("\nError Categorization:")
    from iterminal.execution import ErrorCategory
    
    test_exceptions = [
        (TimeoutError("Connection timeout"), "Timeout"),
        (ConnectionError("Network unreachable"), "Network"),
        (Exception("Invalid credentials"), "Auth"),
    ]
    
    for exc, label in test_exceptions:
        category = handler.categorize_error(exc)
        action = handler.get_recovery_action(category)
        print(f"  {label:15} -> {action}")
    
    print("\nRetry with Exponential Backoff:")
    print("  Config:")
    print("    - max_attempts: 3")
    print("    - backoff_factor: 2.0")
    print("    - initial_delay: 1.0")
    print("  Delays:")
    print("    - Attempt 1: 1.0s")
    print("    - Attempt 2: 2.0s")
    print("    - Attempt 3: 4.0s")


def demo_executor_pool():
    """Demonstrate executor pool management."""
    print_section("5. Centralized Executor Pool")
    
    pool = get_application_context().get_executor_pool()
    
    print("Thread Executor:")
    print(f"  Type: ThreadPoolExecutor")
    print(f"  Workers: {pool.thread_count}")
    print(f"  State: {'Initialized' if pool._initialized else 'Not initialized'}")
    
    print("\nProcess Executor:")
    print(f"  Type: ProcessPoolExecutor")
    print(f"  Workers: {pool.process_count}")
    print(f"  State: {'Initialized' if pool._initialized else 'Not initialized'}")
    
    print("\nUsage Example:")
    print("""
    pool = get_executor_pool()
    future = pool.get_thread_executor().submit(some_function, arg1)
    result = future.result()
    """)


def demo_config_examples():
    """Show configuration examples."""
    print_section("6. Environment Variable Configuration")
    
    examples = {
        "Ultra-Fast Mode": [
            "ITERMINAL_HYPERTHREAD=1",
            "ITERMINAL_THREAD_COUNT=32",
            "ITERMINAL_PARALLEL_REQUESTS=8",
            "ITERMINAL_CACHE_ENABLED=1",
        ],
        "Privacy Mode (Local Only)": [
            "ITERMINAL_AI_PROVIDER=ollama",
            "ITERMINAL_CACHE_ENABLED=1",
            "ITERMINAL_SAFE_MODE=1",
        ],
        "Debug Mode": [
            "ITERMINAL_LOG_LEVEL=DEBUG",
            "ITERMINAL_LOG_FILE=/tmp/iterminal.log",
            "ITERMINAL_STRUCTURED_LOG=1",
        ],
    }
    
    for mode, vars in examples.items():
        print(f"{mode}:")
        for var in vars:
            print(f"  export {var}")
        print()


def main():
    """Run all demonstrations."""
    print("\n" + "="*60)
    print("  iTerminal - Production-Ready Architecture Demo")
    print("="*60)
    
    try:
        demo_config()
        demo_di()
        demo_completion()
        demo_resilience()
        demo_executor_pool()
        demo_config_examples()
        
        print_section("✅ All Demonstrations Complete!")
        print("""
Next Steps:
1. Read IMPLEMENTATION_GUIDE.md for complete reference
2. Check ARCHITECTURE_DIAGRAMS.md for visual overview
3. Review ARCHITECTURAL_IMPROVEMENTS.md for details
4. Start using the new architecture in your code!

Environment Variables:
- All configuration is via environment variables
- No code changes needed for different deployments
- See IMPLEMENTATION_GUIDE.md for full list

Key Features:
✅ Unified Configuration System
✅ Dependency Injection Container
✅ Advanced Tab Completion
✅ Error Resilience (Circuit Breaker, Retry)
✅ Centralized Executor Pool
✅ Production-Ready Logging
✅ Backward Compatibility
        """)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
