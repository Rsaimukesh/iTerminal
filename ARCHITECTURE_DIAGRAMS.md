# iTerminal - Architecture Diagrams & Visual Structure

## 1. Current Architecture (Flat, Monolithic)

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLI ENTRY POINT                            │
│                      (cli.py, iterminal.py)                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │      MONOLITHIC core.py (1080+)    │◄─── PROBLEM: Too many responsibilities
        │  - App loop                         │
        │  - Command execution                │
        │  - UI rendering                     │
        │  - History management               │
        │  - Statistics                       │
        │  - Error handling                   │
        │  - Parallel coordination            │
        └────────────┬─────────────────────┬──┘
                     │                     │
        ┌────────────▼──────┐   ┌──────────▼──────────┐
        │   External Calls  │   │   Scattered Config  │
        │   (not unified)   │   │   (ai.py, core.py)  │
        └─────────┬──────┬──┘   └──────────┬──────────┘
                  │      │                 │
    ┌─────────────▼─┐ ┌──▼─────────┐   ┌──▼──────────┐
    │  ai.py        │ │  shell.py  │   │  config.py  │
    │  (AI logic)   │ │  (command  │   │  (scattered)│
    │               │ │   exec)    │   │             │
    └───────────────┘ └────────────┘   └─────────────┘
        │
    ┌───▼─────────────┐
    │  Duplicated     │
    │  - Executors    │
    │  - Config vars  │
    │  - Threading    │
    └─────────────────┘
```

**Issues:**
- ❌ No clear separation between layers
- ❌ Circular dependencies possible
- ❌ Hard to test individual components
- ❌ Configuration scattered and duplicated
- ❌ Services defined but not used
- ❌ Tight coupling throughout

---

## 2. Proposed Architecture (Layered, Modular)

```
┌──────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                            │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  cli.py (Simple entry point, ~20 lines)                       │  │
│  │     ↓ (Dependency Injection)                                  │  │
│  │  ApplicationContext (resolver)                                │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────┬───────────────────────────────────────────────────┘
                   │
    ┌──────────────▼────────────────────────────────────┐
    │  APPLICATION LAYER (Orchestration & Control Flow) │
    ├──────────────────────────────────────────────────┤
    │  ┌──────────────────────────────────────────┐   │
    │  │ core/                                    │   │
    │  │ ├── app.py (Main loop, 200 lines)       │   │
    │  │ ├── command_executor.py (150 lines)     │   │
    │  │ ├── session_manager.py (150 lines)      │   │
    │  │ ├── error_handler.py (100 lines)        │   │
    │  │ └── middleware.py (command pipelines)   │   │
    │  └──────────────────────────────────────────┘   │
    └──────────────┬───────────────────────────────────┘
                   │
    ┌──────────────▼──────────────────────────────────────┐
    │  SERVICE LAYER (Business Logic & Orchestration)    │
    ├──────────────────────────────────────────────────┤
    │  ┌─────────────────┐  ┌──────────────────────┐  │
    │  │  AIService      │  │  CommandService      │  │
    │  │  - Provider mgmt│  │  - Execution mgmt    │  │
    │  │  - Caching      │  │  - History tracking  │  │
    │  │  - Retry logic  │  │  - Validation        │  │
    │  └────────┬────────┘  └──────────┬───────────┘  │
    │           │                      │               │
    │  ┌────────▼──────────────────────▼────────────┐  │
    │  │  CircuitBreaker                            │  │
    │  │  - Handles API failures gracefully         │  │
    │  │  - Exponential backoff retry               │  │
    │  └────────────────────────────────────────────┘  │
    └──────────────┬───────────────────────────────────┘
                   │
    ┌──────────────▼──────────────────────────────────────┐
    │  INTERFACE LAYER (Abstract Contracts)              │
    ├──────────────────────────────────────────────────┤
    │  ┌─────────────┐  ┌──────────────┐               │
    │  │ AIProvider  │  │ ShellExecutor│               │
    │  │ (interface) │  │ (interface)  │               │
    │  └─────────────┘  └──────────────┘               │
    └──────────────┬───────────────────────────────────┘
                   │
    ┌──────────────▼──────────────────────────────────────┐
    │  IMPLEMENTATION LAYER (Concrete Providers)         │
    ├──────────────────────────────────────────────────┤
    │  ┌──────────┐ ┌───────────┐ ┌─────────────────┐ │
    │  │ Ollama   │ │ OpenRouter│ │ LocalShell      │ │
    │  │ Provider │ │ Provider  │ │ Executor        │ │
    │  └──────────┘ └───────────┘ └─────────────────┘ │
    └──────────────┬───────────────────────────────────┘
                   │
    ┌──────────────▼──────────────────────────────────────┐
    │  INFRASTRUCTURE LAYER                              │
    ├──────────────────────────────────────────────────┤
    │  ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
    │  │ execution/  │ │ config/     │ │observabil.│ │
    │  │ - Executor  │ │ - Settings  │ │ - Logging │ │
    │  │   Pool      │ │ - Env vars  │ │ - Metrics │ │
    │  └─────────────┘ └─────────────┘ └────────────┘ │
    │  ┌──────────────────────────────────────────────┐ │
    │  │ utils/                                       │ │
    │  │ - Cache, Retry, Validation helpers          │ │
    │  └──────────────────────────────────────────────┘ │
    └──────────────────────────────────────────────────────┘
```

**Benefits:**
- ✅ Clear separation of concerns
- ✅ Each layer has single responsibility
- ✅ Easy to test (mock implementations)
- ✅ Loose coupling (interfaces define contracts)
- ✅ Extensible (add providers, executors)
- ✅ Dependency Injection throughout

---

## 3. Data Flow Diagrams

### Flow A: User Enters Shell Command

```
User Input
    │
    ▼
┌─────────────────────┐
│ Input Validator     │  ◄─── Check if valid shell command
└────────┬────────────┘
         │ (if valid shell command)
         ▼
┌─────────────────────────────────────┐
│ ShellExecutor.execute()             │
│ (Direct execution, no AI needed)    │
└────────┬─────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ CommandService                      │
│ - Run command                       │
│ - Capture output                    │
│ - Store in history                  │
└────────┬─────────────────────────────┘
         │
         ▼
Display Result
```

### Flow B: User Enters Natural Language

```
User Input
    │
    ▼
┌─────────────────────┐
│ Input Validator     │  ◄─── Not a shell command
└────────┬────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ AIService.generate_response()    │
│ ├─ Check cache                   │
│ ├─ Try current provider          │
│ ├─ Handle circuit breaker        │
│ └─ Retry with backoff if fails   │
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ Command Translation              │
│ - NL → Shell command             │
│ - Extract intent                 │
│ - Validate syntax                │
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ User Confirmation                │
│ (Explain before execute)         │
└────────┬─────────────────────────┘
         │ (user confirms)
         ▼
┌──────────────────────────────────┐
│ CommandService.execute()         │
│ - Run translated command         │
│ - Capture output                 │
│ - Store full flow in history     │
└────────┬─────────────────────────┘
         │
         ▼
Display Result & Explanation
```

### Flow C: Error Handling & Recovery

```
Command Execution
    │
    ▼
┌─────────────────┐
│ Error occurs?   │
└────────┬────────┘
         │ Yes
         ▼
┌──────────────────────────────────┐
│ ErrorHandler.handle()            │
├─ Classify error type             │
└────────┬─────────────────────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    │         │          │          │
    ▼         ▼          ▼          ▼
Network  Timeout  Command  AI Provider
Failure  Error    Error    Error
    │         │          │          │
    ▼         ▼          ▼          ▼
Retry with  Timeout  Suggest   Fallback
Backoff     Handler  Fix       Provider
    │         │          │          │
    └─────────┴──────────┴──────────┘
              │
              ▼
    ┌──────────────────────┐
    │ Circuit Breaker      │
    │ Track failures       │
    │ Auto-disable if bad  │
    └──────────────────────┘
              │
              ▼
    Present user with options
    (Retry, Skip, Manual input)
```

---

## 4. Component Dependency Graph

```
                    ┌─────────────────┐
                    │   cli.py        │
                    │   (entry point) │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Context Factory │ ◄─── Dependency Injection
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
    ┌────────┐         ┌──────────┐         ┌────────────┐
    │   App  │         │ AI       │         │ Command    │
    │ (core) │         │ Service  │         │ Service    │
    └───┬────┘         └───┬──────┘         └──┬─────────┘
        │                  │                   │
        │    ┌─────────────┼───────────────┐   │
        │    │             │               │   │
        ▼    ▼             ▼               ▼   ▼
    ┌─────────────────────────────────────────┐
    │  Interfaces Layer                       │
    │  - AIProvider                           │
    │  - ShellExecutor                        │
    │  - CommandValidator                    │
    └─────────────────────────────────────────┘
        │                   │
        ▼                   ▼
    ┌──────────┐      ┌────────────┐
    │ Ollama   │      │ LocalShell │
    │ Provider │      │ Executor   │
    └──────────┘      └────────────┘

    ┌─────────────────────────────────────────┐
    │  Cross-cutting concerns                 │
    │  (used by many components)              │
    ├─────────────────────────────────────────┤
    │  - Config/Settings                      │
    │  - ErrorHandler                         │
    │  - CircuitBreaker                       │
    │  - Logger                               │
    │  - ExecutorPool                         │
    │  - Cache                                │
    │  - Retry utilities                      │
    └─────────────────────────────────────────┘
```

---

## 5. Package Structure (Detailed)

```
iterminal/
│
├── __init__.py                    # Package root
│
├── cli.py                         # Entry point (~20 lines)
│
├── config/                        # UNIFIED CONFIG
│   ├── __init__.py
│   ├── settings.py               # All settings classes
│   ├── environment.py            # Environment var loading
│   └── models.py                 # Config data models
│
├── core/                          # APP LOGIC
│   ├── __init__.py
│   ├── app.py                    # Main loop orchestrator
│   ├── command_executor.py       # Command execution logic
│   ├── session_manager.py        # Session & history
│   ├── error_handler.py          # Error recovery
│   ├── middleware.py             # Command pipelines
│   └── context.py                # DI container
│
├── ui/                            # PRESENTATION
│   ├── __init__.py
│   ├── renderer.py               # Rich rendering
│   ├── components/
│   │   ├── __init__.py
│   │   ├── prompt.py
│   │   ├── result_display.py
│   │   ├── history_panel.py
│   │   └── status_bar.py
│   ├── themes.py                 # Theme config
│   └── formatter.py              # Output formatting
│
├── interfaces/                    # CONTRACTS
│   ├── __init__.py
│   ├── ai_provider.py            # AIProvider interface
│   ├── shell_executor.py         # ShellExecutor interface
│   └── validators.py             # Validation interfaces
│
├── models/                        # DOMAIN MODELS
│   ├── __init__.py
│   ├── command.py                # Command model
│   ├── session.py                # Session model
│   └── response.py               # Response model
│
├── services/                      # BUSINESS LOGIC
│   ├── __init__.py
│   ├── ai_service.py             # AI orchestration
│   ├── command_service.py        # Command management
│   ├── session_service.py        # Session management
│   └── provider_service.py       # Provider management
│
├── providers/                     # IMPLEMENTATIONS
│   ├── __init__.py
│   ├── ollama_provider.py        # Ollama implementation
│   ├── openrouter_provider.py    # OpenRouter implementation
│   └── base_provider.py          # Base provider class
│
├── executors/                     # SHELL EXECUTORS
│   ├── __init__.py
│   ├── local_executor.py         # Local shell executor
│   ├── ssh_executor.py           # SSH executor (future)
│   └── docker_executor.py        # Docker executor (future)
│
├── execution/                     # INFRASTRUCTURE
│   ├── __init__.py
│   ├── executor_pool.py          # Centralized executors
│   ├── resilience.py             # Circuit breaker, retry
│   └── strategies.py             # Execution strategies
│
├── observability/                 # MONITORING
│   ├── __init__.py
│   ├── logger.py                 # Structured logging
│   ├── metrics.py                # Metrics collection
│   ├── profiler.py               # Performance profiling
│   └── telemetry.py              # Telemetry
│
├── utils/                         # UTILITIES
│   ├── __init__.py
│   ├── cache.py                  # Caching utilities
│   ├── retry.py                  # Retry logic
│   ├── validation.py             # Validators
│   ├── decorators.py             # Useful decorators
│   └── helpers.py                # General helpers
│
├── plugins/                       # PLUGIN SYSTEM
│   ├── __init__.py
│   ├── base.py                   # Plugin interface
│   ├── registry.py               # Plugin registry
│   ├── loader.py                 # Plugin loader
│   └── discovery.py              # Plugin discovery
│
└── tests/                         # TESTS (moved to root)
    ├── __init__.py
    ├── conftest.py               # Pytest config
    ├── fixtures/
    ├── unit/
    ├── integration/
    └── e2e/
```

---

## 6. Responsibility Matrix

| Component | Input | Output | Dependencies |
|-----------|-------|--------|--------------|
| **cli.py** | User launch | App instance | Context factory |
| **App** | User input | Display | All services, UI renderer |
| **AIService** | Prompt | Response | AI providers, Cache, CircuitBreaker |
| **CommandService** | Command | Result | Executor, History, Logger |
| **ErrorHandler** | Exception | Recovery action | CircuitBreaker, Logger |
| **Renderer** | Data models | Rich output | Theme config |
| **ShellExecutor** | Command | Output | Process execution |
| **Config** | Env vars | Settings | None |
| **Cache** | Key | Value/None | None |
| **Logger** | Message | Log entry | Config |

---

## 7. Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│                    External Systems                         │
├─────────────────────────────────────────────────────────────┤
│  [Ollama] [OpenRouter] [Linux Shell] [File System]          │
└────┬──────────────────┬──────────────┬─────────────┬────────┘
     │ AI Providers    │              │ Shell      │ Storage
     │                │              │ Executor   │
     ▼                ▼              ▼            ▼
┌──────────────────────────────────────────────────────────────┐
│                    Adapter Layer                            │
│  ┌────────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ ollama_        │  │ local_       │  │ file_storage   │  │
│  │ provider.py    │  │ executor.py  │  │ service.py     │  │
│  └────────────────┘  └──────────────┘  └────────────────┘  │
└──────────────────────────────────────────────────────────────┘
     ▲                  ▲                  ▲
     │ implements       │ implements       │ implements
     │                  │                  │
┌────┴──────────────────┴──────────────────┴────────────────┐
│                 Interface Layer                           │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ AIProvider │ ShellExecutor │ HistoryStorage          │ │
│  └──────────────────────────────────────────────────────┘ │
└────┬────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│                 Service Layer                               │
│  ┌──────────────────┐  ┌──────────────────────────────────┐ │
│  │ AIService        │  │ CommandService                   │ │
│  │ - Orchestrate    │  │ - Execute commands               │ │
│  │ - Switch provider│  │ - Track history                  │ │
│  │ - Cache          │  │ - Validate input                 │ │
│  └──────────────────┘  └──────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## 8. Benefits Comparison

### Current Architecture ❌
```
┌────────────────────────────┐
│ Testability: ⭐☆☆☆☆      │ Hard to mock dependencies
│ Maintainability: ⭐☆☆☆☆  │ 1000+ line monolith
│ Extensibility: ⭐⭐☆☆☆   │ Add provider = modify core
│ Performance: ⭐⭐⭐☆☆    │ Thread pools scattered
│ Observability: ⭐⭐☆☆☆   │ Limited logging
│ Resilience: ⭐⭐☆☆☆     │ No error recovery strategy
└────────────────────────────┘
```

### Proposed Architecture ✅
```
┌────────────────────────────┐
│ Testability: ⭐⭐⭐⭐⭐    │ Full DI, mockable
│ Maintainability: ⭐⭐⭐⭐⭐│ Focused components
│ Extensibility: ⭐⭐⭐⭐⭐  │ Plugin system, interfaces
│ Performance: ⭐⭐⭐⭐☆    │ Centralized management
│ Observability: ⭐⭐⭐⭐⭐ │ Structured logging
│ Resilience: ⭐⭐⭐⭐⭐    │ Circuit breaker, retry
└────────────────────────────┘
```

---

## Summary

The proposed architecture:
- **Separates concerns** into focused layers
- **Enables testability** through dependency injection
- **Supports extensibility** via interfaces and plugins
- **Improves resilience** with error handling strategies
- **Enhances observability** with structured monitoring
- **Simplifies maintenance** by decomposing large files
- **Enables scaling** through proper resource management
