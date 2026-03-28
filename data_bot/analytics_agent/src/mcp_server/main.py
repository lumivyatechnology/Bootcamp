"""MCP Server for DuckDB - Exposes SQL query capabilities via Model Context Protocol."""

from mcp.server.fastmcp import FastMCP
from config.dependencies import get_db_tool

# Create FastMCP server
mcp = FastMCP("Postgres MCP Server")


@mcp.tool()
async def execute_query(query: str) -> str:
    """Execute a SQL query against the database and return results as JSON.

    Args:
        query: The SQL query to execute against the loaded tables.

    Returns:
        JSON string containing the query results (limited to first 100 rows).
    """
    tool = get_db_tool()
    return tool.execute_query(query)


@mcp.tool()
async def get_all_tables() -> str:
    """Get a comma-separated list of all available tables in the database.

    Returns:
        A string listing all table names separated by commas.
    """
    tool = get_db_tool()
    return tool.get_all_table()


@mcp.tool()
async def get_table_schema(table_name: str) -> str:
    """Get the CREATE TABLE statement (DDL) for a specific table.

    Args:
        table_name: The name of the table to get the schema for.

    Returns:
        The CREATE TABLE SQL statement showing the table's structure.
    """
    tool = get_db_tool()
    return tool.get_table_schema(table_name)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
