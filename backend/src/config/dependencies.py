"""Application dependencies initialization for tools and LLM."""

from functools import lru_cache

from analytics_agents.tools.postgres_tool import PostgresTool
from analytics_agents.tools.duckdb_tool import DuckDBTool
from analytics_agents.tools.tool import Tools
from analytics_agents.tools.user_input import UserInputTool
from config import settings


def get_postgres_tool() -> Tools:
    pg = PostgresTool(
        connection_params={
            "host": settings.DB_HOST,
            "port": settings.DB_PORT,
            "dbname": settings.DB_NAME,
            "user": settings.DB_USER,
            "password": settings.DB_PASSWORD,
        }
    )
    return pg


def get_duckdb_tool() -> Tools:
    tools = DuckDBTool.from_base_dir(settings.DATA_BASE_PATH)
    return tools


@lru_cache
def get_db_tool() -> Tools:
    """Initialize and return the database tool.

    Returns:
        Tools: The initialized database tool (DuckDB or PostgreSQL).
    """
    source_map = {
        "postgres": get_postgres_tool,
        "duckdb": get_duckdb_tool,
    }
    source_fn = source_map.get(settings.SOURCE)
    if source_fn is None:
        raise ValueError(
            f"Source `{settings.SOURCE}` not found. Available sources: {source_map.keys()}"
        )
    return source_fn()


@lru_cache
def get_user_input_tool() -> UserInputTool:
    """Get the user input tool.

    Returns:
        UserInputTool: The user input tool instance.
    """
    return UserInputTool()


# Pre-initialized instances for convenience
db_tool = get_db_tool()
user_input_tool = get_user_input_tool()
