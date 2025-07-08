# Assistant Bridge Repository - Enhanced Web Scraper

## Overview
This repository contains an enhanced web scraper with OCR (Optical Character Recognition) capabilities that can:
- 🔗 Scrape web pages and extract text content
- 🖼️ Find and download images from web pages  
- 📝 Extract text from images (JPG, PNG, GIF, WebP, etc.) using Tesseract OCR
- 💾 Save results in structured JSON format
- 🎯 Handle both single URLs and multiple pages

## Files

### Core Components
- **`web_scraper.py`** - Main enhanced scraper with OCR capabilities
- **`example_usage.py`** - Examples showing different usage patterns
- **`fetch_data.py`** - API data fetching (existing)
- **`bridge_runner.py`** - OpenAI integration bridge (existing)

### Configuration
- **`requirements.txt`** - Python dependencies
- **`README.md`** - This documentation

## Installation

### 1. Install Tesseract OCR
```bash
brew install tesseract
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

Dependencies include:
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `pytesseract` - OCR wrapper
- `Pillow` - Image processing
- `openai` - OpenAI API integration

## Usage

### Basic Usage

```python
from web_scraper import EnhancedWebScraper

# Create scraper
scraper = EnhancedWebScraper(delay=2)

# Scrape a URL with OCR
result = scraper.scrape_url("https://example.com", extract_images=True)

# Access results
print(f"Title: {result['title']}")
print(f"Page text: {result['page_text']}")
print(f"Images found: {result['images_found']}")

# Check for extracted image text
for img_text in result['image_texts']:
    print(f"Image: {img_text['image_url']}")
    print(f"Text: {img_text['text']}")
```

### Run Examples

```bash
# Interactive examples
python example_usage.py

# Direct execution (tests original ListCorp URL)
python web_scraper.py
```

### Advanced Usage

```python
# Scrape without OCR (faster)
result = scraper.scrape_url(url, extract_images=False)

# Custom delay between requests
scraper = EnhancedWebScraper(delay=5)

# Process multiple URLs
urls = ["https://site1.com", "https://site2.com"]
for url in urls:
    result = scraper.scrape_url(url)
```

## Output Format

The scraper returns a structured dictionary:

```json
{
  "url": "https://example.com",
  "status_code": 200,
  "title": "Page Title",
  "page_text": "Full page text content...",
  "timestamp": "2025-07-08T08:13:41.123456",
  "images_found": 5,
  "image_texts": [
    {
      "image_url": "https://example.com/image1.jpg",
      "text": "Text extracted from image"
    }
  ]
}
```

## Features

### ✅ Enhanced Capabilities
- **OCR Text Extraction** - Reads text from JPG, PNG, GIF, WebP images
- **Smart Image Detection** - Automatically finds all images on pages
- **URL Handling** - Converts relative URLs to absolute
- **Error Handling** - Graceful failure with detailed error messages
- **Rate Limiting** - Configurable delays to respect servers
- **JSON Output** - Structured data for easy processing

### ✅ Original Features Preserved
- **API Integration** - Existing `fetch_data.py` and `bridge_runner.py` 
- **OpenAI Bridge** - Connect scraped data to OpenAI tools
- **ListCorp Support** - Still works with original target URL

## Example Scenarios

### 1. Financial News Scraping
```python
# Original use case - financial articles
url = "https://www.listcorp.com/asx/company/news/article.html"
result = scraper.scrape_url(url, extract_images=True)
```

### 2. Technical Documentation
```python
# Extract text from diagrams and charts
url = "https://docs.example.com/technical-guide"
result = scraper.scrape_url(url, extract_images=True)
```

### 3. Product Information
```python
# Get product details including image text
url = "https://store.example.com/product/123"
result = scraper.scrape_url(url, extract_images=True)
```

## Error Handling

The scraper handles various error conditions:
- Network timeouts and connection errors
- Invalid image formats
- OCR processing failures
- Missing Tesseract installation

If Tesseract is not installed, the scraper will still work but skip image text extraction.

## Performance Considerations

- **With OCR**: Slower due to image processing (recommended delay: 2-3 seconds)
- **Without OCR**: Fast page scraping only (recommended delay: 1 second)
- **Image Limit**: Processes up to 10 images per page by default
- **Memory**: Large images may require more memory for OCR processing

## Troubleshooting

### Tesseract Not Found
```bash
# Install Tesseract
brew install tesseract

# Verify installation
tesseract --version
```

### Import Errors
```bash
# Install missing dependencies
pip install -r requirements.txt
```

### Network Issues
- Check internet connection
- Verify URLs are accessible
- Some sites may block automated requests

## Integration with OpenAI Bridge

The scraped data can be passed to the OpenAI bridge (`bridge_runner.py`) for further processing:

```python
# Scrape data
result = scraper.scrape_url(url, extract_images=True)

# Pass to OpenAI for analysis
# (Integration code would go here)
```

## Backward Compatibility

The enhanced scraper maintains compatibility with existing code while adding new OCR capabilities. Existing scripts using the original `web_scraper.py` functionality will continue to work.
