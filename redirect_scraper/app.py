from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import logging

app = FastAPI()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

logging.basicConfig(level=logging.INFO)

class URLRequest(BaseModel):
    url: str

@app.get("/scrape")
def scrape_url(url: str):
    logging.info(f"Scraping URL: {url}")
    try:
        resp = requests.get(url, allow_redirects=True, timeout=30, headers=HEADERS)  # without verify=False
        resp.raise_for_status()
        logging.info(f"Received status code: {resp.status_code}")
        return {
            "final_url": resp.url,
            "status_code": resp.status_code,
            "content_snippet": resp.text[:500]
        }
    except Exception as e:
        logging.error(f"Error scraping URL {url}: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/fetch/")
async def fetch_url_content(request: URLRequest):
    try:
        with requests.Session() as session:
            response = session.get(request.url, allow_redirects=True, timeout=15)
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '')
            if 'application/pdf' in content_type:
                return {"message": "PDF content detected", "final_url": response.url}
            else:
                preview = response.text[:1000]
                return {"message": "HTML/Text content", "final_url": response.url, "preview": preview}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=str(e))
