import json
import os

import dotenv
import requests

dotenv.load_dotenv()

with requests.request(
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
        "stream": True
    }
) as response:
    for line in response.iter_lines(decode_unicode=True):
        if line and line.startswith("data:"):
            data = line.lstrip("data:").strip()
            if data != "[DONE]":  # 处理结束标记
                try:
                    json_data = json.loads(data)
                    print("content:", json_data.get("choices", [{}])[0].get("delta", {}).get("content", ""))
                except json.JSONDecodeError:
                    print("raw data:", data)