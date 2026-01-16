# iTerminal Architecture

## Overview

iTerminal follows a clean, modular architecture based on separation of concerns, dependency inversion, and service-oriented design principles.

## Architecture Layers

### 1. **Interfaces Layer** (`iterminal/interfaces/`)
Defines abstract contracts and protocols for core components:
- `AIProvider`: Abstract interface for pluggable AI backends (Ollama, OpenRouter, etc.)
- `ShellExecutor`: Abstract interface for command execution strategies
- `CachedAIProvider`: Base class for AI providers with caching support

**Benefits:**
- Enables easy addition of new AI providers
- Facilitates testing with mock implementations
- Promotes loose coupling between components

### 2. **Models Layer** (`iterminal/models/`)
Domain models and data structures:
- `Command`: Represents terminal commands with metadata (type, status, execution details)
- `CommandType`: Enum for command types (shell, natural language, AI-generated)
- `CommandStatus`: Enum for execution status tracking
- `Session`: Represents a terminal session with command history and statistics

**Benefits:**
- Type-safe data structures
- Centralized domain logic
- Easy serialization/deserialization

### 3. **Services Layer** (`iterminal/services/`)
Business logic and orchestration:
- `AIService`: Manages AI provider interactions, caching, and provider switching
- `CommandService`: Handles command execution, validation, and history management

**Benefits:**
- Centralized business logic
- Reusable service components
- Simplified testing and maintenance

### 4. **Core Layer** (`iterminal/`)
Implementation of specific features:
- `ai.py`: AI provider implementations (OpenRouter, Ollama)
- `shell.py`: Shell command execution and validation
- `core.py`: Main application loop and orchestration
- `cli.py`: Command-line interface
- `config.py`: Configuration management
- `logger.py`: Logging infrastructure
- `stats.py`: Usage statistics tracking

## Design Patterns

### 1. **Strategy Pattern**
- `AIProvider` interface allows swapping AI backends at runtime
- Multiple provider implementations (Ollama, OpenRouter)

### 2. **Repository Pattern**
- `CommandService` manages command history and persistence
- Session management with statistical tracking

### 3. **Factory Pattern**
- `AIService` manages provider registration and instantiation
- Dynamic provider selection based on availability

### 4. **Observer Pattern**
- Command status updates trigger UI updates
- Session statistics automatically tracked

### 5. **Singleton Pattern**
- Configuration management (config.py)
- Logging infrastructure

## Data Flow

```
User Input → CLI → Command Service → Shell Executor → Command Result
                ↓
          AI Service → AI Provider → AI Response
                ↓
          Command History → Session Storage
```

## Key Architectural Principles

### 1. **Separation of Concerns**
- Clear separation between UI, business logic, and data layers
- Each module has a single, well-defined responsibility

### 2. **Dependency Inversion**
- High-level modules depend on abstractions (interfaces)
- Low-level modules implement interfaces
- Enables easy testing and extension

### 3. **Open/Closed Principle**
- Open for extension (new AI providers, shell executors)
- Closed for modification (core interfaces remain stable)

### 4. **Single Responsibility**
- Each class has one reason to change
- Services focus on specific domains (AI, commands, etc.)

### 5. **Interface Segregation**
- Small, focused interfaces
- Clients depend only on methods they use

## Performance Optimizations

### 1. **Hyperthreading**
- Parallel AI requests using ThreadPoolExecutor
- Optimal thread pool sizing based on CPU cores
- Configurable concurrency limits

### 2. **Caching**
- Response caching with LRU eviction
- Configurable cache duration
- Thread-safe cache operations

### 3. **Lazy Loading**
- Providers loaded on-demand
- Configuration loaded from environment

## Extensibility Points

### Adding New AI Providers
1. Implement `AIProvider` interface
2. Register with `AIService`
3. Configure in `config.py`

### Adding New Shell Executors
1. Implement `ShellExecutor` interface
2. Inject into `CommandService`
3. Configure execution strategy

### Adding New Command Types
1. Extend `CommandType` enum
2. Add handling logic in `CommandService`
3. Update UI to display new types

## Testing Strategy

### Unit Tests (`tests/`)
- Test individual components in isolation
- Mock dependencies using interfaces
- Fast, focused tests

### Integration Tests
- Test component interactions
- Use test AI providers and executors
- Verify data flow

### End-to-End Tests
- Test complete user workflows
- Verify UI interactions
- Test with real AI providers (optional)

## Future Enhancements

### 1. **Plugin System**
- Dynamic plugin loading
- Third-party provider support
- Custom command handlers

### 2. **Advanced Caching**
- Distributed cache support (Redis)
- Cache warming strategies
- Smart cache invalidation

### 3. **Advanced Analytics**
- Command pattern recognition
- User behavior analytics
- Performance metrics dashboard

### 4. **Multi-User Support**
- User authentication
- Personalized command history
- Shared sessions

### 5. **Enhanced Security**
- Command sandboxing
- Permission-based execution
- Security audit logging

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                            │
│                    (cli.py, core.py)                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                     Services Layer                           │
│  ┌─────────────────┐           ┌───────────────────────┐   │
│  │   AIService     │           │  CommandService       │   │
│  │  - providers    │           │  - executor           │   │
│  │  - caching      │           │  - history            │   │
│  └─────────────────┘           └───────────────────────┘   │
└──────────┬─────────────────────────────┬────────────────────┘
           │                             │
           ↓                             ↓
┌──────────────────────┐      ┌─────────────────────────────┐
│  Interfaces Layer    │      │      Models Layer           │
│  - AIProvider        │      │  - Command                  │
│  - ShellExecutor     │      │  - Session                  │
│  - CachedAIProvider  │      │  - CommandType/Status       │
└──────────┬───────────┘      └─────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────────────────────────┐
│                    Implementation Layer                      │
│  - Ollama Provider  - OpenRouter Provider  - Shell Impl     │
└─────────────────────────────────────────────────────────────┘
```

## Configuration Management

### Environment Variables
- `ITERMINAL_AI_PROVIDER`: AI provider selection (ollama/openrouter)
- `ITERMINAL_CACHE_ENABLED`: Enable/disable caching
- `ITERMINAL_HYPERTHREAD_ENABLED`: Enable/disable hyperthreading
- `ITERMINAL_PERFORMANCE_MODE`: Performance optimizations
- `OLLAMA_BASE_URL`: Ollama server URL
- `OLLAMA_MODEL`: Ollama model name

### Configuration Files
- `.env`: Environment-specific configuration
- `config.py`: Application configuration management

## Deployment

### Development
```bash
pip install -r requirements.txt
python iterminal.py
```

### Production
- Use virtual environments
- Configure AI provider credentials
- Set performance optimizations
- Enable logging

## Maintenance

### Code Quality
- Follow PEP 8 style guide
- Use type hints throughout
- Document public APIs
- Write comprehensive tests

### Monitoring
- Track AI provider response times
- Monitor cache hit rates
- Log command execution errors
- Track session statistics

### Updates
- Keep dependencies updated
- Monitor AI provider API changes
- Update documentation
- Maintain backward compatibility
