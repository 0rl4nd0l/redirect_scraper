#!/usr/bin/env python3
"""
Test the enhanced web scraper with Playwright on ListCorp URL
"""

import asyncio
import json
from web_scraper import EnhancedWebScraper

async def test_listcorp_scraping():
    """Test the enhanced scraper on the problematic ListCorp URL"""
    
    # The ListCorp URL that was problematic
    test_url = "https://www.listcorp.com/asx/alk/alkane-resources-limited/news/tomingley-fy2025-production-achieves-guidance-3210664.html?utm_medium=email&utm_source=transactional&utm_campaign=release_end_of_day_summary_1"
    
    print("🚀 Testing Enhanced Web Scraper with Playwright")
    print("=" * 80)
    print(f"🎯 Target URL: {test_url}")
    print("=" * 80)
    
    # Initialize scraper with Playwright enabled for ListCorp
    scraper = EnhancedWebScraper(delay=2, use_playwright=True)
    
    try:
        # Test the scraper with Playwright
        print("\n🤖 Testing with Playwright (should automatically detect ListCorp)...")
        result = await scraper.scrape_url(test_url, extract_images=True)
        
        # Save result to JSON file
        output_file = "playwright_scrape_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {output_file}")
        
        # Display summary
        if 'error' not in result:
            print(f"\n📊 RESULTS SUMMARY:")
            print(f"   Method Used: {result.get('method', 'unknown')}")
            print(f"   Status Code: {result.get('status_code', 'Unknown')}")
            print(f"   Page Title: {result.get('title', 'No title')[:100]}...")
            print(f"   Page Text Length: {len(result.get('page_text', ''))} characters")
            print(f"   Images Found: {result.get('images_found', 0)}")
            print(f"   Images with OCR Text: {len(result.get('image_texts', []))}")
            
            # Show first 500 characters of extracted text
            page_text = result.get('page_text', '')
            print(f"\n📝 EXTRACTED TEXT (first 500 chars):")
            print("-" * 50)
            print(page_text[:500] + "..." if len(page_text) > 500 else page_text)
            print("-" * 50)
            
            # Show any OCR results
            if result.get('image_texts'):
                print(f"\n🖼️ OCR RESULTS:")
                for i, img_text in enumerate(result['image_texts'][:3], 1):
                    print(f"  Image {i}: {img_text['text'][:100]}...")
        else:
            print(f"\n❌ ERROR: {result.get('error')}")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_listcorp_scraping())
