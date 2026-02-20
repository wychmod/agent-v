import asyncio

# 从 MCP SDK 导入核心组件：
# - StdioServerParameters: 用于配置通过标准输入输出(stdio)启动 MCP 服务器的参数
# - stdio_client: 用于建立与 MCP 服务器的 stdio 连接
# - ClientSession: 用于与 MCP 服务器进行会话管理和通信
from mcp import StdioServerParameters, stdio_client, ClientSession


async def main() -> None:
    """
    MCP 客户端主函数
    负责启动 MCP 服务器、建立连接、发现工具并调用工具
    """
    # 配置 MCP 服务器启动参数
    # StdioServerParameters 定义了如何通过子进程启动 MCP 服务器
    server_params = StdioServerParameters(
        # command: 要执行的命令，这里使用 uv 作为 Python 包管理器和运行器
        command="uv",
        # args: 传递给 uv 命令的参数列表
        args=[
            # --directory: 指定工作目录，uv 会在这个目录下执行命令
            # 这里指向项目根目录，确保能正确找到并运行 MCP 服务文件
            "--directory",
            "/Users/ahs/IdeaProjects/agent-v/agent-study",
            # run: uv 的子命令，用于运行 Python 脚本或模块
            "run",
            # 要运行的 MCP 服务器脚本文件名
            # 这个文件实现了 calculator 工具（数学计算器）
            "17.创建一个mcp服务.py",
        ],
        # env: 环境变量，None 表示继承当前进程的环境变量
        env=None,
    )

    # 使用 stdio_client 建立与 MCP 服务器的连接
    # stdio_client 是一个异步上下文管理器，它会：
    # 1. 启动 MCP 服务器子进程
    # 2. 建立标准输入(stdin)和标准输出(stdout)的通信通道
    # 3. 在退出时自动清理子进程
    async with stdio_client(server_params) as transport:
        # transport 是一个元组 (stdio, write)
        # - stdio: 用于读取服务器响应的流
        # - write: 用于向服务器发送请求的流
        stdio, write = transport

        # 创建 ClientSession 来管理 MCP 会话
        # ClientSession 提供了与 MCP 服务器交互的高级 API，包括：
        # - initialize(): 初始化会话，完成协议握手
        # - list_tools(): 获取服务器提供的工具列表
        # - call_tool(): 调用指定的工具
        async with ClientSession(stdio, write) as session:
            # 初始化 MCP 会话
            # 这一步是必须的，它完成客户端和服务器之间的协议协商和握手
            # 如果初始化失败，后续的工具调用将无法进行
            await session.initialize()

            # 获取 MCP 服务器提供的所有工具列表
            # list_tools() 返回一个包含 tools 属性的对象
            # 每个工具都有 name, description, inputSchema 等属性
            list_tools = await session.list_tools()
            tools = list_tools.tools
            # 打印所有可用工具的名称
            print("工具列表:", [tool.name for tool in tools])

            # 调用名为 "calculator" 的工具
            # 第一个参数是工具名称，第二个参数是传递给工具的参数（字典形式）
            # 这里计算一个数学表达式：564*34+12.4/455**2
            call_tool_response = await session.call_tool("calculator", {"expression": "564*34+12.4/455**2"})
            # 打印工具调用的返回结果
            print("工具结果:", call_tool_response)


if __name__ == "__main__":
    # 使用 asyncio.run() 运行异步主函数
    # 这是 Python 3.7+ 推荐的方式来运行异步程序
    asyncio.run(main())
