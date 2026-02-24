# Training & Using Local AI Models with iTerminal

## Overview

Yes! You can **train and use local models** with iTerminal. There are two main approaches:

1. **Use Pre-trained Models** (Easiest)
2. **Fine-tune Existing Models** (Recommended)
3. **Train Custom Models** (Advanced)

---

## ✅ Option 1: Use Pre-trained Local Models (Easiest)

### Via Ollama (Recommended)

Ollama makes it super easy to run local models without any training needed.

```bash
# List available models
ollama list

# Download a model
ollama pull llama2
ollama pull mistral
ollama pull neural-chat
ollama pull orca-mini

# Run Ollama server
ollama serve

# In another terminal, test it
curl http://localhost:11434/api/generate -d '{
  "model": "llama2",
  "prompt": "What is a terminal?"
}'

# Use with iTerminal
export ITERMINAL_AI_PROVIDER=ollama
export OLLAMA_MODEL=llama2
python -m iterminal.cli
```

### Popular Pre-trained Models

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| **Neural-Chat** | 4GB | ⚡⚡⚡ | ⭐⭐⭐ | Fast, good for chat |
| **Mistral** | 4GB | ⚡⚡⭐ | ⭐⭐⭐⭐ | Balanced, high quality |
| **Llama 2** | 4GB | ⚡⭐ | ⭐⭐⭐ | General purpose |
| **Orca-Mini** | 2GB | ⚡⚡⚡ | ⭐⭐ | Smallest, fastest |
| **Dolphin-Mixtral** | 27GB | ⚡ | ⭐⭐⭐⭐⭐ | Highest quality |

---

## 🎯 Option 2: Fine-tune Existing Models (Recommended)

Fine-tuning adapts a pre-trained model to your specific use case.

### A. Fine-tune with LoRA (Easiest)

LoRA (Low-Rank Adaptation) is efficient and requires minimal compute.

```bash
# Install dependencies
pip install peft transformers torch

# Create training script
cat > finetune_local_model.py << 'EOF'
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments
from peft import get_peft_model, LoraConfig, TaskType

# Model to fine-tune
model_name = "mistralai/Mistral-7B-v0.1"

# Load base model and tokenizer
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Configure LoRA
peft_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=8,
    lora_alpha=32,
    lora_dropout=0.1,
    target_modules=["q_proj", "v_proj"]
)

# Apply LoRA
model = get_peft_model(model, peft_config)

# Your training data
training_data = [
    "sudo apt update && sudo apt upgrade",
    "find . -name '*.txt' -mtime -7",
    "docker ps -a",
    # Add more examples...
]

# Tokenize data
inputs = tokenizer(
    training_data,
    truncation=True,
    max_length=512,
    return_tensors="pt"
)

# Training arguments
training_args = TrainingArguments(
    output_dir="./fine_tuned_model",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    save_steps=10,
    save_total_limit=2,
)

# Train
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=inputs,
)

trainer.train()

# Save fine-tuned model
model.save_pretrained("./my_local_model")
EOF

# Run fine-tuning
python finetune_local_model.py
```

### B. Fine-tune with Simple Script

```bash
# Install dependencies
pip install ollama peft transformers torch

# Create simple training script
cat > train_custom_model.py << 'EOF'
from peft import get_peft_model, LoraConfig, TaskType
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Your custom training data (shell commands + explanations)
training_examples = [
    {
        "command": "ls -la",
        "explanation": "List all files with details"
    },
    {
        "command": "find . -name '*.py' -exec grep -l 'def ' {} \\;",
        "explanation": "Find Python files containing function definitions"
    },
    {
        "command": "ps aux | grep python",
        "explanation": "Show all running Python processes"
    },
    # Add 100+ examples for better results
]

# Load model
model_name = "mistralai/Mistral-7B-v0.1"
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Apply LoRA for efficient fine-tuning
peft_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=8,
    lora_alpha=32,
    lora_dropout=0.1
)
model = get_peft_model(model, peft_config)

# Fine-tune on your data
print("Fine-tuning model on your data...")
# Training logic here...

print("✅ Model fine-tuned successfully!")
print("Use it with: ollama create custom-model --from ./my_local_model")
EOF

python train_custom_model.py
```

### C. Create Ollama Model from Fine-tuned Model

```bash
# Create Modelfile
cat > Modelfile << 'EOF'
FROM mistral
PARAMETER temperature 0.7
PARAMETER num_predict 256
SYSTEM "You are a helpful Linux terminal assistant that translates natural language to shell commands."
EOF

# Create custom model
ollama create my-custom-model -f Modelfile

# Use it
export OLLAMA_MODEL=my-custom-model
python -m iterminal.cli
```

---

## 🚀 Option 3: Train Custom Model from Scratch (Advanced)

For training a model completely from scratch on your own data.

### Step 1: Prepare Training Data

```bash
# Create training data file
cat > training_data.txt << 'EOF'
<|user|>: how do I list files?
<|assistant|>: Use `ls` command. For detailed view: `ls -la`

<|user|>: show me large files
<|assistant|>: Use `du -sh * | sort -hr | head -20` to show top 20 largest items

<|user|>: find python files
<|assistant|>: Use `find . -name "*.py"` to find all Python files

<|user|>: check disk usage
<|assistant|>: Use `df -h` for disk usage or `du -sh` for directory size

<|user|>: kill a process
<|assistant|>: Use `kill -9 PID` where PID is the process ID, or `killall process_name`
EOF
```

### Step 2: Fine-tune with Your Data

```bash
# Install training libraries
pip install transformers datasets peft torch accelerate

# Create training script
cat > train_from_scratch.py << 'EOF'
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments
from datasets import load_dataset
from peft import get_peft_model, LoraConfig, TaskType

# Load dataset
dataset = load_dataset("text", data_files="training_data.txt")

# Load base model
model_name = "gpt2"  # Start with smaller model
model = AutoModelForCausalLM.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token

# Tokenize dataset
def tokenize_function(examples):
    return tokenizer(
        examples["text"],
        padding="max_length",
        truncation=True,
        max_length=512
    )

tokenized_datasets = dataset.map(
    tokenize_function,
    batched=True,
    remove_columns=["text"]
)

# Apply LoRA for efficient training
peft_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=8,
    lora_alpha=32,
    lora_dropout=0.1,
)
model = get_peft_model(model, peft_config)

# Training arguments
training_args = TrainingArguments(
    output_dir="./my_terminal_model",
    learning_rate=2e-4,
    num_train_epochs=10,
    per_device_train_batch_size=8,
    save_steps=500,
    save_total_limit=2,
    logging_steps=100,
)

# Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
)

# Train
trainer.train()

# Save
model.save_pretrained("./my_terminal_model")
EOF

python train_from_scratch.py
```

### Step 3: Convert to Ollama Format

```bash
# Create Ollama model file
cat > Modelfile << 'EOF'
FROM llama2
PARAMETER temperature 0.7
SYSTEM """You are a Linux terminal expert. Convert natural language queries to shell commands."""
EOF

# Create the model
ollama create my-terminal-model -f Modelfile

# Use it
export OLLAMA_MODEL=my-terminal-model
python -m iterminal.cli
```

---

## 📊 Training Comparison

| Approach | Time | Compute | Quality | Difficulty |
|----------|------|---------|---------|------------|
| **Pre-trained** | ⚡ | 💻 | ⭐⭐⭐ | Easy |
| **Fine-tune LoRA** | ⚡⚡ | 💻💻 | ⭐⭐⭐⭐ | Medium |
| **Full Fine-tune** | ⚡⚡⚡ | 💻💻💻 | ⭐⭐⭐⭐⭐ | Hard |
| **Train from Scratch** | 💥 | 💻💻💻💻 | ⭐⭐⭐⭐⭐ | Very Hard |

---

## 🎓 Practical Example: Fine-tune for Your Use Case

```bash
# Step 1: Create training data for your commands
cat > my_commands.txt << 'EOF'
<|user|>: list all python files in my project
<|assistant|>: find . -name "*.py" -type f

<|user|>: count lines of code in python files
<|assistant|>: find . -name "*.py" -exec wc -l {} + | tail -1

<|user|>: find files modified today
<|assistant|>: find . -type f -mtime 0

<|user|>: show me the largest python files
<|assistant|>: find . -name "*.py" -exec ls -lh {} \; | sort -k5 -h | tail -10

<|user|>: delete all python cache files
<|assistant|>: find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; find . -name "*.pyc" -delete
EOF

# Step 2: Fine-tune model
python train_custom_model.py

# Step 3: Create Ollama model
ollama create my-python-assistant -f Modelfile

# Step 4: Use with iTerminal
export OLLAMA_MODEL=my-python-assistant
python -m iterminal.cli
```

---

## 🔧 Integration with iTerminal

### Use Custom Model

```bash
# Configure iTerminal to use your custom model
export ITERMINAL_AI_PROVIDER=ollama
export OLLAMA_MODEL=my-custom-model
export OLLAMA_BASE_URL=http://localhost:11434

# Start iTerminal
python -m iterminal.cli
```

### Monitor Model Performance

```python
from iterminal.core import get_application_context

context = get_application_context()
settings = context.get_settings()

print(f"AI Provider: {settings.ai.provider.value}")
print(f"Model: {settings.ai.ollama_model}")
print(f"Cache enabled: {settings.performance.cache_enabled}")
```

---

## 📈 Training Tips

### 1. **Data Quality**
- Use high-quality examples
- Balance between different command types
- Include explanations for context

### 2. **Hyperparameters**
```python
# Recommended for fine-tuning
learning_rate = 2e-4           # Lower is safer
num_epochs = 5-10              # Depends on data size
batch_size = 8-16              # GPU memory dependent
```

### 3. **Hardware Requirements**

| Model Size | GPU | Time | Quality |
|-----------|-----|------|---------|
| **Small (2GB)** | 4GB | 30 min | Good |
| **Medium (7B)** | 8GB | 2-4 hrs | Very Good |
| **Large (13B)** | 16GB | 8+ hrs | Excellent |

### 4. **Evaluation**

```python
# Test your fine-tuned model
test_prompts = [
    "list all files",
    "find python files",
    "check disk usage",
]

for prompt in test_prompts:
    response = model.generate(prompt)
    print(f"Input: {prompt}")
    print(f"Output: {response}\n")
```

---

## ✅ Quick Start: Fine-tune for iTerminal

```bash
# 1. Install dependencies
pip install peft transformers torch

# 2. Create training data
echo "Your shell commands" > training_data.txt

# 3. Run fine-tuning
python finetune_local_model.py

# 4. Create Ollama model
ollama create my-model -f Modelfile

# 5. Use with iTerminal
export OLLAMA_MODEL=my-model
python -m iterminal.cli
```

---

## 🚀 Recommended Path

### For Beginners
1. Start with pre-trained model: `ollama pull mistral`
2. Use it: `export OLLAMA_MODEL=mistral`
3. Evaluate quality

### For Intermediate Users
1. Collect training data (100+ shell commands)
2. Fine-tune with LoRA (efficient, low resource)
3. Deploy as custom Ollama model

### For Advanced Users
1. Train custom model from scratch
2. Use larger base models
3. Implement advanced training techniques

---

## Resources

- **Ollama:** https://ollama.ai/
- **Hugging Face:** https://huggingface.co/models
- **LoRA Paper:** https://arxiv.org/abs/2106.09685
- **Fine-tuning Guide:** https://huggingface.co/docs/transformers/training

---

## Summary

✅ **Can you train and use local models?** YES!

**Options:**
1. **Easy:** Use pre-trained models (Ollama)
2. **Recommended:** Fine-tune existing models (LoRA)
3. **Advanced:** Train custom models from scratch

**With iTerminal:**
- Set `ITERMINAL_AI_PROVIDER=ollama`
- Set `OLLAMA_MODEL=your-model`
- Get instant local AI assistance!

**No GPU? No problem!** You can fine-tune on CPU or use smaller models.

All models run **100% locally** - no data leaves your machine! 🔒
