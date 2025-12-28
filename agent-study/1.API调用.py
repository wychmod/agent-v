import os

import dotenv
import requests

dotenv.load_dotenv()

response = requests.request(
    "POST",
    f"{os.getenv('API_URL')}/chat/completions",
    headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {os.getenv('API_KEY')}"
    },
    json={
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": "你好，你是?"}
        ],
        "stream": False
    }
)

print(response.json())
