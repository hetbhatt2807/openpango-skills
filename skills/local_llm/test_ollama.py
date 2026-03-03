#!/usr/bin/env python3
"""test_ollama.py - Tests for Ollama integration."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from skills.local_llm.ollama import OllamaClient, OllamaError


class TestOllamaClientMock(unittest.TestCase):
    """Test Ollama client in mock mode."""
    
    def setUp(self):
        """Set up test client."""
        os.environ["OLLAMA_HOST"] = "http://nonexistent:11434"
        self.client = OllamaClient()
    
    def test_mock_mode(self):
        """Test that client starts in mock mode."""
        self.assertTrue(self.client._mock)
    
    def test_list_models(self):
        """Test listing models."""
        models = self.client.list_models()
        self.assertIsInstance(models, list)
        self.assertGreater(len(models), 0)
        self.assertIn("name", models[0])
    
    def test_chat(self):
        """Test chat completion."""
        result = self.client.chat("llama3", "Hello!")
        self.assertIn("model", result)
        self.assertIn("content", result)
        self.assertEqual(result["model"], "llama3")
        self.assertIn("[MOCK]", result["content"])
    
    def test_chat_with_system(self):
        """Test chat with system prompt."""
        result = self.client.chat(
            "llama3",
            "Hello!",
            system="You are a helpful assistant."
        )
        self.assertIn("content", result)
    
    def test_chat_with_history(self):
        """Test chat with history."""
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"}
        ]
        result = self.client.chat("llama3", "How are you?", history=history)
        self.assertIn("content", result)
    
    def test_embed(self):
        """Test embedding generation."""
        embedding = self.client.embed("llama3", "Hello world")
        self.assertIsInstance(embedding, list)
        self.assertEqual(len(embedding), 4)  # Mock returns 4 floats
    
    def test_generate(self):
        """Test text generation."""
        result = self.client.generate("llama3", "Once upon a time")
        self.assertIn("model", result)
        self.assertIn("response", result)
        self.assertIn("[MOCK]", result["response"])
    
    def test_pull_model(self):
        """Test model pull."""
        result = self.client.pull_model("llama3")
        self.assertEqual(result["status"], "success")


class TestOllamaClientEnvironment(unittest.TestCase):
    """Test environment variable configuration."""
    
    def test_custom_host(self):
        """Test custom host configuration."""
        client = OllamaClient(host="http://custom:8080")
        self.assertEqual(client.host, "http://custom:8080")
    
    def test_env_host(self):
        """Test OLLAMA_HOST environment variable."""
        os.environ["OLLAMA_HOST"] = "http://env-host:11434"
        client = OllamaClient()
        self.assertEqual(client.host, "http://env-host:11434")


if __name__ == "__main__":
    unittest.main()
