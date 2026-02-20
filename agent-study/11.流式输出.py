import json
from typing import Any

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
                    "description": "一个可以计算数学表达式的计算器",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "需要计算的数学表达式，例如：'123+456+789'"
                            }
                        },
                        "required": ["expression"]
                    }
                }
            }
        ]

    def process_query(self, query: str):
        self.messages.append({"role": "user", "content": query})
        print("Assistant: ", end="", flush=True)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=self.tools,
            tool_choice="auto",  # 改为auto，让模型自动决定是否调用工具
            stream=True
        )

        # 设置变量判断是否执行工具调用、组装content、组装tool_calls
        is_tool_calls = False
        content = ""
        tool_calls_dict: dict[int, dict] = {}  # 使用字典存储工具调用信息

        for chunk in response:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta
            chunk_content = delta.content
            chunk_tool_calls = delta.tool_calls

            # 处理文本内容
            if chunk_content:
                content += chunk_content
                print(chunk_content, end="", flush=True)

            # 处理工具调用
            if chunk_tool_calls:
                is_tool_calls = True
                for chunk_tool_call in chunk_tool_calls:
                    index = chunk_tool_call.index
                    if index not in tool_calls_dict:
                        # 初始化工具调用信息
                        tool_calls_dict[index] = {
                            "id": chunk_tool_call.id or "",
                            "type": chunk_tool_call.type or "function",
                            "function": {
                                "name": chunk_tool_call.function.name or "",
                                "arguments": chunk_tool_call.function.arguments or ""
                            }
                        }
                        # 首次检测到工具调用时打印提示
                        if chunk_tool_call.function and chunk_tool_call.function.name:
                            print(f"\n[检测到工具调用: {chunk_tool_call.function.name}]", flush=True)
                    else:
                        # 拼接参数
                        if chunk_tool_call.id:
                            tool_calls_dict[index]["id"] = chunk_tool_call.id
                        if chunk_tool_call.function and chunk_tool_call.function.name:
                            tool_calls_dict[index]["function"]["name"] = chunk_tool_call.function.name
                        if chunk_tool_call.function and chunk_tool_call.function.arguments:
                            tool_calls_dict[index]["function"]["arguments"] += chunk_tool_call.function.arguments

        # 准备工具调用列表
        tool_calls_list = None
        if tool_calls_dict:
            print(f"\n[共收集到 {len(tool_calls_dict)} 个工具调用]")
            tool_calls_list = [
                {
                    "id": tc["id"],
                    "type": tc["type"],
                    "function": {"name": tc["function"]["name"], "arguments": tc["function"]["arguments"]}
                }
                for tc in sorted(tool_calls_dict.values(), key=lambda x: x.get("id", ""))
            ]

        # 将模型第一次回复的内容添加到历史消息中
        assistant_message: dict[str, Any] = {
            "role": "assistant",
            "content": content if content else None,
        }
        if tool_calls_list:
            assistant_message["tool_calls"] = tool_calls_list

        self.messages.append(assistant_message)

        # 如果有工具调用，执行工具
        if is_tool_calls and tool_calls_list:
            print(f"\n[开始执行工具调用...]")  # 换行
            # 循环调用对应的工具
            for tool_call in tool_calls_list:
                tool_name = tool_call["function"]["name"]
                tool_arguments = tool_call["function"]["arguments"]
                print(f"\n>>> 工具: {tool_name}")
                print(f">>> 原始参数: {repr(tool_arguments)}")

                try:
                    tool_args = json.loads(tool_arguments)
                except json.JSONDecodeError as e:
                    print(f">>> ❌ 解析工具参数失败: {e}")
                    print(f">>> 错误的参数内容: {repr(tool_arguments)}")
                    continue

                print(f">>> 解析后参数: {tool_args}")

                if tool_name not in self.available_tools:
                    print(f">>> ⚠️  警告：工具 {tool_name} 不存在")
                    continue

                function_to_call = self.available_tools[tool_name]

                # 调用工具
                try:
                    result = function_to_call(**tool_args)
                    print(f">>> ✅ 工具执行结果: {result}")
                except Exception as e:
                    result = json.dumps({"error": f"工具执行失败: {str(e)}"})
                    print(f">>> ❌ 工具执行错误: {result}")

                # 将工具结果添加到历史消息中
                self.messages.append({
                    "tool_call_id": tool_call["id"],
                    "role": "tool",
                    "name": tool_name,
                    "content": result,
                })

            # 再次调用模型，让它基于工具调用的结果生成最终回复内容
            print("\n[正在生成最终答案...]")
            second_response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self.tools,
                tool_choice="none",
                stream=True,
            )
            print("Assistant: ", end="", flush=True)
            second_content = ""
            for chunk in second_response:
                if chunk.choices and chunk.choices[0].delta.content:
                    chunk_text = chunk.choices[0].delta.content
                    second_content += chunk_text
                    print(chunk_text, end="", flush=True)

            # 将第二次回复添加到历史消息中
            if second_content:
                self.messages.append({
                    "role": "assistant",
                    "content": second_content
                })

        print("\n")

    def chat_loop(self):
        """运行循环对话"""
        while True:
            try:
                # 获取用户的输入
                query = input("Query: ").strip()
                if query.lower() == "quit":
                    break
                self.process_query(query)
            except Exception as e:
                print(f"\nError: {str(e)}")


if __name__ == "__main__":
    ReActAgent().chat_loop()
