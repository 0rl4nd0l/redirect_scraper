import requests

url = "https://www.listcorp.com/asx/alkane-researches-limited/news/tomingley-fy2025-production-achievements-guidance-3210664.html"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
}

response = requests.get(url, headers=headers, allow_redirects=True)

print(f"Status code: {response.status_code}")
print(f"Final URL: {response.url}")
print(f"Content snippet: {response.text[:500]}")  # print first 500 chars

