"""
Bash 工具调用示例
展示如何使用 bash 工具执行各种实用命令
"""
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio


async def bash_demo():
    """演示 bash 工具的各种用法"""
    
    # 启动 bash MCP 服务
    server_params = StdioServerParameters(
        command="python",
        args=["20.bash执行.py"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("=" * 50)
            print("Bash 工具调用示例")
            print("=" * 50)
            
            # 示例 1: 获取当前目录
            print("\n【示例 1】获取当前工作目录")
            result = await session.call_tool("bash", {"command": "pwd"})
            print("命令: pwd")
            print(f"输出: {result.content[0].text}")
            
            # 示例 2: 列出文件
            print("\n【示例 2】列出当前目录文件")
            result = await session.call_tool("bash", {"command": "ls -la"})
            print("命令: ls -la")
            print(f"输出:\n{result.content[0].text}")
            
            # 示例 3: 获取系统信息
            print("\n【示例 3】获取系统信息")
            result = await session.call_tool("bash", {"command": "uname -a"})
            print("命令: uname -a")
            print(f"输出: {result.content[0].text}")
            
            # 示例 4: 查看 Python 版本
            print("\n【示例 4】查看 Python 版本")
            result = await session.call_tool("bash", {"command": "python --version"})
            print("命令: python --version")
            print(f"输出: {result.content[0].text}")
            
            # 示例 5: 计算字符串长度（使用管道）
            print("\n【示例 5】使用管道进行文本处理")
            result = await session.call_tool("bash", {"command": "echo 'Hello World' | wc -c"})
            print("命令: echo 'Hello World' | wc -c")
            print(f"输出: {result.content[0].text}")
            
            # 示例 6: 查找文件
            print("\n【示例 6】查找项目中的 Python 文件")
            result = await session.call_tool("bash", {"command": "find . -name '*.py' -maxdepth 1 | head -5"})
            print("命令: find . -name '*.py' -maxdepth 1 | head -5")
            print(f"输出:\n{result.content[0].text}")
            
            # 示例 7: 统计代码行数
            print("\n【示例 7】统计项目代码行数")
            result = await session.call_tool("bash", {"command": "wc -l *.py"})
            print("命令: wc -l *.py")
            print(f"输出:\n{result.content[0].text}")
            
            # 示例 8: 获取当前时间
            print("\n【示例 8】获取当前时间")
            result = await session.call_tool("bash", {"command": "date '+%Y-%m-%d %H:%M:%S'"})
            print("命令: date '+%Y-%m-%d %H:%M:%S'")
            print(f"输出: {result.content[0].text}")
            
            print("\n" + "=" * 50)
            print("所有示例执行完成！")
            print("=" * 50)


if __name__ == "__main__":
    asyncio.run(bash_demo())
