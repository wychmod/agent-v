import dotenv
from openai import OpenAI

dotenv.load_dotenv()

client = OpenAI()

response = client.chat.completions.create(
    model="deepseek-v3.2",
    messages=[{"role": "user", "content": "你好，你是?"}],
    stream=True
)

for chunk in response:
    print(chunk.choices[0].delta.content, end="", flush=True)
