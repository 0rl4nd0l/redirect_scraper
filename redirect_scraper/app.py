from fastapi import FastAPI, HTTPException, Query
import requests

app = FastAPI()

@app.get("/scrape")
def scrape_url(url: str = Query(..., description="URL to scrape")):
    try:
        response = requests.get(url, allow_redirects=True, timeout=15, verify=False)
        response.raise_for_status()
        return {
            "final_url": response.url,
            "status_code": response.status_code,
            "content_snippet": response.text[:500]  # first 500 chars as preview
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=str(e))
