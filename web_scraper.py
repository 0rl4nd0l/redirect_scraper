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
import asyncio
from playwright.async_api import async_playwright

class EnhancedWebScraper:
    def __init__(self, delay=2, use_playwright=False):
        self.delay = delay
        self.use_playwright = use_playwright
        self.session = requests.Session()
        
        # More comprehensive browser headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        })
        
    async def fetch_with_playwright(self, url):
        """Fetch page content using a headless browser with Playwright."""
        print(f"  🤖 Using Playwright to fetch JavaScript-rendered content...")
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--no-first-run',
                        '--no-zygote',
                        '--disable-gpu'
                    ]
                )
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    locale='en-US'
                )
                page = await context.new_page()
                
                # Set additional realistic properties to avoid bot detection
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                """)
                
                # Navigate and wait for content to load
                await page.goto(url, wait_until='networkidle', timeout=30000)
                
                # Wait a bit more for any late-loading content
                await asyncio.sleep(3)
                
                # Get the final URL after any redirects
                final_url = page.url
                
                # Get the rendered HTML content
                content = await page.content()
                
                await browser.close()
                
                print(f"  ✅ Playwright fetch successful! Content length: {len(content)} chars")
                return content, final_url
                
        except Exception as e:
            print(f"  ❌ Playwright fetch failed: {e}")
            return None, None

    def is_image_url(self, url):
        """Check if URL points to an image file"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg']
        
        # Remove query parameters and fragments to check the actual file extension
        from urllib.parse import urlparse
        parsed = urlparse(url.lower())
        path = parsed.path
        
        # Check if path ends with image extension
        for ext in image_extensions:
            if path.endswith(ext):
                return True
        
        # Also check the full URL (for legacy compatibility)
        return any(url.lower().endswith(ext) for ext in image_extensions)
    
    def could_be_image(self, url):
        """Check if URL could be an image (more permissive check)"""
        # Some images might not have extensions or have query parameters
        url_lower = url.lower()
        
        # Skip obvious non-images
        skip_patterns = ['javascript:', 'data:text', '.css', '.js', '.html', '.php']
        if any(pattern in url_lower for pattern in skip_patterns):
            return False
        
        # Include data URIs that start with image
        if url_lower.startswith('data:image/'):
            return True
            
        # Include URLs that might be images but don't have clear extensions
        image_indicators = ['image', 'img', 'photo', 'picture', 'thumbnail', 'avatar', 'resizer', 'cdn']
        if any(indicator in url_lower for indicator in image_indicators):
            return True
            
        # Check for common image service patterns
        image_service_patterns = ['/resizer/', '/resize/', '/thumb/', '/media/', '/assets/images/']
        if any(pattern in url_lower for pattern in image_service_patterns):
            return True
            
        return False
    
    def try_multiple_strategies(self, url):
        """Try multiple strategies to access blocked content"""
        strategies = [
            {
                'name': 'Standard Browser',
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'cross-site',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0'
                }
            },
            {
                'name': 'Mobile Safari',
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate'
                }
            },
            {
                'name': 'Firefox',
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
            }
        ]
        
        best_response = None
        best_length = 0
        
        for strategy in strategies:
            try:
                print(f"  🔄 Trying {strategy['name']}...")
                response = self.session.get(url, headers=strategy['headers'], timeout=15, allow_redirects=True)
                
                # Check if this response is better (longer content, not an error page)
                is_error_page = (
                    response.status_code == 403 or
                    'cloudfront' in response.text.lower() or
                    'request could not be satisfied' in response.text.lower() or
                    'access denied' in response.text.lower()
                )
                
                if not is_error_page and len(response.text) > best_length:
                    best_response = response
                    best_length = len(response.text)
                    print(f"    ✅ {strategy['name']} worked! Got {len(response.text)} chars")
                else:
                    print(f"    ❌ {strategy['name']} blocked or minimal content")
                    
                time.sleep(1)  # Be respectful between attempts
                
            except Exception as e:
                print(f"    ❌ {strategy['name']} failed: {e}")
                
        return best_response
        
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
        
        # Look for img tags with src
        img_tags = soup.find_all('img')
        print(f"  🔍 Found {len(img_tags)} <img> tags total")
        
        for i, img_tag in enumerate(img_tags, 1):
            src = img_tag.get('src')
            data_src = img_tag.get('data-src')  # Lazy loading
            srcset = img_tag.get('srcset')  # Responsive images
            
            print(f"    Image {i}: src='{src}', data-src='{data_src}', srcset='{srcset}'")
            
            # Try different src attributes
            potential_srcs = [src, data_src]
            
            # Parse srcset if available
            if srcset:
                srcset_urls = [url.strip().split()[0] for url in srcset.split(',')]
                potential_srcs.extend(srcset_urls)
            
            for potential_src in potential_srcs:
                if potential_src:
                    # Convert relative URLs to absolute
                    full_url = urljoin(page_url, potential_src)
                    
                    # Check if it's a valid image URL (more permissive)
                    if self.is_image_url(full_url) or self.could_be_image(full_url):
                        images.append(full_url)
                        print(f"      ✅ Added: {full_url}")
                    else:
                        print(f"      ❌ Skipped (not image): {full_url}")
        
        # Also look for CSS background images
        for element in soup.find_all(style=True):
            style = element.get('style', '')
            if 'background-image' in style:
                import re
                matches = re.findall(r'background-image:\s*url\(["\']?([^"\')]+)["\']?\)', style)
                for match in matches:
                    full_url = urljoin(page_url, match)
                    if self.is_image_url(full_url) or self.could_be_image(full_url):
                        images.append(full_url)
                        print(f"      ✅ Added CSS background: {full_url}")
        
        unique_images = list(set(images))  # Remove duplicates
        print(f"  📷 Total unique images found: {len(unique_images)}")
        return unique_images
    
    def find_meta_images(self, soup, page_url):
        """Find images from OpenGraph and meta tags"""
        images = []
        
        print(f"  🔍 Searching for meta images...")
        
        # OpenGraph image (multiple attribute styles)
        og_selectors = [
            ('meta', {'property': 'og:image'}),
            ('meta', {'property': 'og:image:url'}),
            ('meta', {'name': 'og:image'})
        ]
        
        for tag, attrs in og_selectors:
            og_image = soup.find(tag, attrs)
            if og_image and og_image.get('content'):
                img_url = urljoin(page_url, og_image['content'])
                if self.is_image_url(img_url) or self.could_be_image(img_url):
                    images.append(img_url)
                    print(f"      ✅ Added OpenGraph image: {img_url}")
        
        # Twitter card images
        twitter_selectors = [
            ('meta', {'name': 'twitter:image'}),
            ('meta', {'name': 'twitter:image:src'}),
            ('meta', {'property': 'twitter:image'})
        ]
        
        for tag, attrs in twitter_selectors:
            twitter_image = soup.find(tag, attrs)
            if twitter_image and twitter_image.get('content'):
                img_url = urljoin(page_url, twitter_image['content'])
                if self.is_image_url(img_url) or self.could_be_image(img_url):
                    images.append(img_url)
                    print(f"      ✅ Added Twitter image: {img_url}")
        
        # Generic meta images
        meta_selectors = [
            ('meta', {'name': 'image'}),
            ('meta', {'name': 'thumbnail'}),
            ('meta', {'property': 'image'})
        ]
        
        for tag, attrs in meta_selectors:
            meta_images = soup.find_all(tag, attrs)
            for meta in meta_images:
                if meta.get('content'):
                    img_url = urljoin(page_url, meta['content'])
                    if self.is_image_url(img_url) or self.could_be_image(img_url):
                        images.append(img_url)
                        print(f"      ✅ Added meta image: {img_url}")
        
        # Look for any meta tag with image-like content
        all_metas = soup.find_all('meta')
        for meta in all_metas:
            content = meta.get('content', '')
            if content and (self.is_image_url(content) or self.could_be_image(content)):
                img_url = urljoin(page_url, content)
                if img_url not in images:  # Avoid duplicates
                    images.append(img_url)
                    print(f"      ✅ Added discovered meta image: {img_url}")
        
        print(f"  📷 Meta images found: {len(images)}")
        return images
    
    async def scrape_url(self, url, extract_images=True, force_playwright=False):
        """Scrape a single URL for text and optionally extract text from images"""
        print(f"\n🔍 Scraping: {url}")
        print("-" * 80)
        
        try:
            clean_url = self.resolve_redirect(url)
            print(f"🔗 Resolved Clean URL: {clean_url}")

            # Determine if we should use Playwright
            should_use_playwright = (
                self.use_playwright or 
                force_playwright or 
                'listcorp.com' in clean_url.lower()  # Known JavaScript-heavy site
            )
            
            if should_use_playwright:
                # Use Playwright for JavaScript-heavy sites
                content, final_url = await self.fetch_with_playwright(clean_url)
                
                if content:
                    soup = BeautifulSoup(content, 'html.parser')
                    status_code = 200  # Playwright successful
                    final_url = final_url or clean_url
                    print(f"✅ Status code: {status_code} (Playwright)")
                    print(f"🔗 Final URL: {final_url}")
                else:
                    # Fallback to traditional scraping if Playwright fails
                    print("🔄 Playwright failed, falling back to traditional scraping...")
                    should_use_playwright = False
            
            if not should_use_playwright or not content:
                # Traditional scraping approach
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0',
                    'DNT': '1'
                }
                
                response = self.session.get(clean_url, headers=headers, allow_redirects=True, timeout=15)
                
                status_code = response.status_code
                final_url = str(response.url)
                print(f"✅ Status code: {status_code}")
                print(f"🔗 Final URL: {final_url}")
                
                # Check for CloudFront blocking or error pages
                is_blocked = (
                    response.status_code == 403 or 
                    'cloudfront' in response.text.lower() or 
                    'request could not be satisfied' in response.text.lower() or
                    'access denied' in response.text.lower() or
                    len(response.text) < 500  # Threshold for minimal content
                )
                
                if is_blocked:
                    print(f"⚠️  Detected blocking/error page ({len(response.text)} chars). Trying multiple strategies...")
                    
                    # Try multiple strategies to bypass blocking
                    alt_response = self.try_multiple_strategies(clean_url)
                    
                    if alt_response and len(alt_response.text) > len(response.text):
                        print(f"✅ Multi-strategy approach successful! Using best response.")
                        response = alt_response
                    else:
                        print(f"🔴 All strategies blocked. Content may be JavaScript-rendered.")
                        print(f"💡 Consider setting force_playwright=True or use_playwright=True")
                
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
                'url': final_url,
                'status_code': status_code,
                'title': title_text,
                'page_text': clean_text,
                'timestamp': datetime.now().isoformat(),
                'images_found': 0,
                'image_texts': [],
                'method': 'playwright' if should_use_playwright and content else 'traditional'
            }
            
            # Process images if requested
            if extract_images:
                # Find images in the HTML
                images = self.find_images_on_page(soup, final_url)
                
                # Also check OpenGraph and meta tags for images
                meta_images = self.find_meta_images(soup, final_url)
                
                # Combine all images
                all_images = list(set(images + meta_images))
                result['images_found'] = len(all_images)
                
                if all_images:
                    print(f"\n🖼️  Found {len(all_images)} image(s) to analyze:")
                    
                    for i, img_url in enumerate(all_images[:10], 1):  # Limit to first 10 images
                        print(f"\n  Image {i}/{min(len(all_images), 10)}:")
                        
                        # Extract text from image
                        ocr_text = self.extract_text_from_image(img_url, final_url)
                        
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

