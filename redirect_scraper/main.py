from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI()

class URLRequest(BaseModel):
    url: str

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
