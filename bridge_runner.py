import os
import json
import requests
from openai import OpenAI
from web_scraper import EnhancedWebScraper, check_tesseract_available

# Setup OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# URL to your FastAPI backend (deployed or local)
BASE_URL = "https://market-scout-api-production.up.railway.app"  # or your Railway domain

ENDPOINTS = {
    "get_company_kpis": "/get_company_kpis"
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_company_kpis",
            "description": "Get key performance indicators for a company by ticker",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "The stock ticker symbol (e.g., AAPL)"
                    }
                },
                "required": ["ticker"]
            }
        }
    }
]

# Test OCR functionality
print("🔍 Testing OCR capabilities...")
if check_tesseract_available():
    print("✅ Tesseract OCR is available on Railway!")
    
    # Test with a simple web scraping example
    scraper = EnhancedWebScraper(delay=1)
    test_result = scraper.scrape_url("https://httpbin.org/html", extract_images=False)
    print(f"📄 Test scrape result: {test_result.get('title', 'No title')}")
else:
    print("❌ Tesseract OCR not available")

print("\n" + "="*50)
print("Starting OpenAI integration...")
print("="*50)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Get KPIs for AAPL"}],
    tools=tools,
    tool_choice="auto"
)

tool_calls = response.choices[0].message.tool_calls
if tool_calls:
    tool_call = tool_calls[0]
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    ticker = arguments.get("ticker")

    if function_name in ENDPOINTS and ticker:
        res = requests.post(BASE_URL + ENDPOINTS[function_name], json={"ticker": ticker})
        api_result = res.json() if res.ok else {
            "error": f"Status {res.status_code}",
            "details": res.text
        }
    else:
        api_result = {"error": "Invalid function name or missing ticker"}

    print("\nAPI Result:\n", api_result)

    follow_up = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": "Get KPIs for AAPL"},
            {
                "role": "assistant",
                "tool_calls": [tool_call]
            },
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(api_result)
            }
        ]
    )

    print("\nAssistant Response:\n", follow_up.choices[0].message.content)
else:
    print("\nAssistant Response:\n", response.choices[0].message.content)
# debug test line
