import requests
from fastapi import FastAPI, HTTPException
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = FastAPI()

@app.get("/scrape")
def scrape_url(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.listcorp.com/",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }
    try:
        resp = requests.get(url, allow_redirects=True, timeout=10, verify=False, headers=headers)
        resp.raise_for_status()
        return {
            "final_url": resp.url,
            "status_code": resp.status_code,
            "content_snippet": resp.text[:500]
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=str(e))
