import dotenv
from openai import OpenAI
from pydantic import BaseModel, Field, EmailStr

dotenv.load_dotenv()


class User(BaseModel):
    """传递用户的信息进行数据提取&处理，涵盖name、age、email"""
    name: str = Field(..., description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    age: int = Field(..., gt=0, description="年龄，必须是正整数")


client = OpenAI()

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "user", "content": "我叫小名呀，今年18岁，我的联系方式是weiy11111@163.com"}
    ],
    tools=[
        {
            "type": "function",
            "function": {
                "name": User.__name__,
                "description": User.__doc__,
                "parameters": User.model_json_schema(),
            }
        }
    ],
    tool_choice={"type": "function", "function": {"name": User.__name__}}
)
print(f"user name {User.__name__}, description {User.__doc__}")

user = User.model_validate_json(response.choices[0].message.tool_calls[0].function.arguments)
print(user.model_dump())