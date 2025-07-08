import openai
import requests
import json
import time
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

ASSISTANT_ID = "asst_nZVAzYLNhqAIqGTEyrXAqnbb"
BASE_URL = "https://market-scout-api-production.up.railway.app"

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

# Step 1: Create a new thread
thread = openai.beta.threads.create()

# Step 2: Send a message to the thread
message = openai.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="Get KPIs for AAPL"
)

# Step 3: Run the assistant
run = openai.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=ASSISTANT_ID
)

# Step 4: Wait for tool call
while True:
    run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    if run_status.status == "requires_action":
        break
    elif run_status.status in ["completed", "failed", "cancelled"]:
        print(f"Run ended unexpectedly with status: {run_status.status}")
        exit()
    time.sleep(1)

# Step 5: Extract tool call
tool_call = run_status.required_action.submit_tool_outputs.tool_calls[0]
function_name = tool_call.function.name
arguments = json.loads(tool_call.function.arguments)
ticker = arguments.get("ticker")

# Step 6: Call appropriate endpoint
if function_name in ENDPOINTS and ticker:
    try:
        response = requests.post(BASE_URL + ENDPOINTS[function_name], json={"ticker": ticker})
        api_result = response.json() if response.ok else {
            "error": f"Status {response.status_code}",
            "details": response.text
        }
    except Exception as e:
        api_result = {"error": str(e)}
else:
    api_result = {"error": "Invalid function name or missing ticker"}

# Step 7: Submit tool output
openai.beta.threads.runs.submit_tool_outputs(
    thread_id=thread.id,
    run_id=run.id,
    tool_outputs=[{
        "tool_call_id": tool_call.id,
        "output": json.dumps(api_result)
    }]
)

# Step 8: Wait for final response
while True:
    run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    if run_status.status == "completed":
        break
    time.sleep(1)

# Step 9: Print assistant's final message
messages = openai.beta.threads.messages.list(thread_id=thread.id)
for msg in reversed(messages.data):
    if msg.role == "assistant":
        print("\nAssistant Response:\n", msg.content[0].text.value)
        break
