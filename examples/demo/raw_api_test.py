import requests

url = "https://cloud.infini-ai.com/maas/v1/chat/completions"

weather_tool = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "The unit of temperature to use. Infer this from the user's location.",
                },
            },
            "required": ["location"],
        },
    },
}

payload = {
    "model": "claude-sonnet-4-20250514",  # "claude-4-sonnet-20250514",
    "messages": [
        {
            "role": "user",
            "content": "北京今天天气如何？",
        }
    ],
    "tools": [weather_tool],
    # "tool_choice": "auto",
}
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer Your_API_Key",  # Replace with your actual API key
}

response = requests.post(url, json=payload, headers=headers)


print(response.json())
