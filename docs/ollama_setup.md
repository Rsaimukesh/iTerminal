# Connecting Ollama with iTerminal

This guide will help you properly connect your Ollama installation with iTerminal.

## Prerequisites

1. **Ollama installed and running**
   - Install Ollama from [ollama.com/download](https://ollama.com/download)
   - Start the Ollama server by running `ollama serve` in a terminal

2. **At least one model downloaded in Ollama**
   - Download a model by running `ollama pull llama3`
   - Or use another model of your choice

## Quick Setup (Recommended)

For an automatic setup, run:

```bash
cd /home/sai/Desktop/iTerminal
./scripts/connect_ollama.sh
```

This script will:
1. Check if the required Python packages are installed
2. Configure iTerminal to use your Ollama installation
3. Test the connection to make sure everything works

After running, you can start iTerminal with:
```bash
python3 iterminal.py
```

## Manual Setup

If the automatic setup doesn't work, follow these steps:

1. **Start the Ollama server**
   ```bash
   ollama serve
   ```

2. **Check available models**
   ```bash
   ollama list
   ```
   Make note of the models you have installed.

3. **Edit the .env file**
   ```bash
   cd /home/sai/Desktop/iTerminal
   nano .env
   ```
   
   Add or modify these lines:
   ```
   ITERMINAL_AI_PROVIDER=ollama
   OLLAMA_MODEL=llama3:latest  # Replace with your model name
   OLLAMA_BASE_URL=http://localhost:11434
   ```
   
   Save and exit (Ctrl+X, then Y).

4. **Test the connection**
   ```bash
   curl -X POST http://localhost:11434/api/generate \
     -d '{"model": "llama3:latest", "prompt": "Say hello", "stream": false}'
   ```
   Replace `llama3:latest` with your model name.

5. **Run iTerminal**
   ```bash
   python3 iterminal.py
   ```

## Troubleshooting

If you're having trouble connecting Ollama with iTerminal, try these troubleshooting steps:

1. **Check if Ollama server is running**
   ```bash
   curl http://localhost:11434/api/tags
   ```
   You should see a JSON response with available models.

2. **Verify your model exists**
   ```bash
   ollama list
   ```
   Make sure the model name in your .env file matches exactly what's listed here.

3. **Test the Ollama API directly**
   ```bash
   curl -X POST http://localhost:11434/api/generate \
     -d '{"model": "YOUR_MODEL_NAME", "prompt": "Hello", "stream": false}'
   ```
   Replace YOUR_MODEL_NAME with your model name. You should get a response.

4. **Check iTerminal logs**
   Look for any error messages when running iTerminal.

5. **Restart Ollama**
   ```bash
   pkill ollama
   ollama serve
   ```

6. **Run the diagnostic script**
   ```bash
   python3 scripts/connect_ollama.py
   ```
   This interactive script will guide you through setup and troubleshooting.

## Need More Help?

If you're still having issues, run:

```bash
python3 scripts/connect_ollama.py
```

This interactive script will:
- Check your Ollama installation
- List available models
- Configure iTerminal with the correct settings
- Test the connection
- Provide detailed diagnostics if issues are found