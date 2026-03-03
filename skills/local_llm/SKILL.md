---
name: local_llm
description: "Local LLM integration with Ollama and vLLM support. Run LLMs locally without external API calls."
version: "1.0.0"
user-invocable: true
metadata:
  capabilities:
    - local_llm/ollama
    - local_llm/vllm
    - local_llm/chat
    - local_llm/embed
  author: "OpenPango Contributor"
  license: "MIT"
---

# Local LLM Integration

Run LLMs locally using Ollama or vLLM. No external API keys required.

## Features

- **Ollama Support**: Integration with Ollama server
- **vLLM Support**: High-throughput vLLM inference
- **Chat Completions**: OpenAI-compatible API
- **Embeddings**: Generate embeddings locally
- **Model Management**: List, pull, and manage models

## Configuration

| Environment Variable | Description |
|---------------------|-------------|
| `OLLAMA_HOST` | Ollama server URL (default: http://localhost:11434) |
| `VLLM_HOST` | vLLM server URL (default: http://localhost:8000) |

## Usage

```python
from skills.local_llm.ollama import OllamaClient

# Initialize
client = OllamaClient()

# List models
models = client.list_models()

# Chat
response = client.chat("llama3", "Hello!")

# Generate embeddings
embeddings = client.embed("llama3", "Hello world")
```
