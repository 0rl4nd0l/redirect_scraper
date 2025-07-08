import os
import json
import requests
import openai

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Base URL for your custom backend API
BASE_URL = "https://market-scout-api-production.up.railway.app"

# Mapping of function names to backend API endpoints
ENDPOINTS = {
    "get_company_kpis": "/get_company_kpis",
    # Add other endpoints if needed
}

# Define the available tools (functions)
tools = [
    {
        "type": "function",
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
]

# Step 1: Create initial assistant request
response = openai.ChatCompletion.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": "Get KPIs for AAPL"}
    ],
    tools=tools,
    tool_choice="auto"
)

# Step 2: If GPT triggers a tool
tool_calls = response.get("choices")[0]["message"].get("tool_calls")
if tool_calls:
    tool_call = tool_calls[0]
    function_name = tool_call["function"]["name"]
    arguments = json.loads(tool_call["function"]["arguments"])
    ticker = arguments.get("ticker")

    # Step 3: Call backend API
    if function_name in ENDPOINTS and ticker:
        try:
            api_response = requests.post(
                BASE_URL + ENDPOINTS[function_name],
                json={"ticker": ticker}
            )
            api_result = api_response.json() if api_response.ok else {
                "error": f"Status {api_response.status_code}",
                "details": api_response.text
            }
        except Exception as e:
            api_result = {"error": str(e)}
    else:
        api_result = {"error": "Invalid function name or missing ticker"}

    print("\nAPI Result from backend:\n", api_result)

    # Step 4: Submit tool output to assistant
    follow_up = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": "Get KPIs for AAPL"},
            {
                "role": "assistant",
                "tool_calls": [tool_call]
            },
            {
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": json.dumps(api_result)
            }
        ]
    )

    print("\nAssistant Response:\n", follow_up["choices"][0]["message"]["content"])
else:
    # No tool call; direct answer from assistant
    print("\nAssistant Response:\n", response["choices"][0]["message"]["content"])
