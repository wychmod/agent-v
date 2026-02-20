from mcp.server import FastMCP

mcp = FastMCP(name="Bash工具")


@mcp.tool()
async def bash(command: str) -> dict[str, str | int]:
    """
    运行bash命令
    Args:
        command: bash命令

    Returns:
        bash命令的输出
    """
    import subprocess
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
