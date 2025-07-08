from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import httpx
import logging
import time
import random
import urllib3
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional

# Disable SSL warnings for stealth mode
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = FastAPI(
    title="Redirect Scraper", 
    version="1.0.0",
    description="A comprehensive URL redirect scraper with HTTP integration",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for Make.com and other external integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify Make.com domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enhanced headers configuration with anti-bot detection
def get_headers(user_agent: Optional[str] = None, auth_token: Optional[str] = None, referer: Optional[str] = None) -> dict:
    # Rotate through different realistic User-Agent strings
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    
    import random
    selected_ua = user_agent or random.choice(user_agents)
    
    headers = {
        'User-Agent': selected_ua,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9,es;q=0.8,fr;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'DNT': '1',
    }
    
    # Add referer if provided, otherwise use Google as default
    if referer:
        headers['Referer'] = referer
    elif 'listcorp.com' in (user_agent or ''):
        headers['Referer'] = 'https://www.google.com/search?q=listcorp'
    else:
        headers['Referer'] = 'https://www.google.com/'
    
    if auth_token:
        headers['Authorization'] = f'Bearer {auth_token}'
    
    return headers

# Enhanced session with connection pooling and retries
def create_http_session() -> requests.Session:
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=20, pool_maxsize=20)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class URLResponse(BaseModel):
    final_url: str
    status_code: int
    content_type: str
    content_length: Optional[int]
    redirect_count: int
    response_time: float
    headers: dict
    content_preview: Optional[str] = None

# Smart URL endpoint that detects and handles both HTML and PDF content
@app.get("/smart-scrape")
def smart_scrape_url(url: str, user_agent: Optional[str] = None, extract_images: bool = True, delay: int = 2):
    """Smart scraping that automatically detects content type and handles accordingly."""
    logging.info(f"Smart scraping URL: {url}")
    start_time = time.time()

    # Introduce random delay
    actual_delay = random.uniform(1, 3) if delay == 2 else delay
    time.sleep(actual_delay)
    
    # Domain-specific handling
    parsed_url = urlparse(url)
    if "listcorp.com" in parsed_url.netloc:
        headers = get_headers(user_agent=user_agent, referer="https://www.google.com")
    else:
        headers = get_headers(user_agent=user_agent)

    try:
        session = create_http_session()
        
        # First, make a HEAD request to check content type
        head_response = session.head(url, allow_redirects=True, timeout=10, headers=headers)
        content_type = head_response.headers.get('Content-Type', '').lower()
        
        # If HEAD request fails, proceed with GET
        if head_response.status_code >= 400:
            response = session.get(url, allow_redirects=True, timeout=30, headers=headers)
        else:
            response = session.get(url, allow_redirects=True, timeout=30, headers=headers)
        
        response.raise_for_status()
        
        # Check actual content type
        actual_content_type = response.headers.get('Content-Type', '').lower()
        
        # Handle as regular content
        response_time = time.time() - start_time
        redirect_count = len(response.history)
        content_length = response.headers.get('Content-Length')
        content_length = int(content_length) if content_length else None
        
        content_preview = None
        if 'text/' in actual_content_type or 'application/json' in actual_content_type:
            content_preview = response.text[:1000]
        
        logging.info(f"Smart scraped HTML {url} - Status: {response.status_code}")
        
        return {
            "content_type": "html",
            "final_url": response.url,
            "status_code": response.status_code,
            "redirect_count": redirect_count,
            "response_time": response_time,
            "content_preview": content_preview,
            "content_length": content_length,
            "headers": dict(response.headers),
            "method": "traditional",
            "playwright_available": False,
            "note": "Playwright not available in this deployment - use local version for JavaScript-heavy sites"
        }
            
    except Exception as e:
        logging.error(f"Error in smart scraping URL {url}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "redirect-scraper-simple",
        "playwright_available": False
    }

# Basic scraping endpoint
@app.get("/scrape")
def scrape_url(url: str, user_agent: Optional[str] = None) -> URLResponse:
    """Scrape URL with enhanced session management and retry logic."""
    logging.info(f"Scraping URL: {url}")
    start_time = time.time()

    # Introduce random delay to mimic human behavior
    delay = random.uniform(1, 3)  # 1 to 3 seconds
    time.sleep(delay)
    
    # Domain-specific handling for listcorp and others
    parsed_url = urlparse(url)
    if "listcorp.com" in parsed_url.netloc:
        headers = get_headers(user_agent=user_agent, referer="https://www.google.com")
    else:
        headers = get_headers(user_agent=user_agent)

    try:
        session = create_http_session()

        response = session.get(url, allow_redirects=True, timeout=30, headers=headers)
        response.raise_for_status()

        response_time = time.time() - start_time
        redirect_count = len(response.history)

        content_type = response.headers.get('Content-Type', '')
        content_length = response.headers.get('Content-Length')
        content_length = int(content_length) if content_length else None

        content_preview = None
        if 'text/' in content_type or 'application/json' in content_type:
            content_preview = response.text[:1000]

        logging.info(f"Successfully scraped {url} - Status: {response.status_code}, Redirects: {redirect_count}")

        return URLResponse(
            final_url=response.url,
            status_code=response.status_code,
            content_type=content_type,
            content_length=content_length,
            redirect_count=redirect_count,
            response_time=response_time,
            headers=dict(response.headers),
            content_preview=content_preview
        )
    except Exception as e:
        logging.error(f"Error scraping URL {url}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
