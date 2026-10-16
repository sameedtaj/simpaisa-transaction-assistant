
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server.fastmcp import FastMCP
from mcp_server.db import run_select_query

mcp = FastMCP("read-only-db-server")


@mcp.tool()
def execute_readonly_sql(query: str) -> dict:
    """
    Execute a safe read-only SELECT SQL query on PostgreSQL.
    """
    try:
        data = run_select_query(query)

        return {
            "success": True,
            "row_count": len(data),
            "data": data
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "row_count": 0,
            "data": []
        }


@mcp.tool()
def test_database_connection() -> dict:
    """
    Test database connection.
    """
    try:
        data = run_select_query("SELECT 1 AS connected;")

        return {
            "success": True,
            "data": data
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": []
        }


if __name__ == "__main__":
    mcp.run(transport="stdio")
