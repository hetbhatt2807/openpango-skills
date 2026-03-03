#!/usr/bin/env python3
"""
ollama.py - Ollama integration for local LLM inference.

Provides OpenAI-compatible API for Ollama server.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Generator
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger("Ollama")


class OllamaError(Exception):
    """Base exception for Ollama errors."""
    pass


class ModelNotFoundError(OllamaError):
    """Model not found."""
    pass


class OllamaClient:
    """
    Ollama client for local LLM inference.
    
    Supports chat completions, embeddings, and model management.
    Falls back to mock mode when Ollama is not available.
    """
    
    def __init__(self, host: Optional[str] = None):
        """
        Initialize Ollama client.
        
        Args:
            host: Ollama server URL (default: http://localhost:11434)
        """
        self.host = (host or os.getenv("OLLAMA_HOST", "http://localhost:11434")).rstrip("/")
        self._mock = False
        
        if requests is None:
            logger.warning("requests not installed. Running in MOCK mode.")
            self._mock = True
        else:
            self._check_connection()
    
    def _check_connection(self):
        """Check connection to Ollama server."""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code != 200:
                logger.warning(f"Ollama returned status {response.status_code}. Running in MOCK mode.")
                self._mock = True
        except Exception as e:
            logger.warning(f"Cannot connect to Ollama: {e}. Running in MOCK mode.")
            self._mock = True
    
    # ─── Model Management ─────────────────────────────────────
    
    def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models.
        
        Returns:
            List of model info dicts
        """
        if self._mock:
            return [
                {"name": "llama3:latest", "size": "4.7 GB", "modified": "2024-01-15"},
                {"name": "mistral:latest", "size": "4.1 GB", "modified": "2024-01-10"},
                {"name": "codellama:latest", "size": "4.7 GB", "modified": "2024-01-05"},
            ]
        
        response = requests.get(f"{self.host}/api/tags")
        response.raise_for_status()
        data = response.json()
        
        return [
            {
                "name": m.get("name", "unknown"),
                "size": m.get("size", 0),
                "modified": m.get("modified_at", ""),
            }
            for m in data.get("models", [])
        ]
    
    def pull_model(self, model: str) -> Dict[str, Any]:
        """
        Pull a model from Ollama registry.
        
        Args:
            model: Model name (e.g., "llama3", "mistral")
            
        Returns:
            Status dict
        """
        if self._mock:
            logger.info(f"[MOCK] Pulling model: {model}")
            return {"status": "success", "model": model}
        
        response = requests.post(
            f"{self.host}/api/pull",
            json={"name": model},
            stream=True
        )
        
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                if data.get("status") == "success":
                    return {"status": "success", "model": model}
        
        return {"status": "error", "model": model}
    
    # ─── Chat Completions ─────────────────────────────────────
    
    def chat(
        self,
        model: str,
        message: str,
        system: Optional[str] = None,
        history: Optional[List[Dict]] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a chat completion request.
        
        Args:
            model: Model name (e.g., "llama3")
            message: User message
            system: System prompt
            history: Chat history
            stream: Enable streaming
            
        Returns:
            Response dict with content
        """
        messages = []
        
        if system:
            messages.append({"role": "system", "content": system})
        
        if history:
            messages.extend(history)
        
        messages.append({"role": "user", "content": message})
        
        if self._mock:
            return self._mock_chat(model, message, system)
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            **kwargs
        }
        
        response = requests.post(
            f"{self.host}/api/chat",
            json=payload,
            stream=stream
        )
        response.raise_for_status()
        
        if stream:
            return self._stream_response(response)
        
        data = response.json()
        return {
            "model": model,
            "content": data.get("message", {}).get("content", ""),
            "role": "assistant",
            "created": datetime.now().isoformat()
        }
    
    def _mock_chat(self, model: str, message: str, system: Optional[str]) -> Dict[str, Any]:
        """Mock chat response."""
        return {
            "model": model,
            "content": f"[MOCK] I'm running locally on {model}. You said: {message[:50]}...",
            "role": "assistant",
            "created": datetime.now().isoformat()
        }
    
    def _stream_response(self, response) -> Generator[str, None, None]:
        """Stream response chunks."""
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                if "message" in data:
                    content = data["message"].get("content", "")
                    if content:
                        yield content
    
    # ─── Embeddings ────────────────────────────────────────────
    
    def embed(self, model: str, text: str) -> List[float]:
        """
        Generate embeddings for text.
        
        Args:
            model: Model name
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        if self._mock:
            import hashlib
            # Generate deterministic mock embedding
            h = hashlib.md5(text.encode()).hexdigest()
            return [float(int(h[i:i+8], 16)) / 0xFFFFFFFF for i in range(0, 32, 8)]
        
        response = requests.post(
            f"{self.host}/api/embeddings",
            json={"model": model, "prompt": text}
        )
        response.raise_for_status()
        
        return response.json().get("embedding", [])
    
    # ─── Generation ───────────────────────────────────────────
    
    def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text from a prompt.
        
        Args:
            model: Model name
            prompt: Input prompt
            system: System prompt
            
        Returns:
            Response dict
        """
        if self._mock:
            return {
                "model": model,
                "response": f"[MOCK] Generated by {model}: {prompt[:50]}...",
                "created": datetime.now().isoformat()
            }
        
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            **kwargs
        }
        
        response = requests.post(
            f"{self.host}/api/generate",
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        return {
            "model": model,
            "response": data.get("response", ""),
            "created": datetime.now().isoformat()
        }


# ─── CLI ──────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    
    client = OllamaClient()
    
    if len(sys.argv) < 2:
        print("Usage: python ollama.py <command> [args]")
        print("\nCommands:")
        print("  list              List models")
        print("  pull <model>      Pull model")
        print("  chat <model>      Chat with model")
        print("  embed <model>     Generate embeddings")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "list":
        models = client.list_models()
        for m in models:
            print(f"  {m['name']}")
    
    elif cmd == "pull":
        model = sys.argv[2]
        result = client.pull_model(model)
        print(json.dumps(result, indent=2))
    
    elif cmd == "chat":
        model = sys.argv[2]
        message = sys.argv[3] if len(sys.argv) > 3 else "Hello!"
        result = client.chat(model, message)
        print(result.get("content", ""))
    
    elif cmd == "embed":
        model = sys.argv[2]
        text = sys.argv[3] if len(sys.argv) > 3 else "Hello world"
        embedding = client.embed(model, text)
        print(f"Embedding length: {len(embedding)}")
