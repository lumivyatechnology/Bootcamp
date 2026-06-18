from abc import ABC, abstractmethod

import pandas as pd
from langchain_core.tools import StructuredTool


class Tools(ABC):
    """Abstract base class for database tools (Port in Port-Adapter pattern).

    This interface defines the contract that all database tool implementations
    must follow. Implementations include DuckDBTool and PostgresTool.
    """

    @property
    @abstractmethod
    def tools(self) -> list[StructuredTool]:
        """Return all available LangChain tools.

        Returns:
            list[StructuredTool]: List of all tools (execute_query, get_all_table, get_table_schema)
        """
        ...

    @property
    @abstractmethod
    def tool_get_all_table(self) -> StructuredTool:
        """Tool to retrieve all table names from the database.

        Returns:
            StructuredTool: LangChain tool for getting all table names
        """
        ...

    @property
    @abstractmethod
    def tool_get_table_schema(self) -> StructuredTool:
        """Tool to retrieve table schema/DDL.

        Returns:
            StructuredTool: LangChain tool for getting table schema
        """
        ...

    @property
    @abstractmethod
    def tool_execute_query(self) -> StructuredTool:
        """Tool to execute SQL queries.

        Returns:
            StructuredTool: LangChain tool for executing SQL queries
        """
        ...

    @abstractmethod
    def execute(self, query: str) -> list:
        """Execute a query and return raw results.

        Args:
            query: SQL query string to execute

        Returns:
            list: Raw query results as a list of tuples
        """
        ...

    @abstractmethod
    def execute_query(self, query: str) -> str:
        """Execute a query and return JSON string result.

        Args:
            query: SQL query string to execute

        Returns:
            str: JSON string representation of query results (limited to 100 rows)
        """
        ...

    @abstractmethod
    def execute_df(self, query: str) -> pd.DataFrame:
        """Execute a query and return pandas DataFrame.

        Args:
            query: SQL query string to execute

        Returns:
            pd.DataFrame: Query results as a pandas DataFrame
        """
        ...

    @abstractmethod
    def get_all_table(self) -> str:
        """Return comma-separated list of all table names.

        Returns:
            str: Comma-separated string of table names
        """
        ...

    @abstractmethod
    def get_table_schema(self, table_name: str) -> str:
        """Return CREATE TABLE statement for specified table.

        Args:
            table_name: Name of the table to get schema for

        Returns:
            str: DDL/CREATE TABLE statement for the table
        """
        ...
