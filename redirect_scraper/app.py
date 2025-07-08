from fastapi import FastAPI, HTTPException
import requests

app = FastAPI()

@app.get("/scrape")
def scrape_url(url: str):
    try:
        resp = requests.get(url, allow_redirects=True, timeout=10)
        resp.raise_for_status()
        return {
            "final_url": resp.url,
            "status_code": resp.status_code,
            "content_snippet": resp.text[:500]  # first 500 chars for preview
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=str(e))

