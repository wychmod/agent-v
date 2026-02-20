import asyncio

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

    async with stdio_client(server_params) as transport:
        stdio, write = transport
        async with ClientSession(stdio, write) as session:
            await session.initialize()

            list_tools = await session.list_tools()
            tools = list_tools.tools
            print("工具列表:", [tool.name for tool in tools])

            call_tool_response = await session.call_tool("calculator", {"expression": "564*34+12.4/455**2"})
            print("工具结果:", call_tool_response)


if __name__ == "__main__":
    asyncio.run(main())
