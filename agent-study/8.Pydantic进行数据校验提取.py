from pydantic import BaseModel, Field, EmailStr


class UserInfo(BaseModel):
    """传递用户的信息进行数据提取&处理，涵盖name、age、email等"""
    name: str = Field(..., description="用户名字")
    age: int = Field(..., gt=0, description="用户年龄，必须是正整数")
    email: EmailStr = Field(..., description="用户的电子邮件")


# 假设这是从Tool Calls的arguments中获取的字符串
json_string = '{"name": "张三", "age": 25, "email": "zhangsan@example.com"}'

try:
    user = UserInfo.model_validate_json(json_string)  # Pydantic V2的推荐方法
    print(f"用户信息：{user.name}，年龄：{user.age}，邮箱：{user.email}")
    print(user)

except Exception as e:
    print(f"数据提取失败：{e}")

# --- 让我们试试错误数据 ---
invalid_json_string = '{"name": "李四", "age": -5, "email": "not-an-email"}'
try:
    UserInfo.model_validate_json(invalid_json_string)
except Exception as e:
    print("\n--- 错误数据测试 ---")
    print(f"数据校验失败:\n{e}")
