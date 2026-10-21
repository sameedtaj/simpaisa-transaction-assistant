import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = PROJECT_ROOT / "mcp_server" / "server.py"
LOG_PATH = PROJECT_ROOT / "mcp_client_error.log"


async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
        cwd=str(PROJECT_ROOT),
        env=dict(os.environ),
    )

    with open(LOG_PATH, "w", encoding="utf-8") as errlog:
        async with stdio_client(server_params, errlog=errlog) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                result = await session.call_tool(tool_name, arguments)

                output = []
                for item in result.content:
                    if hasattr(item, "text"):
                        output.append(item.text)
                    else:
                        output.append(str(item))

                return "\\n".join(output)


async def execute_readonly_sql(query: str) -> str:
    return await call_mcp_tool(
        "execute_readonly_sql",
        {"query": query}
    )


async def test_database_connection() -> str:
    return await call_mcp_tool(
        "test_database_connection",
        {}
    )