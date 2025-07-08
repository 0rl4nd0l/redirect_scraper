import os
import time
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
    "get_company_profile": "/get_company_profile",
    "get_company_ratios": "/get_company_ratios",
    "get_income_statement": "/get_income_statement",
    "get_balance_sheet": "/get_balance_sheet",
    "get_cash_flow": "/get_cash_flow",
    "get_valuation_metrics": "/get_valuation_metrics",
    "get_insider_trades": "/get_insider_trades",
    "get_price_targets": "/get_price_targets",
    "get_company_news": "/get_company_news"
}

# Define tools (functions) that the assistant can call
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
    # Add other functions in the same format if needed
]

# Step 1: Create the initial assistant response
response = openai.responses.create(
    model="gpt-4o",
    input="Get KPIs for AAPL",
    tools=tools
)

# Step 2: If the assistant wants to call a tool
if response.status == "requires_action":
    tool_call = response.required_action.submit_tool_outputs.tool_calls[0]
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    ticker = arguments.get("ticker")

    # Step 3: Call the external API
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

    print("\nAPI Result from Finchat:\n", api_result)

    # Step 4: Submit the tool output back to the assistant
    follow_up = openai.responses.create(
        model="gpt-4o",
        previous_response_id=response.id,
        tool_outputs=[
            {
                "tool_call_id": tool_call.id,
                "output": json.dumps(api_result)
            }
        ]
    )

    # Step 5: Print the assistant's response
    print("\nAssistant Response:\n", follow_up.output[0].content[0].text)
else:
    # Assistant answered without a tool call
    print("\nAssistant Response:\n", response.output[0].content[0].text)
