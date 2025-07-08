#!/usr/bin/env python3
"""
Example usage of the Enhanced Web Scraper with OCR
"""

from web_scraper import EnhancedWebScraper
import json

def scrape_single_url():
    """Example: Scrape a single URL with OCR"""
    scraper = EnhancedWebScraper(delay=2)
    
    # Example URLs to test
    urls = [
        "https://www.listcorp.com/asx/alkane-researches-limited/news/tomingley-fy2025-production-achievements-guidance-3210664.html",
        "https://example.com",  # Simple page
        # Add your own URLs here
    ]
    
    for url in urls:
        print(f"\n{'='*80}")
        print(f"Testing URL: {url}")
        print(f"{'='*80}")
        
        # Scrape with OCR enabled
        result = scraper.scrape_url(url, extract_images=True)
        
        # Print summary
        if 'error' not in result:
            print(f"\n✅ Success!")
            print(f"   Title: {result.get('title', 'No title')}")
            print(f"   Text length: {len(result.get('page_text', ''))} chars")
            print(f"   Images found: {result.get('images_found', 0)}")
            print(f"   Images with text: {len(result.get('image_texts', []))}")
            
            # Show extracted image texts
            for img_text in result.get('image_texts', []):
                print(f"   📷 {img_text['image_url'][:60]}...")
                print(f"      Text: {img_text['text'][:100]}...")
        else:
            print(f"\n❌ Error: {result.get('error', 'Unknown error')}")

def scrape_without_ocr():
    """Example: Scrape without OCR for faster processing"""
    scraper = EnhancedWebScraper(delay=1)
    
    url = "https://www.listcorp.com/asx/alkane-researches-limited/news/tomingley-fy2025-production-achievements-guidance-3210664.html"
    
    print(f"\n🚀 Fast scraping (no OCR): {url}")
    result = scraper.scrape_url(url, extract_images=False)
    
    if 'error' not in result:
        print(f"✅ Page scraped successfully!")
        print(f"   Text preview: {result['page_text'][:200]}...")

def custom_scraper_usage():
    """Example: Custom usage with different settings"""
    # Create scraper with custom delay
    scraper = EnhancedWebScraper(delay=3)
    
    # Custom URL
    url = input("Enter URL to scrape (or press Enter for default): ").strip()
    if not url:
        url = "https://www.listcorp.com/asx/alkane-researches-limited/news/tomingley-fy2025-production-achievements-guidance-3210664.html"
    
    # Ask about OCR
    use_ocr = input("Extract text from images? (y/n): ").lower().startswith('y')
    
    print(f"\n🔍 Scraping: {url}")
    print(f"📷 OCR enabled: {use_ocr}")
    
    result = scraper.scrape_url(url, extract_images=use_ocr)
    
    # Save to file
    filename = f"scrape_result_{int(time.time())}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {filename}")

if __name__ == "__main__":
    import time
    
    print("🚀 Enhanced Web Scraper Examples")
    print("=" * 50)
    
    choice = input("""
Choose an example:
1. Scrape single URL with OCR
2. Scrape without OCR (faster)
3. Custom scraping
Enter choice (1-3): """).strip()
    
    if choice == "1":
        scrape_single_url()
    elif choice == "2":
        scrape_without_ocr()
    elif choice == "3":
        custom_scraper_usage()
    else:
        print("Invalid choice. Running default example...")
        scrape_single_url()
