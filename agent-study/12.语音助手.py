import json
import tempfile
import io
import os

import dotenv
import keyboard
import numpy as np
import sounddevice as sd
import soundfile as sf
import requests
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

    def process_query(self, query: str) -> str:
        """使用deepseek处理用户输出"""
        self.messages.append({"role": "user", "content": query})

        # 调用deepseek发起请求
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=self.tools,
        )

        # 获取响应消息+工具响应
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # 将模型第一次回复添加到历史消息中
        self.messages.append(response_message.model_dump())

        # 判断是否执行工具调用
        if tool_calls:

            # 循环执行工具调用
            for tool_call in tool_calls:
                print("Tool Call: ", tool_call.function.name)
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                function_to_call = self.available_tools[tool_name]

                # 调用工具
                result = function_to_call(**tool_args)
                print(f"Tool [{tool_name}] Result: {result}")

                # 将工具结果添加到历史消息中
                self.messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": tool_name,
                    "content": result,
                })

            # 再次调用模型，让它基于工具调用的结果生成最终回复内容
            second_response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self.tools,
                tool_choice="none",
            )

            self.messages.append(second_response.choices[0].message.model_dump())
            return "Assistant: " + second_response.choices[0].message.content
        else:
            return "Assistant: " + response_message.content

    def chat_loop(self):
        """运行循环对话"""
        while True:
            try:
                # 获取用户的输入
                query = self.speech_to_text().strip()
                print(f"\nQuery: {query}")
                if query == "退出":
                    break

                # 获取Agent的输出并播放语音
                answer = self.process_query(query)
                print(answer)
                self.text_to_speech(answer)
            except Exception as e:
                print(f"\nError: {str(e)}")

    @classmethod
    def speech_to_text(cls) -> str:
        """根据语音信息获取文本的输入内容"""
        samplerate = 16000
        channels = 1
        recording = []
        is_recording = False

        print("按空格开始录音，再按一次空格停止录音...")

        def callback(indata, frames, time, status):
            if is_recording:
                recording.append(indata.copy())

        stream = sd.InputStream(samplerate=samplerate, channels=channels, callback=callback)
        stream.start()

        # 等待第一次空格：开始录音
        keyboard.wait("space")
        is_recording = True
        print("录音中... 再按一次空格停止")

        # 等待第二次空格：停止录音
        keyboard.wait("space")
        is_recording = False
        stream.stop()
        stream.close()
        print("录音结束")

        # 把片段拼接成一个 numpy 数组
        if not recording:
            print("没有录到声音")
            return ""

        audio_data = np.concatenate(recording, axis=0)
        print(f"[DEBUG] 音频数据形状: {audio_data.shape}")
        print(f"[DEBUG] 音频时长: {len(audio_data) / samplerate:.2f} 秒")

        # 保存到临时文件 - 使用WAV格式确保兼容性
        audio_path = tempfile.mktemp(suffix=".wav")
        print(f"[DEBUG] 临时文件路径: {audio_path}")

        # 使用soundfile写入音频文件，指定格式和子类型
        sf.write(audio_path, audio_data, samplerate, format='WAV', subtype='PCM_16')
        print(f"[DEBUG] 音频文件已写入")

        # 检查文件大小
        file_size = os.path.getsize(audio_path)
        print(f"[DEBUG] 音频文件大小: {file_size} 字节")

        if file_size < 100:
            print(f"[ERROR] 音频文件太小，可能录音失败")
            try:
                os.remove(audio_path)
            except:
                pass
            return ""

        # 调用 OpenAI API 语音转文本
        try:
            print(f"[DEBUG] 开始调用语音转文本API...")
            client = OpenAI(timeout=60.0)  # 增加超时时间

            # 方法1: 使用元组方式传递文件（推荐）
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
            print(f"[DEBUG] 读取音频内容大小: {len(audio_bytes)} 字节")

            # 使用元组格式 (filename, file_content, content_type)
            files = ("audio.wav", audio_bytes, "audio/wav")

            print(f"[DEBUG] 准备发送到Whisper API...")
            transcript = client.audio.translations.create(
                model="whisper-1",
                file=files
            )
            print(f"[DEBUG] 转录成功: {transcript.text}")
            return transcript.text

        except Exception as e:
            print(f"[ERROR] 语音转文本失败: {str(e)}")
            print(f"[ERROR] 错误类型: {type(e).__name__}")
            import traceback
            traceback.print_exc()

            # 尝试备用方案：直接使用 BytesIO
            try:
                print(f"[DEBUG] 尝试备用方案...")
                audio_file = io.BytesIO(audio_bytes)
                audio_file.name = "audio.wav"

                transcript = client.audio.translations.create(
                    model="whisper-1",
                    file=audio_file
                )
                print(f"[DEBUG] 备用方案成功: {transcript.text}")
                return transcript.text
            except Exception as e2:
                print(f"[ERROR] 备用方案也失败: {str(e2)}")
                traceback.print_exc()
                return ""
        finally:
            # 清理临时文件
            try:
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                    print(f"[DEBUG] 临时文件已删除")
            except Exception as e:
                print(f"[WARNING] 删除临时文件失败: {e}")

    @classmethod
    def text_to_speech(cls, text: str) -> None:
        # 调用 OpenAI TTS 生成语音
        try:
            print(f"[DEBUG] 开始文本转语音，文本长度: {len(text)}")
            client = OpenAI(timeout=60.0)
            response = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text,
                response_format="mp3"  # 明确指定格式
            )
            print(f"[DEBUG] TTS API调用成功")

            # 保存临时文件
            audio_path = tempfile.mktemp(suffix=".mp3")
            audio_content = response.content  # 使用content属性更可靠
            print(f"[DEBUG] 语音内容大小: {len(audio_content)} 字节")

            with open(audio_path, "wb") as f:
                f.write(audio_content)
            print(f"[DEBUG] 语音文件已保存: {audio_path}")

            # 播放语音
            print(f"[DEBUG] 开始播放语音...")
            data, samplerate = sf.read(audio_path)
            sd.play(data, samplerate)
            sd.wait()
            print(f"[DEBUG] 语音播放完成")

            # 清理临时文件
            try:
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                    print(f"[DEBUG] 语音临时文件已删除")
            except Exception as e:
                print(f"[WARNING] 删除语音文件失败: {e}")

        except Exception as e:
            print(f"[ERROR] 文本转语音失败: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    ReActAgent().chat_loop()
