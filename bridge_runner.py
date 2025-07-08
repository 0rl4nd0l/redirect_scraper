import openai
import requests
import json
import time
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

ASSISTANT_ID = "asst_nZVAzYLNhqAIqGTEyrXAqnbb"
RAILWAY_URL = "https://market-scout-api-production.up.railway.app/get_company_kpis"

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
arguments = json.loads(tool_call.function.arguments)

ticker = arguments["ticker"]

# Step 6: Call your Railway API
response = requests.post(RAILWAY_URL, json={"ticker": ticker})
if response.status_code != 200:
    print("KPI API failed:", response.text)
    exit()
api_result = response.json()

# Step 7: Submit tool output back to OpenAI
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
