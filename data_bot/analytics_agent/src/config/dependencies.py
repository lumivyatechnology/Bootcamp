"""Application dependencies initialization for tools and LLM."""

import os
from functools import lru_cache

from analytics_agents.tools.postgres_tool import PostgresTool
from analytics_agents.tools.tool import Tools
from analytics_agents.tools.user_input import UserInputTool
from config import settings


TABLES = [
    {"name": "brands", "path": "brands.csv", "format": "csv"},
    {"name": "cpu_models", "path": "cpu_models.csv", "format": "csv"},
    {"name": "operating_systems", "path": "operating_systems.csv", "format": "csv"},
    {"name": "phones", "path": "phones.csv", "format": "csv"},
    {"name": "phone_specs", "path": "phone_specs.csv", "format": "csv"},
]


@lru_cache
def get_postgres_tool() -> Tools:
    pg = PostgresTool(
        connection_params={
            "host": settings.POSTGRES_HOST,
            "port": settings.POSTGRES_PORT,
            "dbname": settings.POSTGRES_DB,
            "user": settings.POSTGRES_USER,
            "password": settings.POSTGRES_PASSWORD,
        }
    )
    return pg


@lru_cache
def get_db_tool() -> Tools:
    """Initialize and return the database tool.

    Returns:
        Tools: The initialized database tool (DuckDB or PostgreSQL).
    """
    return get_postgres_tool()
    # base_dir = settings.DATA_BASE_PATH
    #
    # # Build table infos with full paths
    # table_infos = []
    # for table in TABLES:
    #     table_with_path = table.copy()
    #     table_with_path["path"] = os.path.join(base_dir, table["path"])
    #     table_infos.append(TableInfo(**table_with_path))
    #
    # tool = DuckDBTool(tables=table_infos)
    # tool.load_tables()
    #
    # print("[*] Tables Loaded:", [t.name for t in table_infos])
    #
    # return tool
    #


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
