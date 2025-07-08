import logging

logging.basicConfig(level=logging.INFO)

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
