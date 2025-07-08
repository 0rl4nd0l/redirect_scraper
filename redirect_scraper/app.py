from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import httpx
import logging
import time
import asyncio
import random
import urllib3
import io
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional
from playwright.async_api import async_playwright
import PyPDF2
import pdfplumber
import pytesseract
from PIL import Image
import cv2
import numpy as np

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

# HTTP middleware for request/response logging and metrics
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    logging.info(f"Incoming request: {request.method} {request.url}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Server"] = "Redirect-Scraper"
    
    logging.info(f"Request completed in {process_time:.4f}s with status {response.status_code}")
    return response

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class URLRequest(BaseModel):
    url: str
    user_agent: Optional[str] = None
    auth_token: Optional[str] = None
    timeout: Optional[int] = 15

class URLResponse(BaseModel):
    final_url: str
    status_code: int
    content_type: str
    content_length: Optional[int]
    redirect_count: int
    response_time: float
    headers: dict
    content_preview: Optional[str] = None

class PDFResponse(BaseModel):
    final_url: str
    status_code: int
    content_type: str
    content_length: Optional[int]
    redirect_count: int
    response_time: float
    headers: dict
    pdf_text: str
    page_count: int
    extraction_method: str

class ImageResponse(BaseModel):
    final_url: str
    status_code: int
    content_type: str
    content_length: Optional[int]
    redirect_count: int
    response_time: float
    headers: dict
    extracted_text: str
    image_dimensions: tuple[int, int]
    extraction_method: str
    confidence_score: Optional[float] = None
    
# PDF extraction functions
def extract_pdf_text_pypdf2(pdf_content: bytes) -> tuple[str, int]:
    """Extract text from PDF using PyPDF2."""
    try:
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text_parts = []
        for page in pdf_reader.pages:
            text_parts.append(page.extract_text())
        
        full_text = '\n'.join(text_parts)
        page_count = len(pdf_reader.pages)
        
        return full_text, page_count
    except Exception as e:
        logging.error(f"PyPDF2 extraction failed: {e}")
        return "", 0

def extract_pdf_text_pdfplumber(pdf_content: bytes) -> tuple[str, int]:
    """Extract text from PDF using pdfplumber (more accurate)."""
    try:
        pdf_file = io.BytesIO(pdf_content)
        
        text_parts = []
        page_count = 0
        
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
                page_count += 1
        
        full_text = '\n'.join(text_parts)
        return full_text, page_count
    except Exception as e:
        logging.error(f"pdfplumber extraction failed: {e}")
        return "", 0

def extract_pdf_text(pdf_content: bytes) -> tuple[str, int, str]:
    """Extract text from PDF using the best available method."""
    # Try pdfplumber first (more accurate)
    text, page_count = extract_pdf_text_pdfplumber(pdf_content)
    if text.strip():
        return text, page_count, "pdfplumber"
    
    # Fallback to PyPDF2
    text, page_count = extract_pdf_text_pypdf2(pdf_content)
    if text.strip():
        return text, page_count, "PyPDF2"
    
    return "Unable to extract text from PDF", 0, "failed"

# Enhanced sync endpoint with session management
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

# Enhanced async endpoint with httpx
@app.post("/fetch/")
async def fetch_url_content(request: URLRequest) -> URLResponse:
    """Fetch URL content asynchronously with enhanced error handling."""
    logging.info(f"Fetching URL: {request.url}")
    start_time = time.time()
    
    try:
        headers = get_headers(user_agent=request.user_agent, auth_token=request.auth_token)
        
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=request.timeout,
            headers=headers
        ) as client:
            response = await client.get(request.url)
            response.raise_for_status()
            
            response_time = time.time() - start_time
            redirect_count = len(response.history)
            
            content_type = response.headers.get('Content-Type', '')
            content_length = response.headers.get('Content-Length')
            content_length = int(content_length) if content_length else None
            
            content_preview = None
            if 'application/pdf' in content_type:
                content_preview = "PDF content detected"
            elif 'text/' in content_type or 'application/json' in content_type:
                content_preview = response.text[:1000]
            
            logging.info(f"Successfully fetched {request.url} - Status: {response.status_code}, Redirects: {redirect_count}")
            
            return URLResponse(
                final_url=str(response.url),
                status_code=response.status_code,
                content_type=content_type,
                content_length=content_length,
                redirect_count=redirect_count,
                response_time=response_time,
                headers=dict(response.headers),
                content_preview=content_preview
            )
    except httpx.RequestError as e:
        logging.error(f"Request error for URL {request.url}: {e}")
        raise HTTPException(status_code=400, detail=f"Request failed: {str(e)}")
    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP error for URL {request.url}: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=f"HTTP {e.response.status_code}: {e.response.reason_phrase}")
    except Exception as e:
        logging.error(f"Unexpected error for URL {request.url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# New endpoint for batch processing
@app.post("/batch-fetch/")
async def batch_fetch_urls(urls: list[str], user_agent: Optional[str] = None) -> list[URLResponse]:
    """Fetch multiple URLs concurrently."""
    logging.info(f"Batch fetching {len(urls)} URLs")
    
    async def fetch_single(url: str) -> URLResponse:
        request = URLRequest(url=url, user_agent=user_agent)
        return await fetch_url_content(request)
    
    import asyncio
    tasks = [fetch_single(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions and return successful results
    successful_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logging.error(f"Failed to fetch {urls[i]}: {result}")
        else:
            successful_results.append(result)
    
    return successful_results

# Stealth endpoint for stubborn websites with advanced anti-bot measures
@app.get("/stealth-scrape")
def stealth_scrape_url(url: str, user_agent: Optional[str] = None) -> URLResponse:
    """Stealth scraping with maximum anti-bot detection avoidance."""
    logging.info(f"Stealth scraping URL: {url}")
    start_time = time.time()
    
    # Longer random delay for stealth mode
    delay = random.uniform(2, 5)  # 2 to 5 seconds
    time.sleep(delay)
    
    # Enhanced headers for stealth mode
    stealth_headers = {
        'User-Agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.google.com/',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-User': '?1',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Cache-Control': 'max-age=0',
    }
    
    try:
        session = requests.Session()
        
        # Disable SSL verification for problematic sites (use with caution)
        session.verify = False
        
        # Set custom timeout and retry configuration
        session.mount('http://', HTTPAdapter(max_retries=5))
        session.mount('https://', HTTPAdapter(max_retries=5))
        
        response = session.get(
            url, 
            headers=stealth_headers, 
            allow_redirects=True, 
            timeout=45,
            stream=False
        )
        
        response.raise_for_status()
        
        response_time = time.time() - start_time
        redirect_count = len(response.history)
        
        content_type = response.headers.get('Content-Type', '')
        content_length = response.headers.get('Content-Length')
        content_length = int(content_length) if content_length else None
        
        content_preview = None
        if 'text/' in content_type or 'application/json' in content_type:
            content_preview = response.text[:1000]
        
        logging.info(f"Successfully stealth scraped {url} - Status: {response.status_code}, Redirects: {redirect_count}")
        
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
        logging.error(f"Error in stealth scraping URL {url}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()

# Browser-based scraping endpoint using Playwright
@app.get("/browser-scrape")
async def browser_scrape_url(url: str, user_agent: Optional[str] = None, wait_time: int = 3) -> URLResponse:
    """Scrape URL using headless browser to bypass advanced bot detection."""
    logging.info(f"Browser scraping URL: {url}")
    start_time = time.time()
    
    try:
        # Check if Playwright is available
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logging.error("Playwright not available, falling back to stealth scraping")
            return stealth_scrape_url(url, user_agent)
            
        async with async_playwright() as p:
            # Launch browser with minimal configuration for Railway compatibility
            try:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-web-security',
                    '--disable-features=site-per-process'
                ]
            )
            
            # Create context with realistic browser fingerprint
            context = await browser.new_context(
                user_agent=user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York',
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1'
                }
            )
            
            # Create page and navigate
            page = await context.new_page()
            
            # Set additional realistic properties
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                window.chrome = {
                    runtime: {},
                };
                Object.defineProperty(navigator, 'permissions', {
                    get: () => ({
                        query: () => Promise.resolve({ state: 'granted' }),
                    }),
                });
            """)
            
            # Navigate to the URL
            response = await page.goto(
                url, 
                wait_until='networkidle',
                timeout=30000
            )
            
            # Wait for additional time to ensure full page load
            await asyncio.sleep(wait_time)
            
            # Get final URL after redirects
            final_url = page.url
            
            # Get response details
            status_code = response.status if response else 200
            
            # Count redirects by checking navigation history
            redirect_count = 0
            for entry in await page.evaluate('() => performance.getEntriesByType("navigation")'):
                if 'redirectCount' in entry:
                    redirect_count = entry['redirectCount']
                    break
            
            # Get page content
            content = await page.content()
            content_preview = content[:1000] if content else None
            
            # Get response headers (approximated)
            headers = {
                'Content-Type': 'text/html; charset=utf-8',
                'Status': str(status_code)
            }
            
            response_time = time.time() - start_time
            
            await browser.close()
            
            logging.info(f"Successfully browser scraped {url} - Status: {status_code}, Final URL: {final_url}")
            
            return URLResponse(
                final_url=final_url,
                status_code=status_code,
                content_type='text/html; charset=utf-8',
                content_length=len(content) if content else 0,
                redirect_count=redirect_count,
                response_time=response_time,
                headers=headers,
                content_preview=content_preview
            )
            
            except Exception as browser_error:
                logging.error(f"Browser launch failed: {browser_error}, falling back to stealth scraping")
                return stealth_scrape_url(url, user_agent)
            
    except Exception as e:
        logging.error(f"Error in browser scraping URL {url}: {e}")
        # Fallback to stealth scraping if browser scraping fails completely
        try:
            logging.info(f"Attempting fallback to stealth scraping for {url}")
            return stealth_scrape_url(url, user_agent)
        except Exception as fallback_error:
            logging.error(f"Fallback stealth scraping also failed: {fallback_error}")
            raise HTTPException(status_code=400, detail=f"Both browser and stealth scraping failed: {str(e)}")

# PDF scraping and text extraction endpoint
@app.get("/scrape-pdf")
def scrape_pdf_url(url: str, user_agent: Optional[str] = None) -> PDFResponse:
    """Scrape PDF URL and extract text content."""
    logging.info(f"Scraping PDF URL: {url}")
    start_time = time.time()

    # Introduce random delay to mimic human behavior
    delay = random.uniform(1, 3)
    time.sleep(delay)
    
    # Domain-specific handling
    parsed_url = urlparse(url)
    if "listcorp.com" in parsed_url.netloc:
        headers = get_headers(user_agent=user_agent, referer="https://www.google.com")
    else:
        headers = get_headers(user_agent=user_agent)
    
    # Accept PDF content type
    headers['Accept'] = 'application/pdf,application/octet-stream,*/*;q=0.8'

    try:
        session = create_http_session()
        response = session.get(url, allow_redirects=True, timeout=30, headers=headers)
        response.raise_for_status()

        response_time = time.time() - start_time
        redirect_count = len(response.history)

        content_type = response.headers.get('Content-Type', '')
        content_length = response.headers.get('Content-Length')
        content_length = int(content_length) if content_length else len(response.content)

        # Check if it's actually a PDF
        if 'application/pdf' not in content_type and not response.content.startswith(b'%PDF'):
            raise HTTPException(status_code=400, detail="URL does not contain PDF content")

        # Extract text from PDF
        pdf_text, page_count, extraction_method = extract_pdf_text(response.content)

        logging.info(f"Successfully scraped PDF {url} - Status: {response.status_code}, Pages: {page_count}, Method: {extraction_method}")

        return PDFResponse(
            final_url=response.url,
            status_code=response.status_code,
            content_type=content_type,
            content_length=content_length,
            redirect_count=redirect_count,
            response_time=response_time,
            headers=dict(response.headers),
            pdf_text=pdf_text,
            page_count=page_count,
            extraction_method=extraction_method
        )
    except Exception as e:
        logging.error(f"Error scraping PDF URL {url}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()

# Async PDF scraping endpoint
@app.post("/fetch-pdf/")
async def fetch_pdf_content(request: URLRequest) -> PDFResponse:
    """Fetch PDF content asynchronously and extract text."""
    logging.info(f"Fetching PDF URL: {request.url}")
    start_time = time.time()
    
    try:
        headers = get_headers(user_agent=request.user_agent, auth_token=request.auth_token)
        headers['Accept'] = 'application/pdf,application/octet-stream,*/*;q=0.8'
        
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=request.timeout,
            headers=headers
        ) as client:
            response = await client.get(request.url)
            response.raise_for_status()
            
            response_time = time.time() - start_time
            redirect_count = len(response.history)
            
            content_type = response.headers.get('Content-Type', '')
            content_length = response.headers.get('Content-Length')
            content_length = int(content_length) if content_length else len(response.content)
            
            # Check if it's actually a PDF
            if 'application/pdf' not in content_type and not response.content.startswith(b'%PDF'):
                raise HTTPException(status_code=400, detail="URL does not contain PDF content")
            
            # Extract text from PDF
            pdf_text, page_count, extraction_method = extract_pdf_text(response.content)
            
            logging.info(f"Successfully fetched PDF {request.url} - Status: {response.status_code}, Pages: {page_count}, Method: {extraction_method}")
            
            return PDFResponse(
                final_url=str(response.url),
                status_code=response.status_code,
                content_type=content_type,
                content_length=content_length,
                redirect_count=redirect_count,
                response_time=response_time,
                headers=dict(response.headers),
                pdf_text=pdf_text,
                page_count=page_count,
                extraction_method=extraction_method
            )
    except httpx.RequestError as e:
        logging.error(f"Request error for PDF URL {request.url}: {e}")
        raise HTTPException(status_code=400, detail=f"Request failed: {str(e)}")
    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP error for PDF URL {request.url}: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=f"HTTP {e.response.status_code}: {e.response.reason_phrase}")
    except Exception as e:
        logging.error(f"Unexpected error for PDF URL {request.url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Smart URL endpoint that detects and handles both HTML and PDF content
@app.get("/smart-scrape")
async def smart_scrape_url(url: str, user_agent: Optional[str] = None, extract_images: bool = True, delay: int = 2):
    """Smart scraping that automatically detects content type and handles accordingly."""
    logging.info(f"Smart scraping URL: {url}")
    start_time = time.time()

    # Introduce random delay
    actual_delay = random.uniform(1, 3) if delay == 2 else delay
    time.sleep(actual_delay)
    
    # Domain-specific handling - detect if we should use Playwright
    parsed_url = urlparse(url)
    use_playwright = "listcorp.com" in parsed_url.netloc.lower()  # Known JS-heavy sites
    
    if use_playwright:
        logging.info(f"Detected JavaScript-heavy site, using browser scraping for {url}")
        try:
            # Use browser scraping for JavaScript-heavy sites
            browser_result = await browser_scrape_url(url, user_agent)
            
            # Convert browser result to smart-scrape format
            return {
                "content_type": "html",
                "final_url": browser_result.final_url,
                "status_code": browser_result.status_code,
                "redirect_count": browser_result.redirect_count,
                "response_time": browser_result.response_time,
                "content_preview": browser_result.content_preview,
                "content_length": browser_result.content_length,
                "headers": browser_result.headers,
                "method": "playwright"
            }
        except Exception as browser_error:
            logging.error(f"Browser scraping failed for {url}: {browser_error}, falling back to traditional")
            # Fall through to traditional scraping
    
    # Traditional scraping approach
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
        
        # Detect if it's a PDF (by content type or content signature)
        is_pdf = ('application/pdf' in actual_content_type or 
                 response.content.startswith(b'%PDF'))
        
        if is_pdf:
            # Handle as PDF
            response_time = time.time() - start_time
            redirect_count = len(response.history)
            content_length = len(response.content)
            
            pdf_text, page_count, extraction_method = extract_pdf_text(response.content)
            
            logging.info(f"Smart scraped PDF {url} - Status: {response.status_code}, Pages: {page_count}")
            
            return {
                "content_type": "pdf",
                "final_url": response.url,
                "status_code": response.status_code,
                "redirect_count": redirect_count,
                "response_time": response_time,
                "pdf_text": pdf_text,
                "page_count": page_count,
                "extraction_method": extraction_method,
                "content_length": content_length
            }
        else:
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
                "method": "traditional"
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
        "service": "redirect-scraper"
    }
