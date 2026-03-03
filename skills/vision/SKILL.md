---
name: vision
description: "Computer vision and multimodal skill for image analysis, OCR, and document processing."
version: "1.0.0"
user-invocable: true
metadata:
  capabilities:
    - vision/describe
    - vision/ocr
    - vision/analyze
  author: "OpenPango Contributor"
  license: "MIT"
---

# Computer Vision & Multimodal Skill

Analyze images, charts, and documents with vision-capable models.

## Features

- **Image Description**: Describe images using GPT-4o Vision or local models
- **OCR**: Extract text from images using Tesseract
- **Document Analysis**: Process PDFs and images
- **Base64 Encoding**: Automatic image encoding for API calls

## Configuration

| Environment Variable | Description |
|---------------------|-------------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o Vision |
| `VISION_MODEL` | Vision model to use (default: gpt-4o) |
| `TESSERACT_PATH` | Path to Tesseract binary (optional) |

## Usage

```python
from skills.vision.image_analyzer import ImageAnalyzer

analyzer = ImageAnalyzer()

# Describe an image
description = analyzer.describe_image("photo.jpg", "What's in this image?")

# Extract text with OCR
text = analyzer.extract_text("document.png")

# Analyze a chart
chart_data = analyzer.analyze_chart("chart.png")
```
