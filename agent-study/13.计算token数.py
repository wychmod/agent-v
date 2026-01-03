# 导入 transformers 库，这是 Hugging Face 提供的自然语言处理工具库
# 主要用于加载和使用各种预训练的语言模型
import transformers

# 创建分词器（Tokenizer）
# 分词器的作用是将文本转换为模型能理解的数字序列（token）
tokenizer = transformers.AutoTokenizer.from_pretrained(
    "./tokenizer",  # 从本地 tokenizer 文件夹加载分词器配置
    trust_remote_code=True  # 允许执行远程代码（某些自定义分词器需要）
)

# 定义一个简单的提示词（prompt）
# prompt 是用户直接发送给 AI 模型的文本内容
prompt = "你好，你是?"

# 定义一个消息列表（messages），这是对话格式的数据结构
# 列表中每个字典代表一条消息，包含角色（role）和内容（content）
# role 可以是 "user"（用户）、"assistant"（AI助手）或 "system"（系统）
messages = [{"role": "user", "content": "帮我计算下45243*123"}]

# 计算并打印 prompt 的 token 数量
# tokenizer.encode() 将文本转换为 token ID 列表
# len() 获取列表长度，即 token 的数量
# token 数量决定了 API 调用的成本和模型处理的文本长度
print("prompt: ", tokenizer.encode("你好，你是?"))
print("prompt: ", len(tokenizer.encode("你好，你是?")))

# 计算并打印 messages 的 token 数量
# tokenizer.apply_chat_template() 将对话格式的消息转换为模型需要的格式
# 这个方法会自动添加特殊的格式标记（如角色标识符），所以 token 数会比纯文本多
print("messages: ", tokenizer.apply_chat_template(messages))
print("messages: ", len(tokenizer.apply_chat_template(messages)))