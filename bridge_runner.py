import openai
import requests
import json
import time
import os

openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = "asst_nZVAzYLNhqAIqGTEyrXAqnbb"
RAILWAY_BASE = "https://market-scout-api-production.up.railway.app"

# Mapping of tool names to API endpoints
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

# Step 1: Create thread
thread = openai.beta.threads.create()

# Step 2: Add user message
message = openai.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="Get KPIs for AAPL"
)

# Step 3: Run assistant
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

# Step 5: Handle tool call
tool_call = run_status.required_action.submit_tool_outputs.tool_calls[0]
function_name = tool_call.function.name
arguments = json.loads(tool_call.function.arguments)

endpoint = ENDPOINTS.get(function_name)
if not endpoint:
    print(f"Unknown function requested: {function_name}")
    exit()

# Step 6: Call FastAPI endpoint
url = f"{RAILWAY_BASE}{endpoint}"
response = requests.post(url, json=arguments)

if not response.ok:
    print(f"{function_name} API failed: {response.text}")
    output = {"error": f"API call failed with status {response.status_code}"}
else:
    output = response.json()

# Step 7: Submit tool output
openai.beta.threads.runs.submit_tool_outputs(
    thread_id=thread.id,
    run_id=run.id,
    tool_outputs=[{
        "tool_call_id": tool_call.id,
        "output": json.dumps(output)
    }]
)

# Step 8: Wait for final assistant reply
while True:
    run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    if run_status.status == "completed":
        break
    time.sleep(1)

# Step 9: Print final message
messages = openai.beta.threads.messages.list(thread_id=thread.id)
for msg in reversed(messages.data):
    if msg.role == "assistant":
        print("\nAssistant Response:\n", msg.content[0]["text"]["value"])
        break
