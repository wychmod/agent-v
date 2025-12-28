import dotenv
from openai import OpenAI

dotenv.load_dotenv()

client = OpenAI()

response = client.chat.completions.create(
    model="deepseek-r1-250528",
    messages=[{"role": "user", "content": "你好，你是?"}]
)

print("推理内容:", response.choices[0].message.reasoning_content)
print("最终答案:", response.choices[0].message.content)
