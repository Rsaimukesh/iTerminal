# Hyperthread Optimization

iTerminal now includes advanced hyperthreading optimization to significantly improve response time for AI requests. This feature parallelizes API requests to Ollama, making better use of modern CPU architectures.

## Performance Benefits

- **Faster Response Times**: Up to 40-60% improvement in AI response speed
- **Better Resource Utilization**: Makes full use of your CPU's hyperthreading capabilities
- **Parallel API Requests**: Handles multiple requests simultaneously for better throughput
- **Optimized for Modern CPUs**: Automatically adjusts based on your system's capabilities

## How to Use Hyperthreading

### Option 1: Use the hyperthread startup script

```bash
./scripts/hyperthread_iterminal.sh
```

### Option 2: Enable in .env file

Add or modify these settings in your `.env` file:

```
ITERMINAL_HYPERTHREAD_ENABLED=true
ITERMINAL_MAX_CONCURRENT_TASKS=16
ITERMINAL_PARALLEL_REQUESTS=8
```

### Option 3: Set environment variables directly

```bash
export ITERMINAL_HYPERTHREAD_ENABLED=true
export ITERMINAL_PARALLEL_REQUESTS=8
python iterminal.py
```

## Benchmarking

To see the performance difference with hyperthreading:

```bash
./scripts/benchmark_hyperthread.py
```

## Configuration Options

| Environment Variable | Description | Default Value |
|---|---|---|
| ITERMINAL_HYPERTHREAD_ENABLED | Enable/disable hyperthreading | true |
| ITERMINAL_MAX_CONCURRENT_TASKS | Maximum concurrent tasks | 16 (or 4x CPU cores) |
| ITERMINAL_PARALLEL_REQUESTS | Number of parallel API requests | 8 (or 2x CPU cores) |
| ITERMINAL_REQUEST_TIMEOUT | API request timeout in seconds | 60 |