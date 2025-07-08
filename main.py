from fastapi import FastAPI
from web_scraper import EnhancedWebScraper

app = FastAPI()

@app.get("/smart-scrape")
async def smart_scrape():
    scraper = EnhancedWebScraper(delay=1)
    result = scraper.scrape_url("https://httpbin.org/html", extract_images=False)
    return {
        "title": result.get("title", "No title"),
        "length": len(result.get("page_text", "")),
        "images_found": result.get("images_found", 0)
    }

@app.get("/")
async def root():
    return {"message": "Welcome to the Smart Scraper API!"}
