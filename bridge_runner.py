import os
import json
import requests
from openai import OpenAI

# Load your OpenAI API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Backend API base URL
BASE_URL = "https://market-scout-api-production.up.railway.app"

# Map function name to API endpoint
ENDPOINTS = {
    "get_company_kpis": "/get_company_kpis",
    # Add more endpoints here
}

# Define tools (functions) for the assistant
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
                        "description": "Stock ticker symbol (e.g., AAPL)"
                    }
                },
                "required": ["ticker"]
            }
        }
    }
]

# Step 1: Send initial request
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

    # Step 2: Call your backend API
    if function_name in ENDPOINTS and ticker:
        try:
            res = requests.post(BASE_URL + ENDPOINTS[function_name], json={"ticker": ticker})
            api_result = res.json() if res.ok else {
                "error": f"Status {res.status_code}",
                "details": res.text
            }
        except Exception as e:
            api_result = {"error": str(e)}
    else:
        api_result = {"error": "Invalid function name or missing ticker"}

    print("\nAPI Result from backend:\n", api_result)

    # Step 3: Follow-up with tool result
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
