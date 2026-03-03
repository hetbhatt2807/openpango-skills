#!/usr/bin/env python3
"""test_image_analyzer.py - Tests for image analyzer."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from skills.vision.image_analyzer import ImageAnalyzer, ImageNotFoundError


class TestImageAnalyzerMock(unittest.TestCase):
    """Test image analyzer in mock mode."""
    
    def setUp(self):
        """Set up test analyzer."""
        os.environ["OPENAI_API_KEY"] = ""
        self.analyzer = ImageAnalyzer()
    
    def test_mock_mode(self):
        """Test that analyzer starts in mock mode."""
        self.assertTrue(self.analyzer._mock)
    
    def test_describe_image_mock(self):
        """Test mock image description."""
        result = self.analyzer.describe_image("test.jpg", "What is this?")
        self.assertIn("content", result)
        self.assertIn("[MOCK]", result["content"])
        self.assertEqual(result["file"], "test.jpg")
    
    def test_describe_image_with_custom_prompt(self):
        """Test custom prompt."""
        result = self.analyzer.describe_image("photo.png", "Describe the colors")
        self.assertIn("prompt", result)
        self.assertEqual(result["prompt"], "Describe the colors")
    
    def test_extract_text_mock(self):
        """Test mock OCR."""
        result = self.analyzer.extract_text("document.png")
        self.assertIn("text", result)
        self.assertIn("[MOCK]", result["text"])
        self.assertEqual(result["lang"], "eng")
    
    def test_extract_text_with_lang(self):
        """Test OCR with language."""
        result = self.analyzer.extract_text("doc.png", lang="chi_sim")
        self.assertIn("lang", result)
    
    def test_analyze_chart(self):
        """Test chart analysis."""
        result = self.analyzer.analyze_chart("chart.png")
        self.assertIn("content", result)
        self.assertIn("model", result)
    
    def test_analyze_document(self):
        """Test document analysis."""
        result = self.analyzer.analyze_document("doc.png")
        self.assertIn("description", result)
        self.assertIn("text", result)
    
    def test_batch_describe(self):
        """Test batch description."""
        results = self.analyzer.batch_describe(["a.jpg", "b.jpg"], "Test")
        self.assertEqual(len(results), 2)
        for r in results:
            self.assertIn("content", r)
    
    def test_batch_ocr(self):
        """Test batch OCR."""
        results = self.analyzer.batch_ocr(["a.png", "b.png", "c.png"])
        self.assertEqual(len(results), 3)
        for r in results:
            self.assertIn("text", r)


class TestImageEncoding(unittest.TestCase):
    """Test image encoding utilities."""
    
    def setUp(self):
        """Set up test analyzer."""
        self.analyzer = ImageAnalyzer()
    
    def test_get_mime_type_jpg(self):
        """Test MIME type for JPG."""
        mime = self.analyzer._get_mime_type("test.jpg")
        self.assertEqual(mime, "image/jpeg")
    
    def test_get_mime_type_png(self):
        """Test MIME type for PNG."""
        mime = self.analyzer._get_mime_type("test.png")
        self.assertEqual(mime, "image/png")
    
    def test_get_mime_type_gif(self):
        """Test MIME type for GIF."""
        mime = self.analyzer._get_mime_type("test.gif")
        self.assertEqual(mime, "image/gif")
    
    def test_get_mime_type_webp(self):
        """Test MIME type for WebP."""
        mime = self.analyzer._get_mime_type("test.webp")
        self.assertEqual(mime, "image/webp")
    
    def test_get_mime_type_unknown(self):
        """Test MIME type for unknown extension."""
        mime = self.analyzer._get_mime_type("test.xyz")
        self.assertEqual(mime, "image/jpeg")  # default


class TestImageAnalyzerEnvironment(unittest.TestCase):
    """Test environment configuration."""
    
    def test_custom_model(self):
        """Test custom model configuration."""
        analyzer = ImageAnalyzer(model="llava")
        self.assertEqual(analyzer.model, "llava")
    
    def test_custom_base_url(self):
        """Test custom base URL."""
        analyzer = ImageAnalyzer(base_url="http://localhost:8000/v1")
        self.assertEqual(analyzer.base_url, "http://localhost:8000/v1")
    
    def test_env_model(self):
        """Test VISION_MODEL environment variable."""
        os.environ["VISION_MODEL"] = "gpt-4o-mini"
        analyzer = ImageAnalyzer()
        self.assertEqual(analyzer.model, "gpt-4o-mini")


if __name__ == "__main__":
    unittest.main()
