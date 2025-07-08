#!/usr/bin/env python3
"""
Debug script to test image detection and OCR capabilities
"""

import requests
from bs4 import BeautifulSoup
from PIL import Image
import pytesseract
from io import BytesIO
import re
from urllib.parse import urljoin, urlparse
import json

def debug_image_detection(url):
    """Debug image detection on a specific URL"""
    print(f"🔍 Debugging image detection for: {url}")
    print("=" * 80)
    
    try:
        # Get page content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        print(f"✅ Page loaded successfully (Status: {response.status_code})")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all img tags
        img_tags = soup.find_all('img')
        print(f"\n📷 Found {len(img_tags)} <img> tags total")
        
        images_with_src = []
        for i, img in enumerate(img_tags, 1):
            src = img.get('src')
            alt = img.get('alt', 'No alt text')
            
            print(f"\n  Image {i}:")
            print(f"    src: {src}")
            print(f"    alt: {alt}")
            
            if src:
                full_url = urljoin(url, src)
                print(f"    full URL: {full_url}")
                
                # Check if it's a valid image URL
                image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
                is_image = any(full_url.lower().endswith(ext) for ext in image_extensions)
                print(f"    is image URL: {is_image}")
                
                if is_image:
                    images_with_src.append({
                        'url': full_url,
                        'alt': alt,
                        'original_src': src
                    })
        
        print(f"\n🎯 Valid image URLs found: {len(images_with_src)}")
        
        # Test OCR on each image
        for i, img_info in enumerate(images_with_src, 1):
            print(f"\n📖 Testing OCR on image {i}: {img_info['url']}")
            try:
                # Download image
                img_response = requests.get(img_info['url'], headers=headers, timeout=15)
                img_response.raise_for_status()
                
                print(f"  ✅ Image downloaded ({len(img_response.content)} bytes)")
                
                # Open image
                img = Image.open(BytesIO(img_response.content))
                print(f"  📏 Image size: {img.size}, mode: {img.mode}")
                
                # Convert to RGB if necessary
                if img.mode not in ['RGB', 'L']:
                    img = img.convert('RGB')
                    print(f"  🔄 Converted to RGB mode")
                
                # Try OCR with different configurations
                configs = [
                    '--psm 6',
                    '--psm 3',
                    '--psm 8',
                    '--psm 13'
                ]
                
                for config in configs:
                    try:
                        text = pytesseract.image_to_string(img, config=config)
                        cleaned_text = re.sub(r'\s+', ' ', text).strip()
                        
                        if cleaned_text and len(cleaned_text) > 3:
                            print(f"  ✅ OCR success (config: {config}): {cleaned_text[:100]}...")
                            break
                        else:
                            print(f"  ⚪ No text found (config: {config})")
                    except Exception as ocr_error:
                        print(f"  ❌ OCR failed (config: {config}): {ocr_error}")
                else:
                    print(f"  ❌ No readable text found with any OCR configuration")
                
            except Exception as e:
                print(f"  ❌ Error processing image: {e}")
        
        return images_with_src
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def main():
    # Test with a URL that you know has images
    test_url = input("Enter the URL to test (or press Enter for default): ").strip()
    
    if not test_url:
        test_url = "https://example.com"  # Default test URL
    
    debug_image_detection(test_url)

if __name__ == "__main__":
    main()
