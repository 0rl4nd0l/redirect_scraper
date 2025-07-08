#!/usr/bin/env python3
"""
Enhanced Web Scraper with OCR Text Extraction for Assistant Bridge
Scrapes web pages and extracts text from images (JPG, PNG, etc.)
"""

import requests
from bs4 import BeautifulSoup
from PIL import Image
import pytesseract
from io import BytesIO
import re
from urllib.parse import urljoin, urlparse, unquote
import time
import json
from datetime import datetime
import base64

class EnhancedWebScraper:
    def __init__(self, delay=2):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
    def is_image_url(self, url):
        """Check if URL points to an image file"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
        return any(url.lower().endswith(ext) for ext in image_extensions)
        
    def resolve_redirect(self, url):
        """Resolve redirect to find the clean URL"""
        try:
            if 'track/click' in url:
                print(f"🔍 Detected tracking URL, attempting to decode...")
                parsed_url = urlparse(url)
                
                # Parse query parameters properly
                from urllib.parse import parse_qs
                params = parse_qs(parsed_url.query)
                encoded_data = params.get('p', [None])[0]

                if encoded_data:
                    # Attempt to decode base64
                    try:
                        decoded_data = base64.b64decode(encoded_data + '==').decode('utf-8')

                        print(f"📝 Decoded JSON candidate: {decoded_data[:200]}...")
                        
                        # Attempt to parse JSON
                        data = json.loads(decoded_data)

                        # Extract the actual URL
                        clean_url = data.get('url', url)
                        return unquote(clean_url)

                    except (base64.binascii.Error, json.JSONDecodeError, KeyError) as decode_error:
                        print(f"❌ Error decoding redirect: {decode_error}")
                        return url

                else:
                    print("⚠️ No track parameter found to decode.")
                    return url
            return url

        except Exception as e:
            print(f"❌ Error resolving redirect: {e}")
            return url
    def extract_text_from_image(self, image_url, base_url):
        """Extract text from an image using OCR"""
        try:
            print(f"  📷 Processing image: {image_url}")
            
            # Download image
            response = self.session.get(image_url, timeout=15)
            response.raise_for_status()
            
            # Open and process image
            img = Image.open(BytesIO(response.content))
            
            # Convert to RGB if necessary
            if img.mode not in ['RGB', 'L']:
                img = img.convert('RGB')
            
            # Extract text using OCR
            text = pytesseract.image_to_string(img, config='--psm 6')
            
            # Clean up extracted text
            cleaned_text = re.sub(r'\s+', ' ', text).strip()
            
            if cleaned_text and len(cleaned_text) > 3:
                return cleaned_text
            else:
                return None
                
        except Exception as e:
            print(f"    ❌ Error processing image: {e}")
            return None
    
    def find_images_on_page(self, soup, page_url):
        """Find all images on a page and return their URLs"""
        images = []
        base_domain = urlparse(page_url).netloc
        
        for img_tag in soup.find_all('img', src=True):
            src = img_tag.get('src')
            if src:
                # Convert relative URLs to absolute
                full_url = urljoin(page_url, src)
                
                # Only include images from the same domain or allow external if needed
                if self.is_image_url(full_url):
                    images.append(full_url)
        
        return list(set(images))  # Remove duplicates
    
    def scrape_url(self, url, extract_images=True):
        """Scrape a single URL for text and optionally extract text from images"""
        print(f"\n🔍 Scraping: {url}")
        print("-" * 80)
        
        try:
            clean_url = self.resolve_redirect(url)
            print(f"🔗 Resolved Clean URL: {clean_url}")

            # Get page content with better headers
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = self.session.get(clean_url, headers=headers, allow_redirects=True, timeout=15)
            response.raise_for_status()
            
            print(f"✅ Status code: {response.status_code}")
            print(f"🔗 Final URL: {response.url}")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract page title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "No title"
            print(f"📄 Page Title: {title_text}")
            
            # Extract visible page text
            for script in soup(['script', 'style', 'meta', 'link']):
                script.decompose()
            
            page_text = soup.get_text(separator=' ')
            clean_text = re.sub(r'\s+', ' ', page_text).strip()
            
            print(f"\n📝 Page Text ({len(clean_text)} chars):")
            print(clean_text[:1000] + "..." if len(clean_text) > 1000 else clean_text)
            
            result = {
                'url': str(response.url),
                'status_code': response.status_code,
                'title': title_text,
                'page_text': clean_text,
                'timestamp': datetime.now().isoformat(),
                'images_found': 0,
                'image_texts': []
            }
            
            # Process images if requested
            if extract_images:
                images = self.find_images_on_page(soup, str(response.url))
                result['images_found'] = len(images)
                
                if images:
                    print(f"\n🖼️  Found {len(images)} image(s) to analyze:")
                    
                    for i, img_url in enumerate(images[:10], 1):  # Limit to first 10 images
                        print(f"\n  Image {i}/{min(len(images), 10)}:")
                        
                        # Extract text from image
                        ocr_text = self.extract_text_from_image(img_url, str(response.url))
                        
                        if ocr_text:
                            print(f"  ✅ OCR Text: {ocr_text}")
                            result['image_texts'].append({
                                'image_url': img_url,
                                'text': ocr_text
                            })
                        else:
                            print(f"  ⚪ No readable text found")
                        
                        # Be respectful to the server
                        time.sleep(1)
                else:
                    print("\n🖼️  No images found on this page")
            
            return result
            
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
            return {
                'url': url,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

def check_tesseract_available():
    """Check if Tesseract is available"""
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False

def main():
    """Main function for testing"""
    # Check if Tesseract is available
    if check_tesseract_available():
        print("✅ Tesseract OCR is available")
    else:
        print("⚠️  Tesseract OCR not found - OCR features will be disabled")
        print("On Railway: This is expected - OCR requires system dependencies")
        print("Locally: Install with 'brew install tesseract'")
    
    # Example usage
    scraper = EnhancedWebScraper(delay=2)
    
    # Test URL - original ListCorp URL
    test_url = "https://www.listcorp.com/asx/alkane-researches-limited/news/tomingley-fy2025-production-achievements-guidance-3210664.html"
    
    print(f"🚀 Enhanced Web Scraper with OCR")
    print(f"🎯 Target URL: {test_url}")
    print("=" * 80)
    
    # Scrape the URL
    result = scraper.scrape_url(test_url, extract_images=True)
    
    # Save result to JSON file
    output_file = "scrape_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # Summary
    if 'error' not in result:
        print(f"\n📊 Summary:")
        print(f"   Status: {result.get('status_code', 'Unknown')}")
        print(f"   Page text length: {len(result.get('page_text', ''))} chars")
        print(f"   Images found: {result.get('images_found', 0)}")
        print(f"   Images with text: {len(result.get('image_texts', []))}")

if __name__ == "__main__":
    main()

