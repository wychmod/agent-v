import base64

import dotenv
from openai import OpenAI

dotenv.load_dotenv()

image_url = "./image/dog.jpg"

with open(image_url, "rb") as f:
    image_data = f.read()

image_url = f"data:image/jpeg;base64,{base64.b64encode(image_data).decode("utf-8")}"

client = OpenAI()

response = client.chat.completions.create(
    model="doubao-seed-1-6-flash-250615",
    messages=[
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
    stream=False
)

print("最终答案:", response.choices[0].message.content)
