import requests

url = "https://cloud.infini-ai.com/maas/v1/chat/completions"

payload = {
    "model": "claude-3-7-sonnet-20250219",
    "messages": [{"role": "user", "content": "你是谁"}],
}
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_API_KEY",  # Replace with your actual API key
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
