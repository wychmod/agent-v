from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
    base_url = "https://qianfan.baidubce.com/v2/ai_search/mcp"
    header = {"Authorization": "Bearer "}

    exit_stack = AsyncExitStack()

    try:
        transport = await exit_stack.enter_async_context(streamablehttp_client(
            url=base_url,
            headers=header
        ))

        read_stream, write_stream, _ = transport

        session: ClientSession = await exit_stack.enter_async_context(ClientSession(read_stream, write_stream))

        await session.initialize()

        list_tools = await session.list_tools()
        print("工具列表:", [tool.name for tool in list_tools.tools])
        result = await session.call_tool("chatCompletions", {
            "query": "元神官网"
        })
        print("结果:", result.content[0].text)
    finally:
        await exit_stack.aclose()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
