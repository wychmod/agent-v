import asyncio
from contextlib import AsyncExitStack
from mcp import StdioServerParameters, stdio_client, ClientSession


async def main() -> None:
    server_params = StdioServerParameters(
        command="uv",
        args=[
            "--directory",
            "/Users/ahs/IdeaProjects/agent-v/agent-study",
            "run",
            "17.创建一个mcp服务.py",
        ],
        env=None,
    )

    exit_stack = AsyncExitStack()
    try:
        transport = await exit_stack.enter_async_context(stdio_client(server_params))
        stdio, write = transport
        session = await exit_stack.enter_async_context(ClientSession(stdio, write))
        await session.initialize()

        list_tools = await session.list_tools()
        tools = list_tools.tools
        print("工具列表:", [tool.name for tool in tools])

        call_tool_response = await session.call_tool("calculator", {"expression": "564*34+12.4/455**2"})
        print("工具结果:", call_tool_response)
    finally:
        await exit_stack.aclose()

if __name__ == "__main__":
    asyncio.run(main())
