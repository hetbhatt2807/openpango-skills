#!/usr/bin/env python3
"""
image_analyzer.py - Computer vision and multimodal analysis.

Supports image description via GPT-4o Vision and OCR via Tesseract.
"""

import os
import base64
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger("Vision")


class VisionError(Exception):
    """Base exception for vision errors."""
    pass


class ImageNotFoundError(VisionError):
    """Image file not found."""
    pass


class OCRError(VisionError):
    """OCR processing error."""
    pass


class ImageAnalyzer:
    """
    Image analyzer with vision model and OCR support.
    
    Supports:
    - GPT-4o Vision (cloud)
    - Local vision models (via OpenAI-compatible API)
    - Tesseract OCR
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize image analyzer.
        
        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY)
            model: Vision model to use (default: gpt-4o)
            base_url: API base URL for local models
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("VISION_MODEL", "gpt-4o")
        self.base_url = base_url or os.getenv("VISION_BASE_URL", "https://api.openai.com/v1")
        self._mock = not bool(self.api_key)
        
        if self._mock:
            logger.warning("No OPENAI_API_KEY set. Running in MOCK mode.")
        
        # Try to import Tesseract
        self._tesseract_available = self._check_tesseract()
    
    def _check_tesseract(self) -> bool:
        """Check if Tesseract is available."""
        try:
            import pytesseract
            return True
        except ImportError:
            logger.warning("pytesseract not installed. OCR will use mock mode.")
            return False
    
    # ─── Image Encoding ─────────────────────────────────────────
    
    def _encode_image(self, file_path: str) -> str:
        """
        Encode image to base64.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Base64-encoded image string
        """
        path = Path(file_path)
        
        if not path.exists():
            raise ImageNotFoundError(f"Image not found: {file_path}")
        
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type from file extension."""
        ext = Path(file_path).suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
        }
        return mime_types.get(ext, "image/jpeg")
    
    # ─── Image Description ───────────────────────────────────────
    
    def describe_image(
        self,
        file_path: str,
        prompt: str = "What's in this image?",
        detail: str = "auto"
    ) -> Dict[str, Any]:
        """
        Describe an image using vision model.
        
        Args:
            file_path: Path to image file
            prompt: Description prompt
            detail: Detail level (low, high, auto)
            
        Returns:
            Description dict with content and metadata
        """
        if self._mock:
            return self._mock_describe(file_path, prompt)
        
        image_base64 = self._encode_image(file_path)
        mime_type = self._get_mime_type(file_path)
        
        try:
            import requests
        except ImportError:
            return self._mock_describe(file_path, prompt)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_base64}",
                                "detail": detail
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "content": data["choices"][0]["message"]["content"],
                "model": self.model,
                "file": file_path,
                "prompt": prompt,
                "created": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Vision API error: {e}")
            return self._mock_describe(file_path, prompt)
    
    def _mock_describe(self, file_path: str, prompt: str) -> Dict[str, Any]:
        """Mock image description."""
        return {
            "content": f"[MOCK] This is a mock description of {file_path}. "
                      f"In response to: {prompt[:50]}...",
            "model": "mock-vision",
            "file": file_path,
            "prompt": prompt,
            "created": datetime.now().isoformat()
        }
    
    # ─── OCR ───────────────────────────────────────────────────────
    
    def extract_text(
        self,
        file_path: str,
        lang: str = "eng"
    ) -> Dict[str, Any]:
        """
        Extract text from image using OCR.
        
        Args:
            file_path: Path to image file
            lang: Language code (default: eng)
            
        Returns:
            OCR result with text and metadata
        """
        if not self._tesseract_available:
            return self._mock_ocr(file_path)
        
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            return self._mock_ocr(file_path)
        
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image, lang=lang)
            
            return {
                "text": text.strip(),
                "lang": lang,
                "file": file_path,
                "char_count": len(text.strip()),
                "created": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return self._mock_ocr(file_path)
    
    def _mock_ocr(self, file_path: str) -> Dict[str, Any]:
        """Mock OCR result."""
        return {
            "text": f"[MOCK] Extracted text from {file_path}",
            "lang": "eng",
            "file": file_path,
            "char_count": 30,
            "created": datetime.now().isoformat()
        }
    
    # ─── Chart Analysis ───────────────────────────────────────────
    
    def analyze_chart(
        self,
        file_path: str,
        prompt: str = "Analyze this chart and describe its data."
    ) -> Dict[str, Any]:
        """
        Analyze a chart or graph.
        
        Args:
            file_path: Path to chart image
            prompt: Analysis prompt
            
        Returns:
            Analysis result
        """
        chart_prompt = f"""
Analyze this chart or graph. Describe:
1. Type of chart (bar, line, pie, etc.)
2. Main data points
3. Trends or patterns
4. Any notable insights

{prompt}
"""
        return self.describe_image(file_path, chart_prompt)
    
    # ─── Document Analysis ────────────────────────────────────────
    
    def analyze_document(
        self,
        file_path: str,
        extract_text: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze a document (image or PDF).
        
        Args:
            file_path: Path to document
            extract_text: Also extract text with OCR
            
        Returns:
            Document analysis result
        """
        result = {
            "file": file_path,
            "description": None,
            "text": None,
            "created": datetime.now().isoformat()
        }
        
        # Get visual description
        result["description"] = self.describe_image(
            file_path,
            "Describe this document. What type of document is it? What are the main sections?"
        )
        
        # Extract text if requested
        if extract_text:
            result["text"] = self.extract_text(file_path)
        
        return result
    
    # ─── Batch Processing ──────────────────────────────────────────
    
    def batch_describe(
        self,
        file_paths: List[str],
        prompt: str = "What's in this image?"
    ) -> List[Dict[str, Any]]:
        """
        Describe multiple images.
        
        Args:
            file_paths: List of image paths
            prompt: Description prompt
            
        Returns:
            List of description results
        """
        return [self.describe_image(fp, prompt) for fp in file_paths]
    
    def batch_ocr(
        self,
        file_paths: List[str],
        lang: str = "eng"
    ) -> List[Dict[str, Any]]:
        """
        Extract text from multiple images.
        
        Args:
            file_paths: List of image paths
            lang: Language code
            
        Returns:
            List of OCR results
        """
        return [self.extract_text(fp, lang) for fp in file_paths]


# ─── CLI ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    
    analyzer = ImageAnalyzer()
    
    if len(sys.argv) < 2:
        print("Usage: python image_analyzer.py <command> [args]")
        print("\nCommands:")
        print("  describe <image> [prompt]  Describe an image")
        print("  ocr <image>                Extract text with OCR")
        print("  chart <image>              Analyze a chart")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "describe":
        file_path = sys.argv[2]
        prompt = sys.argv[3] if len(sys.argv) > 3 else "What's in this image?"
        result = analyzer.describe_image(file_path, prompt)
        print(result.get("content", ""))
    
    elif cmd == "ocr":
        file_path = sys.argv[2]
        result = analyzer.extract_text(file_path)
        print(result.get("text", ""))
    
    elif cmd == "chart":
        file_path = sys.argv[2]
        result = analyzer.analyze_chart(file_path)
        print(result.get("content", ""))
