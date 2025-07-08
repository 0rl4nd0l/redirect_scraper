from fastapi import FastAPI, Query, HTTPException
from web_scraper import EnhancedWebScraper, check_tesseract_available
from pydantic import BaseModel
from typing import Optional
import json

app = FastAPI(
    title="Smart Scraper with OCR",
    description="Web scraper that can extract text from web pages and images using OCR",
    version="1.0.0"
)

class ScrapeRequest(BaseModel):
    url: str
    extract_images: bool = True
    delay: int = 2

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Smart Scraper API with OCR!",
        "endpoints": {
            "/smart-scrape": "GET - Scrape a URL with optional OCR",
            "/health": "GET - Health check",
            "/ocr-status": "GET - Check OCR availability"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "ocr_available": check_tesseract_available()
    }

@app.get("/ocr-status")
async def ocr_status():
    return {
        "ocr_available": check_tesseract_available(),
        "message": "OCR is available" if check_tesseract_available() else "OCR not available"
    }

@app.get("/smart-scrape")
async def smart_scrape(
    url: str = Query(default="https://httpbin.org/html", description="URL to scrape"),
    extract_images: bool = Query(default=True, description="Whether to extract text from images"),
    delay: int = Query(default=2, description="Delay between requests in seconds")
):
    """Scrape a URL and optionally extract text from images using OCR"""
    try:
        scraper = EnhancedWebScraper(delay=delay)
        result = scraper.scrape_url(url, extract_images=extract_images)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "url": result.get("url"),
            "title": result.get("title", "No title"),
            "text_length": len(result.get("page_text", "")),
            "page_text_preview": result.get("page_text", "")[:500],
            "images_found": result.get("images_found", 0),
            "images_with_text": len(result.get("image_texts", [])),
            "image_texts": result.get("image_texts", []),
            "timestamp": result.get("timestamp")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/smart-scrape")
async def smart_scrape_post(request: ScrapeRequest):
    """POST version of smart-scrape for complex requests"""
    try:
        scraper = EnhancedWebScraper(delay=request.delay)
        result = scraper.scrape_url(request.url, extract_images=request.extract_images)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "url": result.get("url"),
            "title": result.get("title", "No title"),
            "text_length": len(result.get("page_text", "")),
            "full_page_text": result.get("page_text", ""),
            "images_found": result.get("images_found", 0),
            "images_with_text": len(result.get("image_texts", [])),
            "image_texts": result.get("image_texts", []),
            "timestamp": result.get("timestamp")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
