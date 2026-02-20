"""
code-executor MCP 工具调用示例
展示如何使用 code-executor 服务运行 Python 和 Node.js 代码
"""

import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


def print_result(title: str, result: str):
    """格式化输出结果"""
    print(f"\n{'=' * 60}")
    print(f"📌 {title}")
    print(f"{'=' * 60}")
    print(result)
    print(f"{'=' * 60}\n")


async def main():
    # 连接到 code-executor MCP 服务
    async with streamable_http_client(
            "http://localhost:9888/mcp"
    ) as (read, write, session_id):
        async with ClientSession(read, write) as session:
            # 初始化会话
            await session.initialize()

            # ============================================
            # 示例 1: 运行简单的 Python 代码
            # ============================================
            python_code_1 = """
# 计算斐波那契数列
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

result = [fibonacci(i) for i in range(10)]
print(f"斐波那契数列(前10项): {result}")
"""
            result1 = await session.call_tool("run_code", {
                "language": "python",
                "code": python_code_1,
                "timeout": 30
            })
            print_result("示例 1: Python - 斐波那契数列", result1.content[0].text)

            # ============================================
            # 示例 2: 运行 Python 数据处理代码
            # ============================================
            python_code_2 = """
import json

# 模拟数据
users = [
    {"name": "张三", "age": 25, "city": "北京"},
    {"name": "李四", "age": 30, "city": "上海"},
    {"name": "王五", "age": 28, "city": "北京"},
    {"name": "赵六", "age": 35, "city": "广州"}
]

# 按城市分组统计
city_stats = {}
for user in users:
    city = user["city"]
    if city not in city_stats:
        city_stats[city] = {"count": 0, "total_age": 0}
    city_stats[city]["count"] += 1
    city_stats[city]["total_age"] += user["age"]

# 计算平均年龄
for city in city_stats:
    city_stats[city]["avg_age"] = city_stats[city]["total_age"] / city_stats[city]["count"]
    del city_stats[city]["total_age"]

print("城市统计结果:")
print(json.dumps(city_stats, ensure_ascii=False, indent=2))
"""
            result2 = await session.call_tool("run_code", {
                "language": "python",
                "code": python_code_2,
                "timeout": 30
            })
            print_result("示例 2: Python - 数据处理与统计", result2.content[0].text)

            # ============================================
            # 示例 3: 运行 Python 数学计算
            # ============================================
            python_code_3 = """
import math

# 计算圆的面积和周长
radius = 5
area = math.pi * radius ** 2
circumference = 2 * math.pi * radius

print(f"圆的半径: {radius}")
print(f"圆的面积: {area:.2f}")
print(f"圆的周长: {circumference:.2f}")

# 计算阶乘
n = 10
factorial = math.factorial(n)
print(f"\\n{n}! = {factorial}")

# 计算平方根
numbers = [16, 25, 36, 49, 64]
print(f"\\n平方根计算:")
for num in numbers:
    print(f"  √{num} = {math.sqrt(num)}")
"""
            result3 = await session.call_tool("run_code", {
                "language": "python",
                "code": python_code_3,
                "timeout": 30
            })
            print_result("示例 3: Python - 数学计算", result3.content[0].text)

            # ============================================
            # 示例 4: 运行 Node.js 代码
            # ============================================
            node_code_1 = """
// 字符串处理示例
const text = "Hello, MCP Code Executor!";

console.log("原始文本:", text);
console.log("大写:", text.toUpperCase());
console.log("小写:", text.toLowerCase());
console.log("长度:", text.length);
console.log("分割:", text.split(", "));

// 数组操作
const numbers = [1, 2, 3, 4, 5];
const doubled = numbers.map(n => n * 2);
const sum = numbers.reduce((a, b) => a + b, 0);

console.log("\\n数组操作:");
console.log("原始数组:", numbers);
console.log("翻倍后:", doubled);
console.log("总和:", sum);
"""
            result4 = await session.call_tool("run_code", {
                "language": "node",
                "code": node_code_1,
                "timeout": 30
            })
            print_result("示例 4: Node.js - 字符串和数组操作", result4.content[0].text)

            # ============================================
            # 示例 5: 运行 Node.js 异步代码
            # ============================================
            node_code_2 = """
// 异步操作示例
async function fetchData() {
    // 模拟异步延迟
    await new Promise(resolve => setTimeout(resolve, 100));
    
    const data = {
        timestamp: new Date().toISOString(),
        randomId: Math.random().toString(36).substring(7),
        status: "success"
    };
    
    return data;
}

async function main() {
    console.log("开始异步操作...");
    const result = await fetchData();
    console.log("结果:", JSON.stringify(result, null, 2));
    console.log("异步操作完成!");
}

main();
"""
            result5 = await session.call_tool("run_code", {
                "language": "node",
                "code": node_code_2,
                "timeout": 30
            })
            print_result("示例 5: Node.js - 异步操作", result5.content[0].text)

            # ============================================
            # 示例 6: 运行 Node.js 对象处理
            # ============================================
            node_code_3 = """
// 对象操作示例
const user = {
    name: "John Doe",
    email: "john@example.com",
    age: 30,
    skills: ["JavaScript", "Python", "Go"]
};

// 对象解构
const { name, email, skills } = user;
console.log("用户信息:");
console.log(`  姓名: ${name}`);
console.log(`  邮箱: ${email}`);
console.log(`  技能: ${skills.join(", ")}`);

// 对象合并
const additionalInfo = {
    city: "New York",
    country: "USA"
};

const fullUser = { ...user, ...additionalInfo };
console.log("\\n完整用户信息:", JSON.stringify(fullUser, null, 2));

// 对象键值操作
console.log("\\n对象键值:");
console.log("Keys:", Object.keys(fullUser));
console.log("Values:", Object.values(fullUser));
"""
            result6 = await session.call_tool("run_code", {
                "language": "node",
                "code": node_code_3,
                "timeout": 30
            })
            print_result("示例 6: Node.js - 对象处理", result6.content[0].text)

            print("✅ 所有示例执行完成!")


if __name__ == "__main__":
    asyncio.run(main())
