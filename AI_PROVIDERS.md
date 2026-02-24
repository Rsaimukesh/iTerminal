# iTerminal AI Providers & Models

## Supported AI Providers

iTerminal supports **2 primary AI providers** with automatic fallback:

### 1. **Ollama** (Local, Recommended)
- **Type:** Local AI models running on your machine
- **Privacy:** 100% private - no data sent to external servers
- **Cost:** Free
- **Performance:** Fast (no network latency)
- **Default Model:** `llama2` (can be customized)
- **Setup:** Download from [ollama.ai](https://ollama.ai)

**Configure:**
```bash
export ITERMINAL_AI_PROVIDER=ollama
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=llama2  # or neural-chat, mistral, etc.
```

### 2. **OpenRouter** (Cloud-Based)
- **Type:** Cloud API with access to multiple AI models
- **Privacy:** Data sent to OpenRouter servers (encrypted)
- **Cost:** Pay-as-you-go (affordable)
- **Performance:** Slower (network dependent)
- **Models:** Multiple options available (see below)
- **Website:** [openrouter.ai](https://openrouter.ai)

**Configure:**
```bash
export ITERMINAL_AI_PROVIDER=openrouter
export OPENROUTER_API_KEY=sk-...
```

### 3. **Auto-Select** (Default)
- Automatically tries providers in this order:
  1. **Ollama** (if available locally)
  2. **OpenRouter** (if API key is set)
- Falls back gracefully if one fails

**Configure:**
```bash
export ITERMINAL_AI_PROVIDER=auto
```

---

## OpenRouter Available Models

### Recommended Models (Fast & Good Quality)
```
openai/gpt-3.5-turbo          # Most reliable, affordable
anthropic/claude-instant-v1   # Good alternative
google/palm-2-chat-bison      # Another quality option
meta-llama/llama-2-13b-chat   # Free open-source option
```

### Premium Models (Better Quality, Higher Cost)
```
openai/gpt-4-turbo            # Best quality
anthropic/claude-2.0          # Premium alternative
```

---

## Ollama Available Models

Popular models you can use locally:

```bash
# Download and use different models
ollama pull llama2              # 4GB, general purpose
ollama pull neural-chat         # Optimized for chat
ollama pull mistral             # Fast, good quality
ollama pull dolphin-mixtral     # High quality
ollama pull openchat            # Smaller, faster

# Set your preference
export OLLAMA_MODEL=mistral
```

---

## AI Configuration

### Environment Variables

```bash
# Provider Selection
export ITERMINAL_AI_PROVIDER=auto          # auto, ollama, or openrouter

# Ollama Settings
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=llama2

# OpenRouter Settings
export OPENROUTER_API_KEY=sk-...

# Retry Configuration
export ITERMINAL_RETRY_ATTEMPTS=3          # Number of retries
export ITERMINAL_RETRY_BACKOFF=2.0         # Backoff multiplier

# Performance
export ITERMINAL_REQUEST_TIMEOUT=60        # Timeout in seconds
export ITERMINAL_PARALLEL_REQUESTS=4       # Parallel API calls
export ITERMINAL_CACHE_ENABLED=1           # Cache responses
export ITERMINAL_CACHE_DURATION=7200       # Cache for 2 hours
```

---

## Quick Start Guide

### Option 1: Use Local Ollama (Recommended)

```bash
# 1. Install Ollama
curl https://ollama.ai/install.sh | sh

# 2. Download a model
ollama pull llama2

# 3. Run Ollama in background
ollama serve &

# 4. Start iTerminal
python -m iterminal.cli
```

### Option 2: Use OpenRouter (Cloud)

```bash
# 1. Get API key from openrouter.ai
# 2. Set environment variable
export OPENROUTER_API_KEY=sk-...

# 3. Start iTerminal
python -m iterminal.cli
```

### Option 3: Auto-Select (Try Local First, Fallback to Cloud)

```bash
# 1. Install Ollama (optional)
# 2. Set OpenRouter API key (optional)
export OPENROUTER_API_KEY=sk-...

# 3. Start with auto-select
export ITERMINAL_AI_PROVIDER=auto
python -m iterminal.cli
```

---

## How iTerminal Uses AI

### Natural Language to Shell Commands
```
User input:  "show me the largest files in my home directory"
AI output:   ls -lhS ~/ | head -20
Execution:   Runs the command
```

### Command Explanation
```
User input:   find . -name "*.txt" -mtime -7
AI explains:  Find all .txt files modified in last 7 days
```

### Error Correction
```
User input:   "updaet my system"  (typo)
AI corrects:  "sudo apt update && sudo apt upgrade"
```

### Command Suggestions
```
User types:   "check my IP"
AI suggests:  curl ifconfig.me
```

---

## Performance Comparison

| Provider | Speed | Privacy | Cost | Quality |
|----------|-------|---------|------|---------|
| **Ollama (Local)** | ⚡⚡⚡ | 🔒🔒🔒 | 💰💰💰 | ⭐⭐⭐ |
| **OpenRouter** | ⚡⚡ | 🔒 | 💰 | ⭐⭐⭐⭐ |

---

## Caching & Performance

### Response Caching
- Responses are cached for 2 hours by default
- Same prompts return instant results
- Reduces API calls and improves performance

**Configure cache duration:**
```bash
export ITERMINAL_CACHE_DURATION=14400  # 4 hours
```

### Parallel Requests
- Multiple AI requests can run in parallel
- Improves responsiveness

**Configure parallel requests:**
```bash
export ITERMINAL_PARALLEL_REQUESTS=8  # More concurrent requests
```

---

## Error Handling & Fallback

### Circuit Breaker Pattern
- If an AI provider fails 5+ times, it's automatically disabled
- Waits 60 seconds before attempting recovery
- Automatically falls back to next provider

### Retry Logic
- Automatic retry with exponential backoff
- Default: 3 retry attempts
- Wait times: 1s, 2s, 4s

**Configure retries:**
```bash
export ITERMINAL_RETRY_ATTEMPTS=5
export ITERMINAL_RETRY_BACKOFF=3.0
```

---

## Cost Estimation

### Ollama (Local)
- **One-time cost:** 0 (open source)
- **Recurring cost:** Electricity only (~$1-5/month)
- **Data usage:** 0 (everything local)

### OpenRouter
- **Typical costs:**
  - GPT-3.5: $0.0015 per 1K tokens
  - GPT-4: $0.015 per 1K tokens
  - Llama 2: $0.0002 per 1K tokens
- **Monthly estimate:** $5-50 depending on usage

---

## Best Practices

### For Privacy
```bash
export ITERMINAL_AI_PROVIDER=ollama
# No data leaves your machine
```

### For Best Quality
```bash
export ITERMINAL_AI_PROVIDER=openrouter
export OPENROUTER_API_KEY=sk-...
# Access to GPT-4 and other premium models
```

### For Cost Control
```bash
export ITERMINAL_AI_PROVIDER=ollama
# Free, unlimited usage
```

### For Hybrid Approach
```bash
export ITERMINAL_AI_PROVIDER=auto
# Try local first, fallback to cloud if needed
```

---

## Troubleshooting

### Ollama Not Working
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it
ollama serve &

# Verify model is downloaded
ollama list
```

### OpenRouter Not Working
```bash
# Check API key
echo $OPENROUTER_API_KEY

# Verify API key is valid
curl -X POST https://api.openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer sk-..."
```

### Slow Responses
```bash
# Check cache is enabled
export ITERMINAL_CACHE_ENABLED=1

# Increase parallel requests
export ITERMINAL_PARALLEL_REQUESTS=8

# Use faster model
export OLLAMA_MODEL=neural-chat  # Faster than llama2
```

---

## Summary

**iTerminal uses AI to:**
- Translate natural language to shell commands
- Explain what commands do
- Fix typos and errors
- Suggest related commands

**Two AI providers:**
1. **Ollama** - Local, private, free
2. **OpenRouter** - Cloud, quality, pay-as-you-go

**Auto-selection:** Tries local first, falls back to cloud

**Production-ready:**
- Caching for performance
- Retry logic with backoff
- Circuit breaker for fault tolerance
- Configurable via environment variables
