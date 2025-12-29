import json

import dotenv
from openai import OpenAI

dotenv.load_dotenv()


def calculator(expression: str) -> str:
    """一个简单的计算器，可以执行数学表达式"""
    try:
        result = eval(expression)
        return json.dumps({"result": result})
    except Exception as e:
        return json.dumps({"error": f"无效表达式, 错误信息: {str(e)}"})


class ReActAgent:
    def __init__(self):
        self.client = OpenAI()
        self.messages = [
            {
                "role": "system",
                "content": "你是一个强大的聊天机器人，请根据用户的提问进行答复，如果需要调用工具请直接调用，不知道请直接回复不清楚"
            }
        ]
        self.model = "deepseek-chat"
        self.available_tools = {"calculator": calculator}
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "calculator",
                    "description": "一个简单的计算器，可以执行数学表达式",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "用户输入的数学表达式"
                            }
                        },
                        "required": ["expression"]
                    }
                }
            }
        ]

    def process_query(self, query: str) -> str:
        """处理用户输出"""
        self.messages.append({"role": "user", "content": query})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=self.tools,
            tool_choice="auto",
            stream=False
        )
        tool_calls = response.choices[0].message.tool_calls
        print("tool_calls:", tool_calls)
        if tool_calls:
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                print("tool_name:", tool_name)
                tool_result = self.available_tools[tool_name](tool_args["expression"])
                self.messages.append({
                    "role": "tool",
                    "content": tool_result,
                    "name": tool_name,
                    "tool_call_id": tool_call.id
                })

            second_response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self.tools,
                tool_choice="none",
            )

            self.messages.append(second_response.choices[0].message.model_dump())
            return "Assistant: " + second_response.choices[0].message.content
        else:
            return "Assistant: " + response.choices[0].message.content

    def chat_loop(self):
        while True:
            try:
                # 获取用户的输入
                query = input("\nQuery: ").strip()
                if query.lower() == "quit":
                    break
                print(self.process_query(query))
            except Exception as e:
                print(f"\nError: {str(e)}")


if __name__ == "__main__":
    agent = ReActAgent()
    agent.chat_loop()
