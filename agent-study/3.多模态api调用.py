import base64
import os

import dotenv
import requests

dotenv.load_dotenv()

image_url = "./image/dog.jpg"

with open(image_url, "rb") as f:
    image_data = f.read()

image_url = f"data:image/jpeg;base64,{base64.b64encode(image_data).decode("utf-8")}"

response = requests.request(
    "POST",
    f"{os.getenv('API_URL')}/chat/completions",
    headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {os.getenv('API_KEY')}"
    },
    json={
        "model": "doubao-seed-1-6-flash-250615",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    },
                    {
                        "type": "text",
                        "text": "请描述这个图片"
                    }
                ]
            }
        ],
        "temperature": 0.3
    },
    timeout=20
)

print(response.json())
