import requests

api_key = "b82d24301d364aef9a0c55462079cba3"
ticker = "AAPL"
url = f"https://datafeed.finchat.io/company/{ticker}/kpis"
headers = {"Authorization": f"Bearer {api_key}"}

response = requests.get(url, headers=headers)

if response.ok:
    print("API call successful!")
    print(response.json())
else:
    print(f"Failed with status code: {response.status_code}")
    print(response.text)

